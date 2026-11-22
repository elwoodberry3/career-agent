"""Load config.yaml + .env into a typed Settings object.  (Milestone 1)

Contract:
    load_settings(config_path="config.yaml", env_path=".env") -> Settings

- Settings is a pydantic model mirroring config.yaml sections
  (searches, sources, schedule, scoring, sheets, notify, paths) plus secrets from
  the environment (ANTHROPIC_API_KEY, RAPIDAPI_KEY, GOOGLE_SHEET_ID, ...).
- Secrets are pydantic SecretStr so they never print.
- Validate conditionally: e.g. RAPIDAPI_KEY is required only if sources.jsearch.enabled;
  GOOGLE_SHEET_ID only if sheets.enabled; channel keys only if notify.enabled.
- Raise ConfigError with a message naming each missing value and where to set it.
- Paths are resolved relative to the repo root (parent of the zoe/ package),
  so launchd can run from any working directory.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    pass


def load_settings(config_path: str | Path = "config.yaml", env_path: str | Path = ".env"):
    raise NotImplementedError("Milestone 1")
