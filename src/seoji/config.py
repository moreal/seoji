import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATABASE_URL = "postgresql://seoji:seoji@localhost:55432/seoji"


@dataclass(frozen=True)
class Settings:
    database_url: str
    seoji_cert_key: str | None


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

    return Settings(
        database_url=get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        seoji_cert_key=get("SEOJI_CERT_KEY"),
    )
