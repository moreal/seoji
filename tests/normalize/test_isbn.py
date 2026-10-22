from seoji.normalize.isbn import (
    IsbnValue,
    is_korean_isbn,
    is_valid_isbn10,
    is_valid_isbn13,
    isbn10_to_13,
    parse_isbn_value,
    split_isbn_list,
)


def test_volume_qualifier():
    v = parse_isbn_value("9788925273112 (4)")
    assert v == IsbnValue("9788925273112", "4", False, "9788925273112 (4)")


def test_set_qualifier_korean():
    v = parse_isbn_value("9788925268736 (세트)")
    assert v.is_set is True
    assert v.qualifier is None


def test_set_qualifier_english_lowercase():
    assert parse_isbn_value("9788961596749 (set)").is_set is True


def test_nested_parentheses_qualifier():
    assert parse_isbn_value("9791155971611 (32(완결))").qualifier == "32(완결)"


def test_isbn10_with_x_converted():
    assert parse_isbn_value("895298143X (5)").isbn13 == "9788952981431"


def test_hyphenated():
    assert parse_isbn_value("978-89-364-3426-7").isbn13 == "9788936434267"


def test_bad_checksum_rejected():
    assert parse_isbn_value("9788936434268") is None


def test_no_digits_rejected():
    assert parse_isbn_value("세트") is None


def test_validators_and_conversion():
    assert is_valid_isbn13("9788936434267")
    assert not is_valid_isbn13("9788936434268")
    assert is_valid_isbn10("895298143X")
    assert isbn10_to_13("895298143X") == "9788952981431"


def test_korean_prefixes():
    assert is_korean_isbn("9788936434267")
    assert is_korean_isbn("9791160979053")
    assert not is_korean_isbn("9787520124560")


def test_split_isbn_list():
    assert split_isbn_list("9788936434267 9791160979053;8952981430, ") == [
        "9788936434267",
        "9791160979053",
        "8952981430",
    ]


def test_isbn13_to_10():
    from seoji.normalize.isbn import isbn13_to_10

    assert isbn13_to_10("9788952981431") == "895298143X"
    assert isbn13_to_10("9788936434267") == "8936434268"
    assert isbn13_to_10("9791160979053") is None


def test_unparenthesized_qualifier():
    v = parse_isbn_value("9788925273112 4")
    assert (v.isbn13, v.qualifier) == ("9788925273112", "4")


def test_two_isbns_in_one_value_keeps_first():
    assert parse_isbn_value("9788925273112 9788936434267").isbn13 == "9788925273112"


def test_qualifier_without_space():
    v = parse_isbn_value("9788925273112(21)")
    assert v is not None and v.qualifier == "21"
