from seoji.normalize.authors import Contributor, parse_responsibility


def test_prefix_role():
    assert parse_responsibility("지은이: 손원평") == [Contributor("손원평", "author", "지은이")]


def test_multiple_prefix_roles_keep_order():
    assert parse_responsibility("글: Tadashi Agi ; 그림: Shu Okimoto ;역자: 설은미") == [
        Contributor("Tadashi Agi", "author", "글"),
        Contributor("Shu Okimoto", "illustrator", "그림"),
        Contributor("설은미", "translator", "역자"),
    ]


def test_suffix_roles_with_comma_names():
    assert parse_responsibility("아즈마 키요히코 저 ; 금정,김동욱 역") == [
        Contributor("아즈마 키요히코", "author", "저"),
        Contributor("금정", "translator", "역"),
        Contributor("김동욱", "translator", "역"),
    ]


def test_combined_text_and_art_role():
    assert parse_responsibility("글·그림: Hisaya Nakajo ; 옮긴이: 정효진") == [
        Contributor("Hisaya Nakajo", "author", "글·그림"),
        Contributor("Hisaya Nakajo", "illustrator", "글·그림"),
        Contributor("정효진", "translator", "옮긴이"),
    ]


def test_trailing_etc_marker_removed():
    assert parse_responsibility("胡廣...等纂修")[0].name == "胡廣"


def test_bracketed_editor():
    assert parse_responsibility("[이퍼블릭 편]") == [Contributor("이퍼블릭", "editor", "편")]


def test_no_role_defaults_to_author():
    assert parse_responsibility("박은아") == [Contributor("박은아", "author", None)]


def test_empty():
    assert parse_responsibility(None) == []
    assert parse_responsibility("") == []
