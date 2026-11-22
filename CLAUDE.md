# CLAUDE.md — career-agent ("Zoe Lancaster")

Read this file at the start of every session. It is the source of truth for what
this project is, how it is built, and the rules you must follow while working on it.

## What this project is

**Zoe Lancaster** is a personal job-scout agent for Steve Berry (Elwood S. Berry III).
It runs unattended on his MacBook Pro (M3 Pro, 18 GB, macOS) every ~45–65 minutes
during the day, finds newly posted jobs, scores each one against his profile with
an LLM, logs every evaluated job to a Google Sheet, and pushes an alert for strong
matches so he can apply within **1–2 hours of posting**.

Phase I goal: collect telemetry (what's posted, how it scores) and calibrate the
scoring rubric. Notifications are **off** until the threshold is calibrated
(see `docs/BUILD_PLAN.md`, Milestone 8).

## Architecture

A short-lived Python process, run by macOS `launchd`, that does one pass and exits.
No long-running loops. No browser.

```
launchd (every 45 min) ──► caffeinate -s ──► python -m zoe.main
                                                  │
  1. schedule gate   (peak vs off-peak, jitter)   │  zoe/main.py
  2. ingest          (pluggable sources)          │  zoe/ingest/*
  3. dedupe          (SQLite: seen job IDs)       │  zoe/state.py
  4. score           (Claude, deductive rubric)   │  zoe/scorer.py + prompts/
  5. persist         (SQLite = source of truth)   │  zoe/state.py
  6. log             (batch append to Sheets)     │  zoe/sheets.py
  7. alert           (score ≥ threshold)          │  zoe/notifier.py
```

### Data sources (ingestion)

Sources implement the `JobSource` protocol in `zoe/ingest/base.py` and return
`list[Job]`. Enabled sources are listed in `config.yaml`.

| Source | Module | Gives full description? | Auth |
|---|---|---|---|
| JSearch API (RapidAPI) — aggregates ZipRecruiter, Indeed, LinkedIn, etc. | `zoe/ingest/jsearch.py` | Yes | `RAPIDAPI_KEY` |
| ZipRecruiter job-alert emails via Gmail API | `zoe/ingest/gmail_alerts.py` | No (title, company, location, link, snippet) | OAuth desktop client in `secrets/` |

For Gmail-alert jobs with no full description: try to enrich via a JSearch
lookup (title + company). If that fails, score on the snippet and set
`description_source = "snippet"` so the Sheet shows the score is low-confidence.

Verify the JSearch endpoint, parameters and response fields against its current
RapidAPI docs before coding against them — do not trust field names in this file blindly.

### Hard rule: no scraping job sites

Do **not** write code that drives a browser (Playwright, Selenium, Camoufox,
nodriver, etc.) against ZipRecruiter or any job board, fetches job-board HTML pages,
rotates fingerprints/user agents, solves CAPTCHAs, or otherwise evades bot
protection. ZipRecruiter's terms prohibit automated access and the user's personal
account is at risk. If a feature seems to need this, stop and propose an
API- or email-based alternative instead.

## Tech stack

- Python 3.12+, virtualenv at `.venv/`
- `anthropic` SDK — scoring model set in `config.yaml` (default `claude-haiku-5-5`)
- `pydantic` v2 — all data contracts live in `zoe/models.py`
- `sqlite3` (stdlib) — `data/zoe_state.db`
- `gspread` + Google **Service Account** — Sheets logging
- `google-api-python-client` + `google-auth-oauthlib` — Gmail (user OAuth; a service
  account cannot read a personal Gmail inbox)
- `httpx` — HTTP for JSearch and notifications
- `pyyaml`, `python-dotenv`
- `pytest`, `ruff`

Do not add dependencies without a reason; add them to `requirements.txt` when you do.

## Repository layout

```
CLAUDE.md                 this file
README.md                 human setup guide
config.yaml               searches, schedule, thresholds, sources (no secrets)
.env.example              template for .env (secrets) — .env is gitignored
profile.example.md        template; the real profile.md is gitignored
prompts/scorer_system.md  the deductive scoring rubric (system prompt)
docs/BUILD_PLAN.md        milestones + acceptance criteria — build in this order
docs/SCORING_RUBRIC.md    rationale behind the rubric and calibration process
zoe/
  config.py               load config.yaml + .env into a typed Settings object
  models.py               Job, ScoreResult, RunSummary (pydantic) — the contracts
  state.py                SQLite: schema, seen-check, save jobs/scores, run log
  scorer.py               Claude call with forced tool use → ScoreResult
  sheets.py               batch append rows to Google Sheets
  notifier.py             Pushover / Telegram / macOS notification
  schedule.py             peak/off-peak gate + jitter
  main.py                 orchestrator / CLI entry point
  ingest/
    base.py               JobSource protocol
    jsearch.py            JSearch API source
    gmail_alerts.py       Gmail ZipRecruiter-alert source
scripts/
  score_samples.py        score samples/*.txt offline (rubric tuning)
  gmail_auth.py           one-time Gmail OAuth consent → secrets/gmail_token.json
  install_launchd.sh      render + bootstrap the launchd agent
  uninstall_launchd.sh
launchd/com.elwood.zoelancaster.plist.template
samples/                  hand-pasted job descriptions for testing the scorer
tests/                    pytest suite
data/ logs/ secrets/      runtime only — all gitignored
```

## Rules for working in this repo

1. **This repo is public.** Never commit secrets, `profile.md`, anything in `data/`,
   `logs/`, `secrets/`, or `.env`. Before every commit, run `git status` and check
   that none of those appear. Never print secret values in output or logs.
2. **Build one milestone at a time** from `docs/BUILD_PLAN.md`. Plan first, then
   implement, then meet that milestone's acceptance criteria, then commit. Don't
   start the next milestone in the same change.
3. **Contracts first.** `zoe/models.py` defines the data passed between modules.
   Change a model only deliberately, and update every caller and test.
4. **SQLite is the source of truth.** Sheets is a mirror. Write to SQLite first;
   if the Sheets write fails, mark rows `synced_to_sheet = 0` and retry next run.
5. **Batch external writes.** One `append_rows` call per run, not one per job.
6. **Every module must be runnable/testable on its own** with mocks or `--dry-run`.
   Tests must never call real APIs (mock `anthropic`, `httpx`, `gspread`, Gmail).
7. **Fail soft per job, fail loud per run.** One bad job (parse error, LLM error)
   is logged and skipped; the run continues. Missing config or credentials
   raises immediately with a clear message naming what's missing.
8. **Cost guard.** Never score more than `scoring.max_jobs_per_run` jobs per run.
   Never re-score a job ID already in SQLite.
9. **Logging:** use the stdlib `logging` module (configured in `main.py`), one line
   per significant event. launchd captures stdout/stderr to `logs/`.
10. **Times:** store UTC ISO-8601 in SQLite; use `America/Chicago` for schedule
    logic and for display in the Sheet.
11. Code style: type hints everywhere, small functions, `ruff check` clean.
    Run `pytest -q` and `ruff check .` before saying a milestone is done.

## Common commands

```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
ruff check .
python -m zoe.main --dry-run --no-jitter      # full pass, no Sheets writes, no alerts
python -m zoe.main --no-jitter                # real pass, now
python scripts/score_samples.py               # score samples/*.txt with the rubric
python scripts/gmail_auth.py                  # one-time Gmail consent
./scripts/install_launchd.sh                  # schedule it
tail -f logs/zoe.log
```

## The user

Steve is the product owner, not necessarily reading every line of code. When you
finish a milestone, summarize in plain language what now works, how to test it
himself (one command), and anything he has to do by hand (API keys, Google Cloud
console steps, etc.).
