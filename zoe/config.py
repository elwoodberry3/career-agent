"""Load config.yaml + .env into a typed, frozen Settings object.

Usage:
    from zoe.config import load_settings
    settings = load_settings()

    python -m zoe.config      # check your setup; prints a summary, never secret values

- Settings mirrors config.yaml (searches, sources, schedule, scoring, sheets, notify,
  paths) plus secrets from .env / the environment. Real environment variables win
  over .env. The process environment is never modified.
- Secrets are pydantic SecretStr so they never print.
- Requirements are conditional: RAPIDAPI_KEY only if sources.jsearch.enabled,
  GOOGLE_SHEET_ID only if sheets.enabled, channel keys only if notify.enabled.
- Every problem is reported at once in a single ConfigError naming what's missing
  and where to set it.
- Relative paths resolve against the repo root (parent of the zoe/ package), so
  launchd can run from any working directory.
"""

from __future__ import annotations

import os
import sys
from datetime import time
from pathlib import Path
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from dotenv import dotenv_values
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    ValidationInfo,
    field_validator,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    pass


def _resolve(value: Path, info: ValidationInfo) -> Path:
    """Make a relative path absolute against the root passed in validation context."""
    if value.is_absolute():
        return value
    root = (info.context or {}).get("root", REPO_ROOT)
    return (Path(root) / value).resolve()


RepoPath = Annotated[Path, AfterValidator(_resolve)]


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Search(_Section):
    name: str
    query: str
    location: str
    remote_ok: bool = True


class JSearchConfig(_Section):
    enabled: bool = False
    date_posted: str = "today"
    max_results_per_search: int = Field(default=20, gt=0)
    country: str = "us"


class GmailAlertsConfig(_Section):
    enabled: bool = False
    query: str = "from:(ziprecruiter.com) newer_than:2d"
    enrich_with_jsearch: bool = True


class SourcesConfig(_Section):
    jsearch: JSearchConfig = JSearchConfig()
    gmail_alerts: GmailAlertsConfig = GmailAlertsConfig()


class TimeWindow(_Section):
    """A daily window. `end` may be earlier than `start` (crosses midnight)."""

    start: time
    end: time


class ScheduleConfig(_Section):
    peak_hours: TimeWindow
    quiet_hours: TimeWindow
    off_peak_min_interval_minutes: int = Field(ge=0)
    jitter_seconds_max: int = Field(ge=0)


class ScoringConfig(_Section):
    model: str
    max_tokens: int = Field(gt=0)
    max_jobs_per_run: int = Field(gt=0)
    rubric_version: int = Field(ge=1)
    profile_path: RepoPath
    prompt_path: RepoPath


class SheetsConfig(_Section):
    enabled: bool = False
    worksheet: str
    columns: list[str] = Field(min_length=1)

    @field_validator("columns")
    @classmethod
    def _required_columns(cls, cols: list[str]) -> list[str]:
        missing = [c for c in ("Job ID", "Status") if c not in cols]
        if missing:
            raise ValueError(f"must include {missing}")
        if len(set(cols)) != len(cols):
            raise ValueError("column names must be unique")
        return cols


class NotifyConfig(_Section):
    enabled: bool = False
    threshold: int = Field(ge=0, le=100)
    channel: Literal["pushover", "telegram", "macos"]
    max_alerts_per_run: int = Field(gt=0)


class PathsConfig(_Section):
    db: RepoPath
    logs: RepoPath


class Secrets(_Section):
    """Values from .env / the environment. Field names match the env var names."""

    model_config = ConfigDict(extra="ignore", frozen=True, validate_default=True)

    ANTHROPIC_API_KEY: SecretStr | None = None
    RAPIDAPI_KEY: SecretStr | None = None
    RAPIDAPI_HOST: str = "jsearch.p.rapidapi.com"
    GOOGLE_SERVICE_ACCOUNT_FILE: RepoPath = Path("secrets/service_account.json")
    GOOGLE_SHEET_ID: SecretStr | None = None
    GMAIL_CREDENTIALS_FILE: RepoPath = Path("secrets/gmail_credentials.json")
    GMAIL_TOKEN_FILE: RepoPath = Path("secrets/gmail_token.json")
    PUSHOVER_USER_KEY: SecretStr | None = None
    PUSHOVER_APP_TOKEN: SecretStr | None = None
    TELEGRAM_BOT_TOKEN: SecretStr | None = None
    TELEGRAM_CHAT_ID: SecretStr | None = None


ENV_KEYS: tuple[str, ...] = tuple(Secrets.model_fields)


class Settings(_Section):
    timezone: str = "America/Chicago"
    searches: list[Search] = Field(min_length=1)
    sources: SourcesConfig = SourcesConfig()
    schedule: ScheduleConfig
    scoring: ScoringConfig
    sheets: SheetsConfig
    notify: NotifyConfig
    paths: PathsConfig
    secrets: Secrets = Secrets()
    repo_root: Path = REPO_ROOT

    @field_validator("timezone")
    @classmethod
    def _valid_timezone(cls, tz: str) -> str:
        try:
            ZoneInfo(tz)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(f"unknown timezone {tz!r}") from e
        return tz

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


# ---------------------------------------------------------------- loading


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"{path.name} is not valid YAML: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name} must be a mapping at the top level")
    return data


def _read_env(env_path: Path) -> dict[str, str]:
    """.env values overlaid by real environment variables; blanks are treated as unset."""
    merged: dict[str, str | None] = {}
    if env_path.is_file():
        merged.update(dotenv_values(env_path))
    for key in ENV_KEYS:
        if key in os.environ:
            merged[key] = os.environ[key]
    return {k: v.strip() for k, v in merged.items() if k in ENV_KEYS and v and v.strip()}


def _format_validation_error(e: ValidationError, source: str) -> str:
    lines = [f"Invalid configuration ({source}):"]
    for err in e.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(top level)"
        lines.append(f"  - {loc}: {err['msg']}")
    return "\n".join(lines)


def _missing_requirements(s: Settings) -> list[str]:
    sec = s.secrets
    problems: list[str] = []

    def need_secret(key: str, why: str) -> None:
        if getattr(sec, key) is None:
            problems.append(f"{key} is not set ({why}) — add it to .env")

    def need_file(path: Path, what: str, hint: str) -> None:
        if not path.is_file():
            problems.append(f"{what} not found at {path} — {hint}")

    need_secret("ANTHROPIC_API_KEY", "required for scoring")
    need_file(s.scoring.prompt_path, "Scoring prompt", "check scoring.prompt_path in config.yaml")
    need_file(
        s.scoring.profile_path,
        "Profile",
        "run `cp profile.example.md profile.md` and fill it in",
    )
    if s.sources.jsearch.enabled:
        need_secret("RAPIDAPI_KEY", "sources.jsearch.enabled is true")
    if s.sources.gmail_alerts.enabled:
        need_file(
            sec.GMAIL_CREDENTIALS_FILE,
            "Gmail OAuth client file (GMAIL_CREDENTIALS_FILE)",
            "see docs/BUILD_PLAN.md Milestone 7",
        )
    if s.sheets.enabled:
        need_secret("GOOGLE_SHEET_ID", "sheets.enabled is true")
        need_file(
            sec.GOOGLE_SERVICE_ACCOUNT_FILE,
            "Service account key (GOOGLE_SERVICE_ACCOUNT_FILE)",
            "see docs/BUILD_PLAN.md Milestone 6",
        )
    if s.notify.enabled:
        why = f"notify.enabled with channel {s.notify.channel}"
        if s.notify.channel == "pushover":
            need_secret("PUSHOVER_USER_KEY", why)
            need_secret("PUSHOVER_APP_TOKEN", why)
        elif s.notify.channel == "telegram":
            need_secret("TELEGRAM_BOT_TOKEN", why)
            need_secret("TELEGRAM_CHAT_ID", why)
    return problems


def load_settings(
    config_path: str | Path = "config.yaml",
    env_path: str | Path = ".env",
    *,
    root: str | Path = REPO_ROOT,
) -> Settings:
    """Load and validate settings. Raises ConfigError listing every problem found."""
    root = Path(root).resolve()
    config_path = root / config_path
    env_path = root / env_path

    data = _read_yaml(config_path)
    data["secrets"] = _read_env(env_path)
    data["repo_root"] = root

    try:
        settings = Settings.model_validate(data, context={"root": root})
    except ValidationError as e:
        raise ConfigError(_format_validation_error(e, f"{config_path.name} / .env")) from None

    problems = _missing_requirements(settings)
    if problems:
        raise ConfigError(
            "Zoe can't start — missing configuration:\n" + "\n".join(f"  - {p}" for p in problems)
        )
    return settings


# ---------------------------------------------------------------- CLI


def _summary(s: Settings) -> str:
    sources = [name for name, cfg in s.sources if cfg.enabled]
    lines = [
        f"Config OK  (repo: {s.repo_root})",
        f"  timezone:  {s.timezone}",
        f"  searches:  {len(s.searches)} ({', '.join(x.name for x in s.searches)})",
        f"  sources:   {', '.join(sources) or 'none enabled'}",
        f"  model:     {s.scoring.model}  (max {s.scoring.max_jobs_per_run} jobs/run)",
        f"  sheets:    {'on' if s.sheets.enabled else 'off'}",
        f"  notify:    {'on' if s.notify.enabled else 'off'} ({s.notify.channel}, "
        f"threshold {s.notify.threshold})",
        "  secrets:",
    ]
    for key in ENV_KEYS:
        value = getattr(s.secrets, key)
        if isinstance(value, SecretStr) or value is None:
            lines.append(f"    {'✓' if value is not None else '✗'} {key}")
    return "\n".join(lines)


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as e:
        print(e, file=sys.stderr)
        return 1
    print(_summary(settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
