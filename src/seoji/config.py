import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "postgresql://seoji:seoji@localhost:55432/seoji"


@dataclass(frozen=True)
class Settings:
    database_url: str
    seoji_cert_key: str | None


def load_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        seoji_cert_key=os.environ.get("SEOJI_CERT_KEY") or None,
    )
