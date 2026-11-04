from app.core.settings import Settings, get_settings


def test_settings_defaults_are_safe(monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.delenv("MAX_UPLOAD_MB", raising=False)
    settings = Settings(_env_file=None)
    assert settings.debug is False
    assert settings.max_upload_mb == 200
    assert settings.environment == "development"


def test_settings_read_environment_values(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("MAX_UPLOAD_MB", "64")
    settings = Settings(_env_file=None)
    assert settings.debug is True
    assert settings.max_upload_mb == 64


def test_settings_reject_unsafe_upload_limit(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    try:
        Settings(_env_file=None)
    except Exception as exc:
        assert "MAX_UPLOAD_MB" in str(exc)
    else:
        raise AssertionError("Invalid upload size should be rejected")


def test_cached_settings_can_be_refreshed():
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()
    assert get_settings() is not first
