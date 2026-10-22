from seoji.normalize.text import clean_text, compare_key, strip_hanja


def test_clean_text_strips_html_and_unescapes():
    assert clean_text("<b>아몬드</b> &amp; 친구") == "아몬드 & 친구"


def test_clean_text_blank_is_none():
    assert clean_text("  ") is None
    assert clean_text(None) is None


def test_clean_text_composes_jamo_to_nfc():
    assert clean_text("가") == "가"


def test_compare_key_ignores_parentheses_and_punctuation():
    assert compare_key("(소년탐정) 김전일!") == compare_key("소년탐정 김전일")


def test_compare_key_middle_dot_is_space():
    assert compare_key("스킵·비트!") == compare_key("스킵 비트")


def test_compare_key_fullwidth_casefold():
    assert compare_key("ＡＢＣ") == "abc"


def test_strip_hanja_prefix():
    assert strip_hanja("戰國 전국 스트레이즈") == ("전국 스트레이즈", "戰國")


def test_strip_hanja_only_hanja_unchanged():
    assert strip_hanja("北京圖書館古籍珍本叢刊") == ("北京圖書館古籍珍本叢刊", None)
