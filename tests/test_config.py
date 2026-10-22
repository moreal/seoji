from seoji.config import load_settings


def test_reads_dotenv_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("SEOJI_CERT_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    (tmp_path / ".env").write_text("# comment\nSEOJI_CERT_KEY = 'abc123'\nUNRELATED=1\n")
    s = load_settings(env_file=tmp_path / ".env")
    assert s.seoji_cert_key == "abc123"
    assert s.database_url.endswith("/seoji")


def test_environment_wins_over_dotenv(tmp_path, monkeypatch):
    monkeypatch.setenv("SEOJI_CERT_KEY", "from-env")
    (tmp_path / ".env").write_text("SEOJI_CERT_KEY=from-file\n")
    assert load_settings(env_file=tmp_path / ".env").seoji_cert_key == "from-env"


def test_missing_dotenv_is_fine(tmp_path, monkeypatch):
    monkeypatch.delenv("SEOJI_CERT_KEY", raising=False)
    assert load_settings(env_file=tmp_path / "nope.env").seoji_cert_key is None
