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


def test_public_service_settings_defaults(tmp_path, monkeypatch):
    for key in (
        "SEOJI_PUBLIC_RICH_TEXT",
        "SEOJI_CONTACT",
        "SEOJI_RATE_LIMIT_PER_MINUTE",
        "SEOJI_TRUST_FORWARDED_FOR",
        "SEOJI_ALLOWED_HOSTS",
        "SEOJI_CORS_ORIGINS",
    ):
        monkeypatch.delenv(key, raising=False)
    s = load_settings(env_file=tmp_path / "none.env")
    assert s.public_rich_text is False
    assert s.contact is None
    assert s.rate_limit_per_minute == 60
    assert s.trust_forwarded_for is False
    assert s.allowed_hosts == ("localhost", "127.0.0.1")
    assert s.cors_origins == ()


def test_public_service_settings_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SEOJI_PUBLIC_RICH_TEXT", "true")
    monkeypatch.setenv("SEOJI_CONTACT", "takedown@example.org")
    monkeypatch.setenv("SEOJI_RATE_LIMIT_PER_MINUTE", "30")
    monkeypatch.setenv("SEOJI_TRUST_FORWARDED_FOR", "1")
    monkeypatch.setenv("SEOJI_ALLOWED_HOSTS", "books.example.org, localhost")
    monkeypatch.setenv("SEOJI_CORS_ORIGINS", "https://app.example")
    s = load_settings(env_file=tmp_path / "none.env")
    assert (s.public_rich_text, s.contact, s.rate_limit_per_minute, s.trust_forwarded_for) == (
        True,
        "takedown@example.org",
        30,
        True,
    )
    assert s.allowed_hosts == ("books.example.org", "localhost")
    assert s.cors_origins == ("https://app.example",)
