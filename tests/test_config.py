import importlib


def test_api_base_and_scopes():
    from health_data_connect import config

    assert config.GOOGLE_API_BASE == "https://health.googleapis.com/v4"
    # First slice: sleep + activity, read-only, least privilege.
    assert "googlehealth.sleep.readonly" in config.GOOGLE_SCOPES
    assert "googlehealth.activity_and_fitness.readonly" in config.GOOGLE_SCOPES


def test_config_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("HEALTH_DATA_CONNECT_CONFIG_DIR", str(tmp_path))
    from health_data_connect import config

    importlib.reload(config)
    try:
        assert config.GOOGLE_CLIENT_PATH == tmp_path / "google_client.json"
        assert config.GOOGLE_TOKENS_PATH == tmp_path / "google_tokens.json"
    finally:
        monkeypatch.delenv("HEALTH_DATA_CONNECT_CONFIG_DIR", raising=False)
        importlib.reload(config)
