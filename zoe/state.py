"""SQLite state: the source of truth.  (Milestone 3)

Database: settings.paths.db (data/zoe_state.db). Create dirs + schema on first use.

Suggested schema:
    jobs(job_id TEXT PRIMARY KEY, source, title, company, location, canonical_url,
         dedupe_key, posted_at, first_seen_at, raw_json)
    scores(job_id TEXT PRIMARY KEY REFERENCES jobs, final_score INT, verdict,
           result_json, model, rubric_version INT, scored_at,
           alerted INT DEFAULT 0, synced_to_sheet INT DEFAULT 0)
    runs(id INTEGER PRIMARY KEY, started_at, finished_at, status, summary_json)
    gmail_messages(message_id TEXT PRIMARY KEY, processed_at)   -- Milestone 7

Contract (class State, constructed with a db path):
    is_seen(job: Job) -> bool         # by job_id, canonical_url, or dedupe_key within 7 days
    save_job(job: Job) -> None
    save_score(score: StoredScore) -> None
    unsynced_rows() -> list[tuple[Job, StoredScore]]
    mark_synced(job_ids: list[str]) -> None
    mark_alerted(job_ids: list[str]) -> None
    start_run() -> int
    finish_run(run_id: int, summary: RunSummary) -> None
    last_successful_run() -> datetime | None

dedupe_key = lowercase alphanumerics of title + "|" + company.
Use one connection per run, WAL mode, and parameterized queries only.
"""

from __future__ import annotations


class State:
    def __init__(self, db_path):
        raise NotImplementedError("Milestone 3")
