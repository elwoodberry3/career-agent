"""One-time Gmail OAuth consent.  (Milestone 7)

Usage: python scripts/gmail_auth.py

- Reads the OAuth Desktop client JSON at GMAIL_CREDENTIALS_FILE.
- Runs google_auth_oauthlib.flow.InstalledAppFlow.run_local_server with scope
  gmail.readonly only.
- Saves the token to GMAIL_TOKEN_FILE (secrets/, gitignored) with 0600 permissions.
- Prints the Gmail address it authorized and how many messages match the
  configured alert query, as a sanity check.
"""

raise SystemExit("Milestone 7: implement scripts/gmail_auth.py")
