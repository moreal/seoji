import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATABASE_URL = "postgresql://seoji:seoji@localhost:55432/seoji"


@dataclass(frozen=True)
class Settings:
    database_url: str
    seoji_cert_key: str | None
    # Public service (seoji serve)
    public_database_url: str | None = None  # login as seoji_public; else SET ROLE seoji_public
    public_rich_text: bool = False  # 책소개·목차·서평·초록; keep off unless NLK confirms in writing
    contact: str | None = None  # where takedown requests go
    rate_limit_per_minute: int = 60
    trust_forwarded_for: bool = False  # only behind a reverse proxy that sets X-Forwarded-For
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1")
    cors_origins: tuple[str, ...] = ()  # browsers on other sites may call the API only if listed


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load_settings(env_file: Path = Path(".env")) -> Settings:
    """Read settings from the environment, falling back to a .env file."""
    file_values = _read_dotenv(env_file)

    def get(key: str) -> str | None:
        return os.environ.get(key) or file_values.get(key) or None

    def flag(key: str) -> bool:
        return (get(key) or "").strip().lower() in ("1", "true", "yes", "on")

    def items(key: str) -> tuple[str, ...]:
        return tuple(v.strip() for v in (get(key) or "").split(",") if v.strip())

    hosts = items("SEOJI_ALLOWED_HOSTS")
    return Settings(
        database_url=get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        seoji_cert_key=get("SEOJI_CERT_KEY"),
        public_database_url=get("SEOJI_PUBLIC_DATABASE_URL"),
        public_rich_text=flag("SEOJI_PUBLIC_RICH_TEXT"),
        contact=get("SEOJI_CONTACT"),
        rate_limit_per_minute=int(get("SEOJI_RATE_LIMIT_PER_MINUTE") or 60),
        trust_forwarded_for=flag("SEOJI_TRUST_FORWARDED_FOR"),
        allowed_hosts=hosts or ("localhost", "127.0.0.1"),
        cors_origins=items("SEOJI_CORS_ORIGINS"),
    )
