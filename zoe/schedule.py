"""Decide whether this launchd tick should run, and add jitter.  (Milestone 5)

Contract:
    should_run(now_local: datetime, last_success: datetime | None, settings) -> tuple[bool, str]
    jitter_sleep(settings, enabled: bool = True) -> None

Rules (times in settings.timezone):
- Inside quiet_hours (handles ranges that cross midnight): don't run.
- Inside peak_hours: run.
- Otherwise: run only if last_success is None or older than
  off_peak_min_interval_minutes.
- Return a short human-readable reason for the log line.
- jitter_sleep sleeps random 0..jitter_seconds_max seconds unless disabled.
Pure functions apart from the sleep, so they're easy to test with fixed datetimes.
"""

from __future__ import annotations


def should_run(now_local, last_success, settings):
    raise NotImplementedError("Milestone 5")


def jitter_sleep(settings, enabled: bool = True) -> None:
    raise NotImplementedError("Milestone 5")
