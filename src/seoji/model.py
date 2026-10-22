from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Literal

from seoji.normalize.authors import Contributor

Source = Literal["lod", "nlseoji"]

FIELDS: tuple[str, ...] = (
    "title", "remainder_of_title", "title_hanja", "volume_label", "edition_statement",
    "responsibility_stmt", "publisher", "publication_place", "pub_date", "pub_date_precision",
    "extent_raw", "page_count", "height_cm", "width_mm", "height_mm", "volumes", "binding",
    "form", "ea_add_code", "kdc", "kdc_edition", "ddc", "nlk_call_no", "language",
    "original_title", "series_title", "series_no", "price_planned", "price_real", "cover_url",
    "deposit_yn", "cip_control_no", "related_isbn_raw",
)  # fmt: skip
_DATE_FIELDS = {"pub_date"}


@dataclass
class CandidateRecord:
    """One source's view of one ISBN, already normalized but not yet merged."""

    source: Source
    source_key: str
    isbn13: str
    fields: dict[str, Any] = field(default_factory=dict)
    contributors: list[Contributor] = field(default_factory=list)
    subjects: list[tuple[str, str, str | None]] = field(default_factory=list)
    rich_text: dict[str, str] = field(default_factory=dict)
    set_isbn13: str | None = None
    set_add_code: str | None = None
    set_expression: str | None = None
    observed_at: datetime | None = None

    def to_json(self) -> dict:
        d = asdict(self)
        d["fields"] = {k: v.isoformat() if k in _DATE_FIELDS else v for k, v in self.fields.items()}
        d["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        return d

    @classmethod
    def from_json(cls, d: dict) -> "CandidateRecord":
        d = dict(d)
        d["fields"] = {
            k: date.fromisoformat(v) if k in _DATE_FIELDS else v for k, v in d["fields"].items()
        }
        d["contributors"] = [Contributor(**c) for c in d["contributors"]]
        d["subjects"] = [tuple(s) for s in d["subjects"]]
        if d["observed_at"]:
            d["observed_at"] = datetime.fromisoformat(d["observed_at"])
        return cls(**d)


@dataclass(frozen=True)
class NoIsbnRecord:
    resource_uri: str
    title: str | None
    responsibility_stmt: str | None
    publisher: str | None
    issued_year: int | None
    kdc: str | None


@dataclass(frozen=True)
class InvalidIsbn:
    source: Source
    source_key: str
    raw: str
