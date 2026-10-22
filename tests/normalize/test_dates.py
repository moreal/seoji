from datetime import date

from seoji.normalize.dates import parse_issued


def test_year():
    assert parse_issued("2017") == (date(2017, 1, 1), "year")


def test_year_range_takes_start():
    assert parse_issued("2010-2015") == (date(2010, 1, 1), "year")


def test_minguo_with_bracketed_year():
    assert parse_issued("民國82[1993]") == (date(1993, 1, 1), "year")


def test_day_forms():
    assert parse_issued("20220509") == (date(2022, 5, 9), "day")
    assert parse_issued("2022-05-09") == (date(2022, 5, 9), "day")


def test_month():
    assert parse_issued("202205") == (date(2022, 5, 1), "month")


def test_unparseable_or_out_of_range():
    assert parse_issued("미상") == (None, None)
    assert parse_issued("1200") == (None, None)
    assert parse_issued(None) == (None, None)
