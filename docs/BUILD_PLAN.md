# Build plan

Build in this order. Each milestone is one Claude Code session (or less) and ends
with a commit. Don't start a milestone until the previous one's acceptance
criteria pass.

Suggested prompt for each: *"Plan Milestone N from docs/BUILD_PLAN.md. Show me the
plan before writing code."* — then *"Go."*

---

## Milestone 0 — Environment (Steve, by hand, ~10 min)

- [ ] `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- [ ] `cp .env.example .env` and add `ANTHROPIC_API_KEY`
- [ ] `cp profile.example.md profile.md` and fill it in (this matters more than any code)
- [ ] Paste 5–10 real job descriptions into `samples/` as `.txt` files — include
      some great fits, some obvious misses, and some "looks good but isn't"

## Milestone 1 — Config + models

- `zoe/config.py`: load `config.yaml` + `.env` into a pydantic `Settings` object.
  Clear error naming any missing required value.
- `zoe/models.py` is already drafted — review it, finalize it.
- **Accept:** `pytest tests/test_models.py tests/test_config.py` passes.

## Milestone 2 — Scorer (the core)

- `zoe/scorer.py`: `score_job(job, profile_text, settings) -> ScoreResult`.
  Uses `prompts/scorer_system.md` as the system prompt; forces a tool call whose
  input schema is `ScoreResult.model_json_schema()`; validates with pydantic;
  one retry on validation failure; then raises `ScoringError`.
- Recompute the final score in Python from the deductions the model returns
  (100 minus the sum, clamped 0–100) rather than trusting the model's arithmetic.
- `scripts/score_samples.py`: score every `samples/*.txt`, print a table
  (file, score, verdict, top deductions), and write `data/sample_scores.csv`.
- **Accept:** unit tests with a mocked Anthropic client pass; Steve runs
  `python scripts/score_samples.py` and the ranking of his samples matches his gut.
  Iterate on `prompts/scorer_system.md` (not code) until it does.

## Milestone 3 — State (SQLite)

- `zoe/state.py`: create schema on first run (`jobs`, `scores`, `runs` tables);
  `is_seen(job_id)`, `save_job`, `save_score`, `unsynced_rows()`,
  `mark_synced(ids)`, `start_run()`, `finish_run(summary)`, `last_successful_run()`.
- Dedupe key: `Job.job_id` = `"{source}:{source_native_id}"`; also dedupe by
  `canonical_url` and by normalized `(title, company)` within 7 days, since the
  same job arrives from multiple sources.
- **Accept:** tests against a temp-file DB cover dedupe and sync flags.

## Milestone 4 — JSearch ingestion

- `zoe/ingest/jsearch.py`: for each search in `config.yaml`, query JSearch with
  "posted today", map results to `Job`. Respect `max_results_per_search`.
  Retry with backoff on 429/5xx; skip the source for this run after 3 failures.
- **Accept:** tests with recorded JSON fixtures (in `tests/fixtures/`, no real
  key); `python -m zoe.ingest.jsearch --print` lists today's jobs when run by hand.

## Milestone 5 — Orchestrator, dry run

- `zoe/schedule.py` + `zoe/main.py`: CLI flags `--dry-run`, `--no-jitter`,
  `--force` (ignore schedule gate). Ingest → dedupe → score (cap) → save →
  print a summary. No Sheets, no alerts yet.
- **Accept:** `python -m zoe.main --dry-run --no-jitter --force` runs end to end
  on real data and a second run immediately after scores 0 new jobs.

## Milestone 6 — Google Sheets

- Steve: create the Google Cloud project, enable Sheets + Drive APIs, create a
  service account, download its key to `secrets/service_account.json`, create
  the Sheet, share it with the service account's `client_email` as Editor, put
  the Sheet ID in `.env`. (Claude: walk him through this step by step.)
- `zoe/sheets.py`: ensure header row exists; `append_rows` once per run from
  `state.unsynced_rows()`; mark synced on success.
- **Accept:** a real run adds rows; killing Wi-Fi mid-run leaves rows unsynced
  and the next run catches them up.

## Milestone 7 — Gmail alert ingestion

- Steve: set ZipRecruiter job alerts (instant/daily) for his searches; create an
  OAuth *Desktop app* client in the same Google Cloud project, enable the Gmail
  API, save the client JSON to `secrets/gmail_credentials.json`; run
  `python scripts/gmail_auth.py` once.
- `zoe/ingest/gmail_alerts.py`: read-only scope; query from `config.yaml`;
  parse each alert email's job cards (title, company, location, link, snippet);
  enrich via JSearch where possible; label processed messages or track message
  IDs in SQLite so they're not reparsed.
- **Accept:** tests on saved `.eml`/HTML fixtures; real run picks up alert jobs.

## Milestone 8 — Calibration week (no code)

- Run on schedule for ~5–7 days with `notify.enabled: false`.
- Steve marks the Sheet's `Status` column (Applied / Would apply / No).
- Pick `notify.threshold` from the data: the lowest score where "Would apply"
  dominates. Tune the rubric if great jobs are scoring low.

## Milestone 9 — Notifications

- `zoe/notifier.py`: Pushover (default), Telegram (optional), macOS
  `osascript` notification (fallback). One message per job ≥ threshold with
  title, company, score, one-line reason, apply link. Daily heartbeat optional.
- **Accept:** `python -m zoe.notifier --test` delivers to Steve's phone.

## Milestone 10 — launchd

- `scripts/install_launchd.sh` renders the plist template with the repo path and
  venv python, copies it to `~/Library/LaunchAgents/`, and runs
  `launchctl bootstrap gui/$(id -u) …`. Uninstall script does `bootout`.
- **Accept:** `launchctl print gui/$(id -u)/com.elwood.zoelancaster` shows it
  loaded; `logs/zoe.log` gets a new run within an hour.

## Later / maybe

- Weekly digest email of the Sheet's top 10.
- Second scoring pass with a larger model only for jobs scoring ≥ 60.
- Auto-draft a tailored cover-letter opener for alerted jobs.
