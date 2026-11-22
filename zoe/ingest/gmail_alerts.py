"""ZipRecruiter job-alert emails via the Gmail API.  (Milestone 7)

This reads Steve's own inbox. It never visits ZipRecruiter pages.

Contract:
    class GmailAlertsSource(JobSource): __init__(settings, state, jsearch: JSearchSource | None)

- Auth: user OAuth, scope https://www.googleapis.com/auth/gmail.readonly only.
  Token at GMAIL_TOKEN_FILE (created by scripts/gmail_auth.py); refresh automatically;
  if missing/invalid, raise SourceError telling Steve to run scripts/gmail_auth.py.
- List messages matching settings.sources.gmail_alerts.query; skip message IDs
  already in state (gmail_messages table).
- Parse the HTML body with BeautifulSoup into job cards: title, company,
  location, snippet, link. Alert layouts change — keep the parser isolated in
  parse_alert_html(html) -> list[dict] and test it on fixtures in tests/fixtures/.
- job_id = "gmail_alerts:" + a stable hash of the link's job identifier (or title|company).
- If enrich_with_jsearch and jsearch is given: jsearch.lookup(title, company);
  on a confident match use its full description (description_source="full"),
  else description=snippet, description_source="snippet".
"""

from __future__ import annotations


class GmailAlertsSource:
    name = "gmail_alerts"

    def __init__(self, settings, state, jsearch=None):
        raise NotImplementedError("Milestone 7")
