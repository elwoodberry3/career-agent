import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from zoe.config import ENV_KEYS, REPO_ROOT, ConfigError, Settings, load_settings

FAKE_KEY = "sk-ant-FAKE-DO-NOT-LEAK-123"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """A throwaway repo root with the real config.yaml + prompt, a dummy profile and .env."""
    shutil.copy(REPO_ROOT / "config.yaml", tmp_path / "config.yaml")
    (tmp_path / "prompts").mkdir()
    shutil.copy(REPO_ROOT / "prompts" / "scorer_system.md", tmp_path / "prompts")
    (tmp_path / "profile.md").write_text("# Test profile\n")
    (tmp_path / ".env").write_text(f"ANTHROPIC_API_KEY={FAKE_KEY}\n")
    return tmp_path


def edit_config(root: Path, **changes: dict) -> None:
    """Shallow-merge changes into top-level sections of the tmp config.yaml."""
    path = root / "config.yaml"
    data = yaml.safe_load(path.read_text())
    for section, value in changes.items():
        if isinstance(value, dict) and isinstance(data.get(section), dict):
            for k, v in value.items():
                if isinstance(v, dict) and isinstance(data[section].get(k), dict):
                    data[section][k].update(v)
                else:
                    data[section][k] = v
        else:
            data[section] = value
    path.write_text(yaml.safe_dump(data))


def write_env(root: Path, **values: str) -> None:
    (root / ".env").write_text("".join(f"{k}={v}\n" for k, v in values.items()))


def test_shipped_config_loads(root: Path) -> None:
    s = load_settings(root=root)
    assert s.timezone == "America/Chicago"
    assert len(s.searches) >= 1
    assert s.secrets.ANTHROPIC_API_KEY is not None
    assert s.secrets.ANTHROPIC_API_KEY.get_secret_value() == FAKE_KEY
    assert s.sources.jsearch.enabled is False  # until Milestone 4


def test_relative_paths_resolve_under_root(root: Path) -> None:
    s = load_settings(root=root)
    r = root.resolve()
    assert s.scoring.profile_path == r / "profile.md"
    assert s.scoring.prompt_path == r / "prompts" / "scorer_system.md"
    assert s.paths.db == r / "data" / "zoe_state.db"
    assert s.paths.logs == r / "logs"
    assert s.secrets.GOOGLE_SERVICE_ACCOUNT_FILE == r / "secrets" / "service_account.json"
    assert s.repo_root == r


def test_missing_anthropic_key(root: Path) -> None:
    write_env(root)
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        load_settings(root=root)


def test_blank_env_value_counts_as_missing(root: Path) -> None:
    write_env(root, ANTHROPIC_API_KEY="   ")
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        load_settings(root=root)


def test_missing_env_file_is_ok_if_environment_has_keys(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (root / ".env").unlink()
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    assert load_settings(root=root).secrets.ANTHROPIC_API_KEY is not None


def test_rapidapi_key_not_required_when_jsearch_disabled(root: Path) -> None:
    s = load_settings(root=root)
    assert s.secrets.RAPIDAPI_KEY is None


def test_rapidapi_key_required_when_jsearch_enabled(root: Path) -> None:
    edit_config(root, sources={"jsearch": {"enabled": True}})
    with pytest.raises(ConfigError, match="RAPIDAPI_KEY"):
        load_settings(root=root)
    write_env(root, ANTHROPIC_API_KEY=FAKE_KEY, RAPIDAPI_KEY="fake-rapid")
    assert load_settings(root=root).sources.jsearch.enabled


def test_all_problems_reported_together(root: Path) -> None:
    write_env(root)
    (root / "profile.md").unlink()
    edit_config(root, sources={"jsearch": {"enabled": True}}, sheets={"enabled": True})
    with pytest.raises(ConfigError) as exc:
        load_settings(root=root)
    msg = str(exc.value)
    for expected in ("ANTHROPIC_API_KEY", "RAPIDAPI_KEY", "GOOGLE_SHEET_ID", "Profile"):
        assert expected in msg


def test_missing_profile_points_to_example(root: Path) -> None:
    (root / "profile.md").unlink()
    with pytest.raises(ConfigError, match="profile.example.md"):
        load_settings(root=root)


def test_sheets_requires_sheet_id_and_key_file(root: Path) -> None:
    edit_config(root, sheets={"enabled": True})
    with pytest.raises(ConfigError) as exc:
        load_settings(root=root)
    assert "GOOGLE_SHEET_ID" in str(exc.value)
    assert "Service account key" in str(exc.value)


def test_notify_pushover_requires_keys(root: Path) -> None:
    edit_config(root, notify={"enabled": True, "channel": "pushover"})
    with pytest.raises(ConfigError) as exc:
        load_settings(root=root)
    assert "PUSHOVER_USER_KEY" in str(exc.value)
    assert "PUSHOVER_APP_TOKEN" in str(exc.value)


def test_notify_telegram_requires_keys(root: Path) -> None:
    edit_config(root, notify={"enabled": True, "channel": "telegram"})
    with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
        load_settings(root=root)


def test_notify_macos_needs_no_keys(root: Path) -> None:
    edit_config(root, notify={"enabled": True, "channel": "macos"})
    assert load_settings(root=root).notify.channel == "macos"


def test_unknown_key_is_readable_error(root: Path) -> None:
    edit_config(root, scoring={"max_job_per_run": 5})  # typo
    with pytest.raises(ConfigError, match=r"scoring\.max_job_per_run"):
        load_settings(root=root)


def test_bad_channel_is_readable_error(root: Path) -> None:
    edit_config(root, notify={"channel": "sms"})
    with pytest.raises(ConfigError, match=r"notify\.channel"):
        load_settings(root=root)


def test_bad_timezone_rejected(root: Path) -> None:
    edit_config(root, timezone="Mars/Olympus_Mons")
    with pytest.raises(ConfigError, match="timezone"):
        load_settings(root=root)


def test_bad_time_rejected(root: Path) -> None:
    edit_config(root, schedule={"peak_hours": {"start": "25:00"}})
    with pytest.raises(ConfigError, match=r"schedule\.peak_hours\.start"):
        load_settings(root=root)


def test_times_parse_including_cross_midnight(root: Path) -> None:
    s = load_settings(root=root)
    assert s.schedule.quiet_hours.start.hour == 23
    assert s.schedule.quiet_hours.end.hour == 6


def test_missing_config_file(root: Path) -> None:
    (root / "config.yaml").unlink()
    with pytest.raises(ConfigError, match="not found"):
        load_settings(root=root)


def test_invalid_yaml(root: Path) -> None:
    (root / "config.yaml").write_text("searches: [unclosed\n")
    with pytest.raises(ConfigError, match="not valid YAML"):
        load_settings(root=root)


def test_real_environment_overrides_dotenv(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-environment")
    s = load_settings(root=root)
    assert s.secrets.ANTHROPIC_API_KEY.get_secret_value() == "from-environment"


def test_secrets_never_printed(root: Path) -> None:
    s = load_settings(root=root)
    assert FAKE_KEY not in repr(s)
    assert FAKE_KEY not in str(s)
    assert FAKE_KEY not in s.model_dump_json()


def test_validation_errors_do_not_echo_secret_values(root: Path) -> None:
    edit_config(root, timezone="Nowhere/None")
    with pytest.raises(ConfigError) as exc:
        load_settings(root=root)
    assert FAKE_KEY not in str(exc.value)


def test_settings_are_frozen(root: Path) -> None:
    s = load_settings(root=root)
    with pytest.raises(ValidationError):
        s.timezone = "UTC"
    with pytest.raises(ValidationError):
        s.scoring.max_jobs_per_run = 10_000
    with pytest.raises(ValidationError):
        s.secrets.ANTHROPIC_API_KEY = None
    assert isinstance(s, Settings)
