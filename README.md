# career-agent — Zoe Lancaster

A personal job scout that runs on a Mac every ~45–65 minutes, finds newly posted
jobs, scores each one against your profile with Claude, logs everything to a
Google Sheet, and pings your phone for strong matches.

Built with Claude Code. Architecture, rules and build order live in
[`CLAUDE.md`](CLAUDE.md) and [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md).

## Quick start

```bash
git clone https://github.com/elwoodberry3/career-agent.git
cd career-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # add ANTHROPIC_API_KEY
cp profile.example.md profile.md  # fill in your profile
pytest -q                         # model tests should pass
claude                            # start Claude Code here
```

Then, in Claude Code:

> Read CLAUDE.md and docs/BUILD_PLAN.md. Plan Milestone 1 and show me the plan before writing code.

## What is never committed

`.env`, `profile.md`, `secrets/`, `data/`, `logs/`, `samples/*.txt`. See `.gitignore`.

## Status

| Milestone | Status |
|---|---|
| 0 Environment | ☐ |
| 1 Config + models | ☐ |
| 2 Scorer | ☐ |
| 3 SQLite state | ☐ |
| 4 JSearch ingestion | ☐ |
| 5 Orchestrator (dry run) | ☐ |
| 6 Google Sheets | ☐ |
| 7 Gmail alerts | ☐ |
| 8 Calibration week | ☐ |
| 9 Notifications | ☐ |
| 10 launchd | ☐ |
