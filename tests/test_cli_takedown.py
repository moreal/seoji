from seoji.cli import main


def test_takedown_add_list_remove(db, migrated_url, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", migrated_url)
    assert main(["takedown", "add", "978-89-364-3426-7", "--reason", "출판사 요청"]) == 0
    assert main(["takedown", "list"]) == 0
    assert "9788936434267\t출판사 요청" in capsys.readouterr().out
    assert main(["takedown", "remove", "9788936434267"]) == 0
    assert db.execute("SELECT count(*) AS n FROM gold.takedown").fetchone()["n"] == 0


def test_takedown_rejects_invalid_isbn(db, migrated_url, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", migrated_url)
    assert main(["takedown", "add", "12345"]) == 2
    assert "ISBN" in capsys.readouterr().err
