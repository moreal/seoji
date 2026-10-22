import html
import re
import unicodedata

_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")
_MIDDLE_DOTS = str.maketrans({"·": " ", "ㆍ": " ", "･": " ", "・": " "})
_BRACKETS = re.compile(r"[()\[\]{}<>「」『』【】〈〉《》（）［］]")
_NON_WORD = re.compile(r"[\W_]+", re.UNICODE)
_HANJA = r"㐀-䶿一-鿿豈-﫿"
_HANJA_PREFIX = re.compile(rf"^([{_HANJA}]+)\s+(.*\S.*)$")


def clean_text(s: str | None) -> str | None:
    if s is None:
        return None
    s = html.unescape(_TAG.sub("", s))
    s = _SPACE.sub(" ", unicodedata.normalize("NFC", s)).strip()
    return s or None


def compare_key(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).casefold().translate(_MIDDLE_DOTS)
    s = _BRACKETS.sub(" ", s)
    return _NON_WORD.sub("", s)


def strip_hanja(s: str) -> tuple[str, str | None]:
    """Split a leading hanja gloss off a title, e.g. '戰國 전국 스트레이즈'."""
    m = _HANJA_PREFIX.match(s)
    if not m or re.fullmatch(rf"[{_HANJA}\s]+", m.group(2)):
        return s, None
    return m.group(2), m.group(1)
