import re
from datetime import date

MIN_YEAR, MAX_YEAR = 1400, 2100

_BRACKET_YEAR = re.compile(r"\[(\d{4})\]")
_DAY = re.compile(r"^(\d{4})-?(\d{2})-?(\d{2})$")
_MONTH = re.compile(r"^(\d{4})-?(\d{2})$")
_YEAR = re.compile(r"(?<!\d)(\d{4})(?!\d)")


def _make(year: int, month: int = 1, day: int = 1) -> date | None:
    if not MIN_YEAR <= year <= MAX_YEAR:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_issued(s: str | None) -> tuple[date | None, str | None]:
    if not s:
        return None, None
    s = s.strip()
    patterns = ((_DAY, "day"), (_MONTH, "month"), (_BRACKET_YEAR, "year"), (_YEAR, "year"))
    for pattern, precision in patterns:
        m = pattern.match(s) if precision != "year" else pattern.search(s)
        if m:
            d = _make(*(int(g) for g in m.groups()))
            if d:
                return d, precision
    return None, None
