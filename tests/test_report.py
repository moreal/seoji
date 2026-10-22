from seoji.report import fill_rates, issue_counts, source_coverage
from seoji.silver.build import rebuild_silver


def test_report_on_fixtures(loaded):
    rebuild_silver(loaded)
    editions = loaded.execute("SELECT count(*) AS n FROM silver.edition").fetchone()["n"]
    coverage = source_coverage(loaded)
    assert set(coverage) == {"lod_only", "nlseoji_only", "both"}
    assert sum(coverage.values()) == editions
    assert coverage["both"] == 1
    rates = {field: (n, ratio) for field, n, ratio in fill_rates(loaded)}
    assert rates["title"] == (editions, 1.0)
    assert 0 < rates["price_planned"][1] < 1
    assert issue_counts(loaded)["invalid_isbn"] == 2


def test_report_on_empty_db(db):
    assert fill_rates(db)[0][1:] == (0, 0.0)
    assert source_coverage(db) == {"lod_only": 0, "nlseoji_only": 0, "both": 0}
