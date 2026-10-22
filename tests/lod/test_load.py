from seoji.lod.load import load_dump
from tests.lod_helpers import NLK, SAMPLE_KR

ALMOND = NLK + "KJU201703899"


def _changed_at(db):
    return dict(
        (r["resource_uri"], r["changed_at"])
        for r in db.execute("SELECT resource_uri, changed_at FROM bronze.lod_resource")
    )


def test_load_dump_counts(db):
    stats = load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    assert (stats.resources, stats.inserted, stats.changed) == (9, 9, 0)
    assert db.execute("SELECT count(*) AS n FROM bronze.lod_resource").fetchone()["n"] == 9


def test_reload_same_dump_is_noop(db):
    load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    before = _changed_at(db)
    stats = load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    assert (stats.inserted, stats.changed, stats.unchanged) == (0, 0, 9)
    assert _changed_at(db) == before


def test_changed_body_updates_changed_at(db, make_nt):
    load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    before = _changed_at(db)
    path = make_nt("retitled.nt", retitle={ALMOND: "아몬드 (개정판)"})
    stats = load_dump(db, path, dataset="book", fmt="nt", dump_date=None)
    assert stats.changed == 1
    after = _changed_at(db)
    assert [uri for uri in after if after[uri] != before[uri]] == [ALMOND]


def test_mark_missing_tombstones(db, make_nt):
    load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    stats = load_dump(
        db,
        make_nt("eight.nt", drop={ALMOND}),
        dataset="book",
        fmt="nt",
        dump_date=None,
        mark_missing=True,
    )
    assert stats.tombstoned == 1
    row = db.execute(
        "SELECT deleted_at FROM bronze.lod_resource WHERE resource_uri = %s", (ALMOND,)
    ).fetchone()
    assert row["deleted_at"] is not None
    load_dump(db, SAMPLE_KR, dataset="book", fmt="rdfxml", dump_date=None)
    row = db.execute(
        "SELECT deleted_at FROM bronze.lod_resource WHERE resource_uri = %s", (ALMOND,)
    ).fetchone()
    assert row["deleted_at"] is None
