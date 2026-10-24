import psycopg
import pytest

ALMOND = "9788936434267"


def test_search(api):
    r = api.get("/api/v1/search", params={"q": "아몬드"})
    assert r.status_code == 200
    body = r.json()
    assert body["items"][0]["isbn13"] == ALMOND
    assert r.headers["cache-control"].startswith("public")


def test_search_out_of_policy_is_400(api):
    r = api.get("/api/v1/search", params={"q": "아몬드", "limit": 500})
    assert r.status_code == 400
    assert r.json() == {
        "error": {"code": "limit_out_of_range", "message": "limit은 1~50 사이여야 합니다"}
    }


def test_search_missing_query_is_400(api):
    r = api.get("/api/v1/search")
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_request"


def test_book(api):
    r = api.get(f"/api/v1/books/{ALMOND}")
    assert r.status_code == 200
    assert r.json()["title"] == "아몬드"
    assert "rich_text" not in r.json()


def test_book_rich_text_only_when_enabled(make_api, built):
    # Opening rich text is a two-step decision: the flag and an explicit grant.
    built.execute("GRANT SELECT ON silver.edition_rich_text TO seoji_public")
    built.commit()
    try:
        r = make_api(public_rich_text=True).get(f"/api/v1/books/{ALMOND}")
        assert "introduction" in r.json()["rich_text"]
    finally:
        built.execute("REVOKE SELECT ON silver.edition_rich_text FROM seoji_public")
        built.commit()


def test_book_not_found_and_invalid(api):
    assert api.get("/api/v1/books/9791180000027").json() == {
        "error": {"code": "not_found", "message": "해당 ISBN의 책이 없습니다"}
    }
    assert api.get("/api/v1/books/9791180000027").status_code == 404
    r = api.get("/api/v1/books/abc")
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_isbn"


def test_set(api):
    r = api.get("/api/v1/sets/9788993171440")
    assert r.status_code == 200 and len(r.json()["members"]) == 6


def test_meta(api):
    body = api.get("/api/v1/meta").json()
    assert body["contact"] == "takedown@example.org" and body["rich_text"] is False


def test_healthz(api):
    assert api.get("/healthz").json() == {"ok": True}


def test_security_headers(api):
    r = api.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    csp = r.headers["content-security-policy"]
    assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "no-referrer"


def test_unknown_host_rejected(api):
    r = api.get("/api/v1/meta", headers={"host": "evil.example.com"})
    assert r.status_code == 400


def test_only_get_allowed_on_api(api):
    assert api.post("/api/v1/search", params={"q": "x"}).status_code == 405


def test_rate_limit(make_api):
    client = make_api(rate_limit_per_minute=3)
    codes = [client.get("/api/v1/meta").status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    r = client.get("/api/v1/meta")
    assert int(r.headers["retry-after"]) >= 1
    assert r.json()["error"]["code"] == "rate_limited"


def test_static_files_not_rate_limited(make_api):
    client = make_api(rate_limit_per_minute=1)
    assert [client.get("/").status_code for _ in range(3)] == [200, 200, 200]


def test_database_connections_are_read_only(api):
    with (
        api.app.state.pool.connection() as conn,
        pytest.raises(psycopg.errors.ReadOnlySqlTransaction),
    ):
        conn.execute("INSERT INTO gold.takedown (isbn13) VALUES ('9788936434267')")


def test_statement_timeout_is_503(make_api, monkeypatch):
    import seoji.server.app as app_module

    monkeypatch.setattr(app_module, "STATEMENT_TIMEOUT", "1ms")
    r = make_api().get("/api/v1/search", params={"q": "재판 이야기 좌충우돌"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "query_timeout"


def test_pool_runs_as_least_privilege_role(api):
    with api.app.state.pool.connection() as conn:
        assert conn.execute("SELECT current_user AS u").fetchone()["u"] == "seoji_public"
        conn.execute("SET default_transaction_read_only = off")  # even if read-only is undone…
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("INSERT INTO gold.takedown (isbn13) VALUES ('9788936434267')")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1 FROM silver.edition_rich_text LIMIT 1",
        "SELECT 1 FROM bronze.source_record LIMIT 1",
        "SELECT 1 FROM silver.field_provenance LIMIT 1",
    ],
)
def test_pool_cannot_read_non_public_tables(api, sql):
    with (
        api.app.state.pool.connection() as conn,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        conn.execute(sql)


def test_pool_exhaustion_is_503(make_api, monkeypatch):
    import seoji.server.app as app_module

    monkeypatch.setattr(app_module, "POOL_TIMEOUT", 0.05)
    client = make_api()
    pool = client.app.state.pool
    held = [pool.getconn() for _ in range(pool.max_size)]
    try:
        r = client.get("/api/v1/search", params={"q": "아몬드"})
        assert r.status_code == 503 and r.json()["error"]["code"] == "busy"
    finally:
        for conn in held:
            pool.putconn(conn)


def test_nul_byte_is_400_not_500(api):
    r = api.get("/api/v1/search", params={"q": "abc\x00def"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_query"


def test_rejections_still_carry_security_headers(make_api):
    client = make_api(rate_limit_per_minute=1)
    client.get("/api/v1/meta")
    limited = client.get("/api/v1/meta")
    wrong_host = client.get("/api/v1/meta", headers={"host": "evil.example.com"})
    for r in (limited, wrong_host):
        assert "default-src 'self'" in r.headers["content-security-policy"], r.status_code
        assert r.headers["x-content-type-options"] == "nosniff"


def test_csp_limits_images_to_cover_hosts(api):
    csp = api.get("/").headers["content-security-policy"]
    assert "img-src 'self' https://www.nl.go.kr https://nl.go.kr" in csp


def test_docs_ui_disabled_but_schema_served(api):
    assert api.get("/api/docs").status_code == 404
    assert api.get("/api/openapi.json").status_code == 200


def test_cors_off_by_default(api):
    r = api.get("/api/v1/meta", headers={"origin": "https://other.example"})
    assert "access-control-allow-origin" not in r.headers


def test_cors_for_configured_origins(make_api):
    client = make_api(cors_origins=("https://app.example",))
    ok = client.get("/api/v1/meta", headers={"origin": "https://app.example"})
    other = client.get("/api/v1/meta", headers={"origin": "https://other.example"})
    assert ok.headers["access-control-allow-origin"] == "https://app.example"
    assert "access-control-allow-origin" not in other.headers
