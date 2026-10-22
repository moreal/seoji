import re
from dataclasses import dataclass

_ROLE_WORDS: dict[str, tuple[str, ...]] = {}
for _role, _words in {
    "author": ("지은이", "지음", "저", "저자", "글", "글쓴이", "著", "撰", "작가"),
    "translator": ("옮김", "옮긴이", "역", "역자", "번역", "譯"),
    "illustrator": ("그림", "그린이", "그림작가"),
    "editor": ("엮음", "엮은이", "편", "편저", "編", "편집"),
    "original_author": ("원작",),
    "supervisor": ("감수",),
    "photographer": ("사진",),
}.items():
    for _w in _words:
        _ROLE_WORDS[_w] = (_role,)
for _w in ("글·그림", "글그림", "글/그림", "글ㆍ그림"):
    _ROLE_WORDS[_w] = ("author", "illustrator")

_PREFIX = re.compile(r"^([^:：]{1,12})\s*[:：]\s*(.+)$")
_ETC = re.compile(r"\s*(?:\.\.\.|…)?\s*(?:等.*|외|\[外\]|등)\s*$")


@dataclass(frozen=True)
class Contributor:
    name: str
    role: str
    role_raw: str | None


def _names(part: str) -> list[str]:
    names = []
    for name in part.split(","):
        name = _ETC.sub("", name).strip(" .")
        if name:
            names.append(name)
    return names


def _emit(names: list[str], role_raw: str | None) -> list[Contributor]:
    if role_raw is None:
        roles: tuple[str, ...] = ("author",)
    else:
        roles = _ROLE_WORDS.get(role_raw, ("other",))
    return [Contributor(n, r, role_raw) for n in names for r in roles]


def parse_responsibility(stmt: str | None) -> list[Contributor]:
    """Parse a statement such as '글: A ; 그림: B ;역자: C' or 'A 저 ; B,C 역'."""
    if not stmt:
        return []
    stmt = stmt.strip()
    if stmt.startswith("[") and stmt.endswith("]"):
        stmt = stmt[1:-1]
    out: list[Contributor] = []
    for group in stmt.split(";"):
        group = group.strip()
        if not group:
            continue
        m = _PREFIX.match(group)
        if m:
            out += _emit(_names(m.group(2)), m.group(1).strip())
            continue
        head, _, last = group.rpartition(" ")
        if head and last in _ROLE_WORDS:
            out += _emit(_names(head), last)
        else:
            out += _emit(_names(group), None)
    return out
