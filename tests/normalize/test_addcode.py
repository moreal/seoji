from seoji.normalize.addcode import FORM_LABELS, READER_LABELS, AddCode, decode_add_code


def test_decode_valid():
    assert decode_add_code("03810") == AddCode("03810", "0", "3", "8", "81")


def test_decode_rejects_wrong_length_or_empty():
    assert decode_add_code("0381") is None
    assert decode_add_code("") is None
    assert decode_add_code(None) is None


def test_labels_follow_nlk_table():
    assert "2" not in READER_LABELS
    assert READER_LABELS["7"] == "아동"
    assert FORM_LABELS["5"] == "전자출판물"
