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


def is_valid(field: str, value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return value.strip() not in ("", "0")
    if field == "page_count":
        return 1 <= value <= 20000
    if field == "pub_date":
        return date(1400, 1, 1) <= value <= date.today() + timedelta(days=730)
    if isinstance(value, int | float):
        return value != 0
    return True
