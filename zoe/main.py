"""Orchestrator: one pass, then exit.  (Milestone 5, extended in 6, 7, 9)

Usage:
    python -m zoe.main [--dry-run] [--no-jitter] [--force]

    --dry-run    ingest + score + save to SQLite, but no Sheets writes and no alerts
    --no-jitter  skip the random start delay (manual runs)
    --force      ignore the schedule gate

Flow:
    1. configure logging (logs/zoe.log + stdout), load settings, open State
    2. schedule.should_run(...) unless --force; if not, record skipped run and exit 0
    3. schedule.jitter_sleep(...) unless --no-jitter
    4. for each enabled source: fetch jobs (source failure = logged, run continues)
    5. drop jobs where state.is_seen(job); save new jobs
    6. score up to scoring.max_jobs_per_run new jobs (newest first);
       per-job ScoringError = logged and skipped
    7. unless --dry-run: sheets.sync_to_sheet(...) if enabled; notifier.notify(...) if enabled
    8. finish_run with RunSummary; print one summary line; exit 0
       (exit 1 only on config/credential errors so launchd logs show it)
"""

from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError("Milestone 5")


if __name__ == "__main__":
    raise SystemExit(main())
