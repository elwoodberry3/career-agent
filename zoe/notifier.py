"""Alert on strong matches.  (Milestone 9)

Contract:
    notify(jobs_and_scores: list[tuple[Job, StoredScore]], settings) -> int  # sent count

- Only when settings.notify.enabled and final_score >= settings.notify.threshold,
  at most settings.notify.max_alerts_per_run, highest score first.
- Message: "{score} · {title} — {company}\n{summary}\n{apply_url}"
- Channels:
    pushover  POST https://api.pushover.net/1/messages.json (token, user, message,
              title, url, priority=1)
    telegram  POST https://api.telegram.org/bot{token}/sendMessage (chat_id, text)
    macos     osascript -e 'display notification ...' (fallback, local only)
- Caller marks alerted in State only for messages that actually sent.
- `python -m zoe.notifier --test` sends a test message on the configured channel.
"""

from __future__ import annotations


def notify(jobs_and_scores, settings) -> int:
    raise NotImplementedError("Milestone 9")


if __name__ == "__main__":
    raise SystemExit("Milestone 9: implement --test")
