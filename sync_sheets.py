#!/usr/bin/env python3
"""Synchronize the "master glass" tab with channel-specific tabs."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Iterable, List, Sequence

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DEFAULT_SPREADSHEET_ID = "1oK_WS28RIqEkjSI7KHoNTB27f9IgL6jwvAFGNjOauJI"
MASTER_TAB = "master glass"
TARGET_TABS = ("Ebay", "TikTok", "Whatnot")


class SyncError(RuntimeError):
    """Raised when synchronization cannot be completed."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Mirror rows from the 'master glass' tab into the Ebay, TikTok, and "
            "Whatnot tabs, aligning columns by header name."
        )
    )
    parser.add_argument(
        "--spreadsheet",
        dest="spreadsheet_id",
        default=os.getenv("SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID),
        help="Spreadsheet ID to synchronise (defaults to env SPREADSHEET_ID or project default).",
    )
    parser.add_argument(
        "--service-account",
        dest="service_account_file",
        default=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"),
        help="Path to the Google service account JSON credentials file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and align data without writing back to the spreadsheet.",
    )
    return parser.parse_args(argv)


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )


def load_credentials(service_account_file: str) -> Credentials:
    if not os.path.exists(service_account_file):
        raise FileNotFoundError(
            f"Service account credentials not found at: {service_account_file}."
        )
    return Credentials.from_service_account_file(service_account_file, scopes=SCOPES)


from googleapiclient.discovery import Resource

def create_service(credentials: Credentials) -> Resource:
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def get_values(service, spreadsheet_id: str, range_: str) -> List[List[str]]:
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_)
        .execute()
    )
    return response.get("values", [])


def clear_values(service, spreadsheet_id: str, sheet_name: str) -> None:
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}",
        body={},
    ).execute()


def update_values(
    service,
    spreadsheet_id: str,
    sheet_name: str,
    values: Iterable[Iterable[str]],
) -> None:
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}",
        valueInputOption="RAW",
        body={"values": [list(row) for row in values]},
    ).execute()


def align_rows(
    master_headers: Sequence[str],
    target_headers: Sequence[str],
    master_rows: Iterable[Sequence[str]],
) -> List[List[str]]:
    header_map = {header.strip().lower(): idx for idx, header in enumerate(master_headers)}
    aligned_rows: List[List[str]] = []
    for row in master_rows:
        aligned_row: List[str] = []
        for header in target_headers:
            key = header.strip().lower()
            idx = header_map.get(key)
            value = ""
            if idx is not None and idx < len(row):
                value = row[idx]
            aligned_row.append(value)
        aligned_rows.append(aligned_row)
    return aligned_rows


def sync_spreadsheet(
    service,
    spreadsheet_id: str,
    dry_run: bool = False,
) -> None:
    logging.info("Reading master tab '%s'", MASTER_TAB)
    master_range = f"'{MASTER_TAB}'"
    master_data = get_values(service, spreadsheet_id, master_range)
    if not master_data:
        raise SyncError("Master tab is empty; nothing to synchronise.")

    master_headers = master_data[0]
    master_rows = master_data[1:] if len(master_data) > 1 else []

    for tab in TARGET_TABS:
        logging.info("Processing target tab '%s'", tab)
        target_data = get_values(service, spreadsheet_id, f"{tab}!1:1")
        if not target_data:
            logging.warning(
                "Skipping tab '%s' because it has no header row to align against.", tab
            )
            continue

        target_headers = target_data[0]
        if not target_headers:
            logging.warning(
                "Skipping tab '%s' because its header row is empty.", tab
            )
            continue

        aligned_rows = align_rows(master_headers, target_headers, master_rows)
        values = [target_headers] + aligned_rows
        logging.info("Prepared %d rows for tab '%s'", len(aligned_rows), tab)

        if dry_run:
            logging.info("Dry run enabled; not writing to tab '%s'", tab)
            continue

        logging.debug("Clearing existing data in tab '%s'", tab)
        clear_values(service, spreadsheet_id, tab)
        logging.info("Writing %d rows to tab '%s'", len(values), tab)
        update_values(service, spreadsheet_id, tab, values)


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    configure_logging()
    args = parse_args(argv)

    try:
        credentials = load_credentials(args.service_account_file)
        service = create_service(credentials)
        sync_spreadsheet(service, args.spreadsheet_id, dry_run=args.dry_run)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1
    except HttpError as exc:
        logging.error("Google Sheets API error: %s", exc)
        return 1
    except SyncError as exc:
        logging.error("%s", exc)
        return 1
    except Exception:  # pragma: no cover - unexpected errors
        logging.exception("Unexpected error during synchronisation")
        return 1

    logging.info("Synchronization complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
