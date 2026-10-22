import re
from datetime import datetime

from seoji.model import CandidateRecord, InvalidIsbn
from seoji.normalize.addcode import decode_add_code
from seoji.normalize.authors import parse_responsibility
from seoji.normalize.dates import parse_issued
from seoji.normalize.isbn import parse_isbn_value
from seoji.normalize.physical import parse_book_size
from seoji.normalize.text import clean_text, strip_hanja

_LEADING_INT = re.compile(r"^\s*(\d+)")
_RICH_TEXT = {"BOOK_TB_CNT": "toc", "BOOK_INTRODUCTION": "introduction", "BOOK_SUMMARY": "summary"}


def _text(doc: dict, key: str) -> str | None:
    return clean_text(doc.get(key))


def _int(value: str | None, *, digits_only: bool = False) -> int | None:
    if not value:
        return None
    if digits_only:
        value = re.sub(r"\D", "", value)
        return int(value) if value and int(value) != 0 else None
    m = _LEADING_INT.match(value)
    return int(m.group(1)) if m and int(m.group(1)) != 0 else None


def map_seoji_doc(
    doc: dict[str, str], observed_at: datetime
) -> CandidateRecord | InvalidIsbn | None:
    # A record with only SET_ISBN describes the set itself (e.g. SET_EXPRESSION "전6권").
    is_set_record = not _text(doc, "EA_ISBN") and bool(_text(doc, "SET_ISBN"))
    raw_isbn = _text(doc, "SET_ISBN") if is_set_record else _text(doc, "EA_ISBN")
    if not raw_isbn:
        return None
    isbn = parse_isbn_value(raw_isbn)
    if isbn is None:
        return InvalidIsbn("nlseoji", raw_isbn, raw_isbn)

    add_code = _text(doc, "SET_ADD_CODE" if is_set_record else "EA_ADD_CODE")
    decoded = decode_add_code(add_code)
    form = _text(doc, "FORM")
    if form == "오디오북":
        binding = "audio"
    elif _text(doc, "EBOOK_YN") == "Y" or (decoded is not None and decoded.form == "5"):
        binding = "ebook"
    else:
        binding = "paper"
    width, height = parse_book_size(_text(doc, "BOOK_SIZE"))
    pub_date, precision = parse_issued(_text(doc, "REAL_PUBLISH_DATE"))
    if pub_date is None:
        pub_date, precision = parse_issued(_text(doc, "PUBLISH_PREDATE"))
    deposit = _text(doc, "DEPOSIT_YN")

    fields: dict = {}
    if title := _text(doc, "TITLE"):
        fields["title"], hanja = strip_hanja(title)
        if hanja:
            fields["title_hanja"] = hanja
    fields |= {
        "volume_label": _text(doc, "VOL"),
        "series_title": _text(doc, "SERIES_TITLE"),
        "series_no": _text(doc, "SERIES_NO"),
        "responsibility_stmt": _text(doc, "AUTHOR"),
        "publisher": _text(doc, "PUBLISHER"),
        "edition_statement": _text(doc, "EDITION_STMT"),
        "price_planned": _int(doc.get("PRE_PRICE"), digits_only=True),
        "price_real": _int(doc.get("REAL_PRICE"), digits_only=True),
        "kdc": _text(doc, "KDC"),
        "ddc": _text(doc, "DDC"),
        "page_count": _int(doc.get("PAGE")),
        "width_mm": width,
        "height_mm": height,
        "form": form,
        "binding": binding,
        "pub_date": pub_date,
        "pub_date_precision": precision,
        "ea_add_code": add_code if decoded else None,
        "cover_url": _text(doc, "TITLE_URL"),
        "deposit_yn": {"Y": True, "N": False}.get(deposit or ""),
        "cip_control_no": _text(doc, "CONTROL_NO"),
        "related_isbn_raw": _text(doc, "RELATED_ISBN"),
    }
    fields = {k: v for k, v in fields.items() if v is not None}

    subjects: list[tuple[str, str, str | None]] = []
    for scheme in ("kdc", "ddc"):
        if code := fields.get(scheme):
            subjects.append((scheme, code, None))
    if decoded:
        subjects.append(("add_code", decoded.code, None))
    if subject := _text(doc, "SUBJECT"):
        subjects.append(("seoji_subject", subject, subject))

    set_isbn = None if is_set_record else parse_isbn_value(_text(doc, "SET_ISBN") or "")
    return CandidateRecord(
        source="nlseoji",
        source_key=isbn.isbn13,
        isbn13=isbn.isbn13,
        fields=fields,
        contributors=parse_responsibility(fields.get("responsibility_stmt")),
        subjects=subjects,
        rich_text={kind: body for key, kind in _RICH_TEXT.items() if (body := _text(doc, key))},
        set_isbn13=set_isbn.isbn13 if set_isbn else None,
        set_add_code=_text(doc, "SET_ADD_CODE"),
        set_expression=_text(doc, "SET_EXPRESSION"),
        observed_at=observed_at,
    )
