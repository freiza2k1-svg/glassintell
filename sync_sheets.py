"""Utility helpers for synchronizing data between Google Sheets tabs."""

from __future__ import annotations

from typing import Iterable, Sequence

import re

# Example constants that consuming code can rely on. These can be overridden or
# imported from environment specific modules when the script is integrated.
MASTER_TAB = "master glass"
CHANNEL_TABS: Sequence[str] = ("Amazon", "Ebay", "Website")


def format_range(sheet: str, cells: str | None = None) -> str:
    """Return an A1 notation range for the provided sheet and cell selection.

    Sheet names that contain spaces or special characters must be wrapped in
    single quotes according to the Google Sheets API requirements. The helper
    takes care of quoting the sheet while allowing callers to pass an optional
    ``cells`` suffix (for example ``"1:1"`` or ``"A1:C10"``).

    The function is idempotent; it does not add an additional set of quotes when
    the caller already passes a quoted sheet name. Embedded quotes inside the
    sheet name are escaped by doubling them, which follows the Google Sheets
    syntax.
    """

    if sheet.startswith("'") and sheet.endswith("'"):
        quoted_sheet = sheet
    else:
        needs_quotes = bool(re.search(r"[^A-Za-z0-9_]", sheet))
        if needs_quotes:
            escaped = sheet.replace("'", "''")
            quoted_sheet = f"'{escaped}'"
        else:
            quoted_sheet = sheet

    if cells:
        return f"{quoted_sheet}!{cells}"
    return quoted_sheet


def get_values(service, spreadsheet_id: str, range_name: str) -> Sequence[Sequence[str]]:
    """Read rows from ``range_name`` within ``spreadsheet_id`` using the API."""

    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return result.get("values", [])


def get_master_rows(service, spreadsheet_id: str) -> Sequence[Sequence[str]]:
    """Fetch all rows from the master tab."""

    return get_values(service, spreadsheet_id, format_range(MASTER_TAB))


def get_channel_header(service, spreadsheet_id: str, tab: str) -> Sequence[str]:
    """Fetch the header row from an individual channel tab."""

    header = get_values(service, spreadsheet_id, format_range(tab, "1:1"))
    return header[0] if header else []


def clear_values(service, spreadsheet_id: str, sheet: str, cells: str | None = None) -> None:
    """Clear values from ``sheet`` (optionally limited to ``cells``)."""

    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=format_range(sheet, cells),
        body={},
    ).execute()


def update_values(
    service,
    spreadsheet_id: str,
    sheet: str,
    values: Iterable[Sequence[str]],
    cells: str | None = None,
    *,
    value_input_option: str = "RAW",
) -> None:
    """Write ``values`` to ``sheet`` within ``spreadsheet_id``."""

    body = {"values": [list(row) for row in values]}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=format_range(sheet, cells),
        valueInputOption=value_input_option,
        body=body,
    ).execute()


__all__ = [
    "CHANNEL_TABS",
    "MASTER_TAB",
    "clear_values",
    "format_range",
    "get_channel_header",
    "get_master_rows",
    "get_values",
    "update_values",
]
