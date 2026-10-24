import re


def test_index_loads_external_assets_only(api):
    html = api.get("/").text
    assert '<script src="/app.js" defer></script>' in html
    assert '<link rel="stylesheet" href="/style.css">' in html
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html), "inline scripts break the CSP"
    assert "style=" not in html


def test_assets_served_with_types(api):
    assert api.get("/app.js").headers["content-type"].startswith("text/javascript")
    assert api.get("/style.css").headers["content-type"].startswith("text/css")


def test_app_js_never_uses_innerhtml(api):
    js = api.get("/app.js").text
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "eval(" not in js


def test_href_filter_rejects_backslash_scheme_relative(api):
    js = api.get("/app.js").text
    assert "\\/(?![\\/\\\\])" in js
