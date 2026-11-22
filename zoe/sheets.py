"""Mirror scored jobs to Google Sheets.  (Milestone 6)

Contract:
    sync_to_sheet(state: State, settings) -> int   # rows written

- Auth: gspread.service_account(filename=GOOGLE_SERVICE_ACCOUNT_FILE).
- Open by GOOGLE_SHEET_ID; get or create worksheet settings.sheets.worksheet.
- Ensure row 1 equals settings.sheets.columns (write it if the sheet is empty;
  warn, don't overwrite, if it differs).
- Build rows from state.unsynced_rows() in column order. Timestamp and
  Posted Age in America/Chicago. Leave "Status" blank for Steve.
- ONE worksheet.append_rows(rows, value_input_option="USER_ENTERED") call.
- On success state.mark_synced(ids). On any exception, log and return 0 —
  rows stay unsynced and go next run.
"""

from __future__ import annotations


def sync_to_sheet(state, settings) -> int:
    raise NotImplementedError("Milestone 6")
