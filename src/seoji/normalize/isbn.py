import re
from dataclasses import dataclass

KOREAN_PREFIXES = ("97889", "97911")

_ISBN_HEAD = re.compile(r"^\s*([0-9][0-9\- ]{8,16}[0-9Xx])(.*)$")
_SPLIT = re.compile(r"[\s,;]+")


@dataclass(frozen=True)
class IsbnValue:
    isbn13: str
    qualifier: str | None
    is_set: bool
    raw: str


def is_valid_isbn13(s: str) -> bool:
    if len(s) != 13 or not s.isdigit():
        return False
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(s))
    return total % 10 == 0


def is_valid_isbn10(s: str) -> bool:
    if len(s) != 10 or not s[:9].isdigit() or not (s[9].isdigit() or s[9] in "Xx"):
        return False
    digits = [int(d) for d in s[:9]] + [10 if s[9] in "Xx" else int(s[9])]
    return sum(d * w for d, w in zip(digits, range(10, 0, -1), strict=True)) % 11 == 0


def isbn10_to_13(isbn10: str) -> str:
    body = "978" + isbn10[:9]
    check = (10 - sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(body)) % 10) % 10
    return body + str(check)


def is_korean_isbn(isbn13: str) -> bool:
    return isbn13.startswith(KOREAN_PREFIXES)


def _strip_outer_parens(s: str) -> str:
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        return s[1:-1].strip()
    return s


def parse_isbn_value(raw: str) -> IsbnValue | None:
    """Split a raw ISBN value such as '9788925273112 (4)' into ISBN-13 and its qualifier."""
    m = _ISBN_HEAD.match(raw)
    if not m:
        return None
    digits = m.group(1).replace("-", "").replace(" ", "")
    if len(digits) == 10 and is_valid_isbn10(digits):
        isbn13 = isbn10_to_13(digits)
    elif len(digits) == 13 and is_valid_isbn13(digits):
        isbn13 = digits
    else:
        return None
    qualifier = _strip_outer_parens(m.group(2)) or None
    is_set = qualifier is not None and ("세트" in qualifier or qualifier.casefold() == "set")
    return IsbnValue(isbn13, None if is_set else qualifier, is_set, raw)


def split_isbn_list(raw: str) -> list[str]:
    return [t for t in _SPLIT.split(raw) if t]
