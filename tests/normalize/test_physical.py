from seoji.normalize.physical import Physical, parse_book_size, parse_extent


def test_pages_and_height():
    assert parse_extent(["263 p", "20 cm"]) == Physical(263, 20.0, None)


def test_roman_prefix_and_compact_forms():
    assert parse_extent(["xii, 263 p."]).page_count == 263
    assert parse_extent(["485p", "27cm"]) == Physical(485, 27.0, None)
    assert parse_extent(["263쪽"]).page_count == 263


def test_multi_volume():
    assert parse_extent(["15책", "19 cm"]) == Physical(None, 19.0, 15)


def test_illustration_only():
    assert parse_extent(["삽화, 도표"]) == Physical(None, None, None)


def test_book_size():
    assert parse_book_size("183*235") == (183, 235)
    assert parse_book_size("") == (None, None)
    assert parse_book_size(None) == (None, None)
