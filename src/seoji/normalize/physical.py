import re
from dataclasses import dataclass

_PAGES = re.compile(r"(\d+)\s*(?:p|쪽|면)(?![a-z])", re.IGNORECASE)
_HEIGHT = re.compile(r"(\d+(?:\.\d+)?)\s*cm", re.IGNORECASE)
_VOLUMES = re.compile(r"(\d+)\s*책")
_BOOK_SIZE = re.compile(r"^\s*(\d+)\s*[*x×]\s*(\d+)\s*$")


@dataclass(frozen=True)
class Physical:
    page_count: int | None
    height_cm: float | None
    volumes: int | None


def parse_extent(values: list[str]) -> Physical:
    pages = height = volumes = None
    for value in values:
        if volumes is None and (m := _VOLUMES.search(value)):
            volumes = int(m.group(1))
        if height is None and (m := _HEIGHT.search(value)):
            height = float(m.group(1))
        if pages is None and (m := _PAGES.search(value)):
            pages = int(m.group(1))
    if volumes is not None:
        pages = None
    return Physical(pages, height, volumes)


def parse_book_size(s: str | None) -> tuple[int | None, int | None]:
    """Seoji BOOK_SIZE '183*235' is width*height in millimetres."""
    m = _BOOK_SIZE.match(s or "")
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))
