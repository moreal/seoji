from seoji.lod.parse import LodResource, Value
from seoji.model import CandidateRecord, InvalidIsbn, NoIsbnRecord
from seoji.normalize.authors import parse_responsibility
from seoji.normalize.dates import parse_issued
from seoji.normalize.isbn import IsbnValue, parse_isbn_value
from seoji.normalize.physical import parse_extent
from seoji.normalize.text import clean_text, compare_key, strip_hanja

NLON = "http://lod.nl.go.kr/ontology/"
BIBO = "http://purl.org/ontology/bibo/"
DC = "http://purl.org/dc/elements/1.1/"
DCT = "http://purl.org/dc/terms/"
BF = "http://id.loc.gov/ontologies/bibframe/"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"


def _texts(res: LodResource, pred: str) -> list[str]:
    out = []
    for v in res.body.get(pred, []):
        raw = v if isinstance(v, str) else v.get("@value")
        if (text := clean_text(raw)) is not None:
            out.append(text)
    return out


def _first(res: LodResource, pred: str) -> str | None:
    values = _texts(res, pred)
    return values[0] if values else None


def _iris(res: LodResource, pred: str) -> list[str]:
    return [v["@id"] for v in res.body.get(pred, []) if isinstance(v, dict) and "@id" in v]


def _last_segment(iri: str) -> str:
    return iri.rstrip("/").rsplit("/", 1)[-1]


def _label_parts(res: LodResource) -> tuple[str | None, str | None]:
    label = _first(res, RDFS_LABEL)
    if not label:
        return None, None
    title, sep, stmt = label.partition(" / ")
    return title.strip(), (stmt.strip() or None) if sep else None


def _title(res: LodResource, label_title: str | None) -> str | None:
    titles = sorted(_texts(res, DCT + "title"))
    if label_title:
        key = compare_key(label_title)
        for t in titles:
            if compare_key(t) == key:
                return t
    return titles[0] if titles else label_title


def _shared_fields(res: LodResource) -> tuple[dict, list, list, dict]:
    label_title, stmt = _label_parts(res)
    fields: dict = {}
    if title := _title(res, label_title):
        fields["title"], hanja = strip_hanja(title)
        if hanja:
            fields["title_hanja"] = hanja
    pub_date, precision = parse_issued(_first(res, DCT + "issued"))
    if pub_date is None:
        pub_date, precision = parse_issued(_first(res, NLON + "issuedYear"))
    extent = _texts(res, BF + "extent")
    physical = parse_extent(extent)
    cls_no, item_no = (
        _first(res, NLON + "classificationNumberOfNLK"),
        _first(res, NLON + "itemNumberOfNLK"),
    )
    languages = _iris(res, BF + "language")
    fields |= {
        "remainder_of_title": _first(res, NLON + "remainderOfTitle"),
        "responsibility_stmt": stmt,
        "publisher": _first(res, DC + "publisher"),
        "publication_place": _first(res, NLON + "publicationPlace"),
        "pub_date": pub_date,
        "pub_date_precision": precision,
        "extent_raw": " ; ".join(extent) or None,
        "page_count": physical.page_count,
        "height_cm": physical.height_cm,
        "volumes": physical.volumes,
        "kdc": _first(res, NLON + "kdc"),
        "kdc_edition": _first(res, NLON + "editionOfKDC"),
        "ddc": _first(res, NLON + "ddc"),
        "nlk_call_no": f"{cls_no}-{item_no}" if cls_no and item_no else None,
        "edition_statement": _first(res, BIBO + "edition"),
        "series_title": _first(res, NLON + "titleOfSeries"),
        "series_no": _first(res, NLON + "volumeOfSeries"),
        "original_title": _first(res, NLON + "titleOfTranslation"),
        "language": _last_segment(languages[0]) if languages else None,
    }
    fields = {k: v for k, v in fields.items() if v is not None}

    contributors = parse_responsibility(stmt)
    if not contributors:
        contributors = parse_responsibility(" ; ".join(_texts(res, DC + "creator")))

    subjects: list[tuple[str, str, str | None]] = []
    if kdc := fields.get("kdc"):
        subjects.append(("kdc", kdc, None))
    if ddc := fields.get("ddc"):
        subjects.append(("ddc", ddc, None))
    subjects += [("ksh", _last_segment(iri), None) for iri in _iris(res, DCT + "subject")]
    subjects += [("nlk_keyword", kw, kw) for kw in _texts(res, NLON + "keyword")]

    rich_text = {}
    if toc := _texts(res, DCT + "tableOfContents"):
        rich_text["toc"] = "\n".join(toc)
    if abstract := _texts(res, DCT + "description"):
        rich_text["abstract"] = "\n".join(abstract)
    return fields, contributors, subjects, rich_text


def map_lod_resource(
    res: LodResource,
) -> tuple[list[CandidateRecord], NoIsbnRecord | None, list[InvalidIsbn]]:
    raw_isbns: list[Value] = res.body.get(BIBO + "isbn", [])
    if not raw_isbns:
        label_title, stmt = _label_parts(res)
        pub_date, _ = parse_issued(_first(res, DCT + "issued"))
        return (
            [],
            NoIsbnRecord(
                res.uri,
                _title(res, label_title),
                stmt,
                _first(res, DC + "publisher"),
                pub_date.year if pub_date else None,
                _first(res, NLON + "kdc"),
            ),
            [],
        )

    parsed: list[IsbnValue] = []
    invalid: list[InvalidIsbn] = []
    seen: set[str] = set()
    for raw in raw_isbns:
        text = raw if isinstance(raw, str) else raw.get("@value", "")
        value = parse_isbn_value(text)
        if value is None:
            invalid.append(InvalidIsbn("lod", res.uri, text))
        elif value.isbn13 not in seen:
            seen.add(value.isbn13)
            parsed.append(value)
    if not parsed:
        return [], None, invalid

    fields, contributors, subjects, rich_text = _shared_fields(res)
    set_isbn = next((v.isbn13 for v in parsed if v.is_set), None)
    # bibo:volume describes the whole resource, so it only labels a single-ISBN record.
    resource_volume = _first(res, BIBO + "volume") if len(parsed) == 1 else None

    cands = []
    for value in parsed:
        own = dict(fields)
        if label := value.qualifier or (None if value.is_set else resource_volume):
            own["volume_label"] = label
        cands.append(
            CandidateRecord(
                source="lod",
                source_key=res.uri,
                isbn13=value.isbn13,
                fields=own,
                contributors=list(contributors),
                subjects=list(subjects),
                rich_text=dict(rich_text),
                set_isbn13=None if value.is_set else set_isbn,
            )
        )
    return cands, None, invalid
