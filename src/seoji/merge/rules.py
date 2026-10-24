from datetime import date, timedelta
from typing import Any

from seoji.model import FIELDS

_NLSEOJI_FIRST = {
    "price_planned", "price_real", "ea_add_code", "form", "binding", "cover_url", "deposit_yn",
    "cip_control_no", "width_mm", "height_mm", "related_isbn_raw",
}  # fmt: skip
_DATE_RULE = {"pub_date", "pub_date_precision"}  # decided by choose_pub_date

PRECEDENCE: dict[str, tuple[str, ...]] = {
    f: ("nlseoji", "lod") if f in _NLSEOJI_FIRST else ("lod", "nlseoji")
    for f in FIELDS
    if f not in _DATE_RULE
}


# Plausible ranges for numeric fields; anything outside (e.g. a price of 10^15 seen in Seoji)
# is treated as missing so the next source can win.
NUMBER_RANGES: dict[str, tuple[float, float]] = {
    "page_count": (1, 20_000),
    "price_planned": (1, 100_000_000),
    "price_real": (1, 100_000_000),
    "width_mm": (10, 2_000),
    "height_mm": (10, 2_000),
    "height_cm": (1, 200),
    "volumes": (1, 10_000),
}


def is_valid(field: str, value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return value.strip() not in ("", "0")
    if field in NUMBER_RANGES:
        low, high = NUMBER_RANGES[field]
        return low <= value <= high
    if field == "pub_date":
        return date(1400, 1, 1) <= value <= date.today() + timedelta(days=730)
    if isinstance(value, int | float):
        return value != 0
    return True
