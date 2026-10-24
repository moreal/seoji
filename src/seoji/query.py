"""Read-only queries behind every public channel (REST API, MCP, web).

Only the fields listed here ever leave the database. Publisher- or reviewer-written text
(책소개·목차·서평·초록) is returned only when the caller opts in, which the server does only when
SEOJI_PUBLIC_RICH_TEXT is set. Limits on page size and depth keep the database from being
copied wholesale through the API.
"""

import re
import unicodedata
from datetime import date
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import psycopg

from seoji.config import Settings
from seoji.normalize.addcode import FORM_LABELS, READER_LABELS
from seoji.normalize.isbn import parse_isbn_value

MAX_LIMIT = 50
MAX_OFFSET = 1000
MAX_QUERY_LENGTH = 100  # after NFKC, which can expand one character into many
COVER_HOSTS = ("www.nl.go.kr", "nl.go.kr")  # every cover URL in the data points here
MAX_TERMS = 8  # each term is one pg_bigm LIKE; dozens of one-letter terms cost seconds
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
ATTRIBUTION = (
    "서지 데이터 출처: 국립중앙도서관 ISBN 서지정보 유통지원시스템(Seoji), "
    "국립중앙도서관 국가서지 LOD(공공누리 제1유형·CC0 1.0)"
)
NOTICE = (
    "책소개·목차·서평은 출판사·저자·평론가의 저작물일 수 있어 제공하지 않습니다. "
    "표지 이미지는 국립중앙도서관 원본 주소로 연결만 합니다."
)

PUBLIC_EDITION_FIELDS: tuple[str, ...] = (
    "isbn13", "isbn10", "title", "remainder_of_title", "title_hanja", "volume_label",
    "edition_statement", "responsibility_stmt", "publisher", "publication_place", "pub_date",
    "pub_date_precision", "pub_status", "page_count", "height_cm", "width_mm", "height_mm",
    "binding", "form", "ea_add_code", "add_reader", "add_form", "add_kdc_class",
    "add_kdc_division", "kdc", "ddc", "nlk_call_no", "language", "original_title",
    "series_title", "series_no", "price_planned", "price_real", "deposit_yn", "is_korean",
)  # fmt: skip
BOOK_EXTRA_FIELDS: tuple[str, ...] = (
    "cover_url", "add_code_labels", "contributors", "subjects", "sets", "sources", "links",
    "attribution", "rich_text",
)  # fmt: skip
SEARCH_ITEM_FIELDS: tuple[str, ...] = (
    "isbn13", "title", "authors", "publisher", "pub_year", "binding", "volume_label",
    "cover_url",
)  # fmt: skip
_NOT_TAKEN_DOWN = "NOT EXISTS (SELECT 1 FROM gold.takedown t WHERE t.isbn13 = {col})"


class QueryError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_isbn(raw: str) -> str:
    value = parse_isbn_value(raw.strip()) if raw else None
    if value is None or value.qualifier is not None:
        raise QueryError("invalid_isbn", "ISBN-10 또는 ISBN-13 형식이 아닙니다")
    return value.isbn13


def public_cover_url(url: str | None) -> str | None:
    """Cover URLs are hotlinked, never copied: only NLK hosts, rebuilt as plain https URLs."""
    if not url:
        return None
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError:
        return None
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or host not in COVER_HOSTS:
        return None
    if parts.username or parts.password or port not in (None, 80, 443):
        return None
    return urlunsplit(("https", host, parts.path, parts.query, ""))


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def search(
    conn: psycopg.Connection,
    q: str,
    *,
    limit: int = 20,
    offset: int = 0,
    korean_only: bool = False,
) -> dict:
    q = (q or "").strip()
    if _CONTROL.search(q):
        raise QueryError("invalid_query", "검색어에 제어 문자를 쓸 수 없습니다")
    if not q:
        raise QueryError("empty_query", "검색어를 입력하세요")
    normalized = unicodedata.normalize("NFKC", q)
    if len(normalized) > MAX_QUERY_LENGTH:
        raise QueryError("query_too_long", f"검색어는 {MAX_QUERY_LENGTH}자 이하여야 합니다")
    if len(normalized.split()) > MAX_TERMS:
        raise QueryError("too_many_terms", f"검색어는 {MAX_TERMS}단어 이하여야 합니다")
    if not 1 <= limit <= MAX_LIMIT:
        raise QueryError("limit_out_of_range", f"limit은 1~{MAX_LIMIT} 사이여야 합니다")
    if not 0 <= offset <= MAX_OFFSET:
        raise QueryError("offset_out_of_range", f"offset은 0~{MAX_OFFSET} 사이여야 합니다")
    rows = conn.execute(
        """
        SELECT s.isbn13, s.title, s.authors, s.publisher, s.pub_year,
               e.binding, e.volume_label, e.cover_url
          FROM gold.search_books(%s, %s, %s, %s) s
          JOIN silver.edition e USING (isbn13)
        """,
        (q, limit + 1, korean_only, offset),
    ).fetchall()
    items = [
        {k: _json_value(r[k]) for k in SEARCH_ITEM_FIELDS}
        | {"cover_url": public_cover_url(r["cover_url"])}
        for r in rows[:limit]
    ]
    return {"query": q, "limit": limit, "offset": offset, "has_more": len(rows) > limit,
            "items": items}  # fmt: skip


def get_book(
    conn: psycopg.Connection, isbn: str, *, include_rich_text: bool = False
) -> dict | None:
    isbn13 = normalize_isbn(isbn)
    row = conn.execute(
        "SELECT * FROM silver.edition e WHERE isbn13 = %s AND "
        + _NOT_TAKEN_DOWN.format(col="e.isbn13"),
        (isbn13,),
    ).fetchone()
    if row is None:
        return None
    book = {k: _json_value(row[k]) for k in PUBLIC_EDITION_FIELDS}
    book["cover_url"] = public_cover_url(row["cover_url"])
    book["add_code_labels"] = {
        "reader": READER_LABELS.get(row["add_reader"] or ""),
        "form": FORM_LABELS.get(row["add_form"] or ""),
    }
    book["contributors"] = [
        {"name": r["name"], "role": r["role"]}
        for r in conn.execute(
            "SELECT name, role FROM silver.edition_contributor WHERE isbn13 = %s ORDER BY ordinal",
            (isbn13,),
        )
    ]
    book["subjects"] = [
        {"scheme": r["scheme"], "code": r["code"], "label": r["label"]}
        for r in conn.execute(
            "SELECT DISTINCT scheme, code, label FROM silver.edition_subject WHERE isbn13 = %s"
            " ORDER BY scheme, code",
            (isbn13,),
        )
    ]
    book["sets"] = [
        {"set_isbn13": r["set_isbn13"], "title": r["title"], "total_volumes": r["total_volumes"]}
        for r in conn.execute(
            "SELECT b.set_isbn13, b.title, b.total_volumes FROM silver.set_member m"
            " JOIN silver.book_set b USING (set_isbn13) WHERE m.isbn13 = %s AND "
            + _NOT_TAKEN_DOWN.format(col="b.set_isbn13")
            + " ORDER BY 1",
            (isbn13,),
        )
    ]
    book["sources"] = row["provenance"]
    book["links"] = {"nlk_lod": row["primary_resource_uri"]} if row["primary_resource_uri"] else {}
    book["attribution"] = ATTRIBUTION
    if include_rich_text:
        rich: dict[str, list[dict]] = {}
        for r in conn.execute(
            "SELECT kind, source, body FROM silver.edition_rich_text WHERE isbn13 = %s"
            " ORDER BY kind, source",
            (isbn13,),
        ):
            rich.setdefault(r["kind"], []).append({"source": r["source"], "body": r["body"]})
        book["rich_text"] = rich
    return book


def get_set(conn: psycopg.Connection, set_isbn: str) -> dict | None:
    set_isbn13 = normalize_isbn(set_isbn)
    row = conn.execute(
        "SELECT * FROM silver.book_set b WHERE set_isbn13 = %s AND "
        + _NOT_TAKEN_DOWN.format(col="b.set_isbn13"),
        (set_isbn13,),
    ).fetchone()
    if row is None:
        return None
    members = conn.execute(
        f"""
        SELECT e.isbn13, e.title, e.volume_label, e.pub_date
          FROM silver.set_member m JOIN silver.edition e USING (isbn13)
         WHERE m.set_isbn13 = %s AND {_NOT_TAKEN_DOWN.format(col="e.isbn13")}
         ORDER BY e.isbn13
        """,
        (set_isbn13,),
    ).fetchall()
    return {
        "set_isbn13": set_isbn13,
        "title": row["title"],
        "set_expression": row["set_expression"],
        "total_volumes": row["total_volumes"],
        "is_open_ended": row["is_open_ended"],
        "members": [
            {k: _json_value(m[k]) for k in ("isbn13", "title", "volume_label", "pub_date")}
            for m in members
        ],  # fmt: skip
        "attribution": ATTRIBUTION,
    }


def meta(conn: psycopg.Connection, settings: Settings) -> dict:
    build = conn.execute(
        "SELECT finished_at, editions FROM silver.build_state"
        " WHERE kind = 'rebuild' AND finished_at IS NOT NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return {
        "name": "seoji",
        "attribution": ATTRIBUTION,
        "notice": NOTICE,
        "contact": settings.contact,
        "last_rebuild_at": build["finished_at"].isoformat() if build else None,
        "editions": build["editions"] if build else None,
        "limits": {"max_limit": MAX_LIMIT, "max_offset": MAX_OFFSET},
        "rich_text": settings.public_rich_text,
    }
