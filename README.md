# glassintell

Automation utilities for synchronising channel-specific Google Sheets tabs with the master inventory data.

## Prerequisites

* Python 3.10+
* A Google Cloud service account with access to the target spreadsheet

## Setup

1. Install dependencies in your Python environment:

   ```bash
   pip install -r requirements.txt
   ```

2. Place your service account credentials JSON file at the repository root (e.g. `service_account.json`). Keep this file **out of version control**.

3. Create a `.env` file next to `sync_sheets.py` and configure it with at least the path to your credentials. You can optionally override the default spreadsheet ID:

   ```env
   GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
   # SPREADSHEET_ID=1oK_WS28RIqEkjSI7KHoNTB27f9IgL6jwvAFGNjOauJI
   # LOG_LEVEL=DEBUG
   ```

## Usage

Run the synchronisation script to mirror the `master glass` tab into the Ebay, TikTok, and Whatnot tabs while aligning columns by header name:

```bash
python sync_sheets.py
```

You can override configuration at runtime using CLI flags:

* `--spreadsheet <spreadsheet_id>` – specify a different spreadsheet.
* `--service-account <path>` – use a non-default service account file.
* `--dry-run` – preview changes without writing to the destination tabs.

Example:

```bash
python sync_sheets.py --spreadsheet 1oK_WS28RIqEkjSI7KHoNTB27f9IgL6jwvAFGNjOauJI --dry-run
```

The script uses basic logging for progress visibility and error reporting.

## Environment Variables

* `GOOGLE_SERVICE_ACCOUNT_FILE` – path to your service account JSON file (defaults to `service_account.json`).
* `SPREADSHEET_ID` – target spreadsheet ID (defaults to the project master sheet).
* `LOG_LEVEL` – logging verbosity (defaults to `INFO`).

## Notes

* Ensure the channel tabs contain a header row; the script aligns data based on header names.
* Missing values in the master sheet are mirrored as blank cells to prevent misalignment.
* The repository intentionally ignores `.env` and credentials files—store secrets securely.
