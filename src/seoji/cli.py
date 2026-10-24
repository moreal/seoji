import argparse
import sys
from datetime import date
from pathlib import Path

from seoji.config import load_settings
from seoji.db import connect, migrate
from seoji.gold.build import rebuild_search_doc
from seoji.lod.load import load_dump
from seoji.lod.parse import FORMATS
from seoji.lod.sparql import sparql_construct, sparql_count_books
from seoji.nlseoji.client import SeojiClient
from seoji.nlseoji.harvest import harvest_all, harvest_range, window_dates
from seoji.query import QueryError, normalize_isbn
from seoji.report import fill_rates, issue_counts, source_coverage
from seoji.silver.build import rebuild_silver, refresh_silver


def _cmd_db_migrate(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        applied = migrate(conn)
    print("\n".join(applied) if applied else "nothing to apply")
    return 0


def _cmd_lod_load(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        stats = load_dump(
            conn,
            args.path,
            dataset=args.dataset,
            fmt=args.format,
            dump_date=date.fromisoformat(args.dump_date) if args.dump_date else None,
            mark_missing=args.mark_missing,
        )
    print(stats)
    return 0


def _cmd_lod_fetch(args: argparse.Namespace) -> int:
    uris = [u if u.startswith("http") else f"http://lod.nl.go.kr/resource/{u}" for u in args.uris]
    Path(args.output).write_bytes(sparql_construct(uris))
    return 0


def _cmd_lod_count(args: argparse.Namespace) -> int:
    print(sparql_count_books())
    return 0


def _cmd_harvest(args: argparse.Namespace) -> int:
    settings = load_settings()
    if not settings.seoji_cert_key:
        print("SEOJI_CERT_KEY가 필요합니다 (.env 또는 환경변수)", file=sys.stderr)
        return 2
    if args.all:

        def progress(page: int, size: int, total: int) -> None:
            if page % 50 == 0 or page * size >= total:
                last = -(-total // size)
                print(f"page {page}/{last} ({min(page * size, total):,}/{total:,})", flush=True)

        with connect(settings.database_url) as conn:
            stats = harvest_all(
                conn,
                SeojiClient(settings.seoji_cert_key),
                page_size=args.page_size or 1000,
                restart=args.restart,
                max_pages=args.max_pages,
                on_page=progress,
            )
        print(stats)
        return 0
    if args.window:
        start, end = window_dates(args.window, date.today())
    elif args.date_from and args.date_to:
        start, end = date.fromisoformat(args.date_from), date.fromisoformat(args.date_to)
    else:
        print("--all, --window 또는 --from/--to 를 지정하세요", file=sys.stderr)
        return 2
    with connect(settings.database_url) as conn:
        stats = harvest_range(
            conn, SeojiClient(settings.seoji_cert_key), start, end, page_size=args.page_size or 100
        )
    print(stats)
    return 0


def _cmd_silver(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        stats = rebuild_silver(conn) if args.silver_command == "rebuild" else refresh_silver(conn)
    print(stats)
    return 0


def _cmd_gold_rebuild(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        print(f"{rebuild_search_doc(conn)} search documents")
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        rows = conn.execute(
            "SELECT * FROM gold.search_books(%s, %s, %s)",
            (args.query, args.limit, args.korean_only),
        ).fetchall()
    for r in rows:
        year = r["pub_year"] or ""
        print(f"{r['isbn13']}\t{r['title']}\t{r['authors'] or ''}\t{r['publisher'] or ''}\t{year}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        print("# source coverage")
        for key, n in source_coverage(conn).items():
            print(f"{key}\t{n}")
        print("\n# open merge issues")
        for kind, n in issue_counts(conn).items():
            print(f"{kind}\t{n}")
        print("\n# fill rates (silver.edition)")
        for field, n, ratio in fill_rates(conn):
            print(f"{field}\t{n}\t{ratio:.1%}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from seoji.server.app import create_app

    settings = load_settings()
    uvicorn.run(
        create_app(settings),
        host=args.host,
        port=args.port,
        proxy_headers=settings.trust_forwarded_for,
        forwarded_allow_ips=args.forwarded_allow_ips if settings.trust_forwarded_for else None,
        server_header=False,
    )
    return 0


def _cmd_takedown(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        if args.takedown_command == "list":
            for r in conn.execute("SELECT * FROM gold.takedown ORDER BY created_at"):
                print(f"{r['isbn13']}\t{r['reason'] or ''}\t{r['created_at']:%Y-%m-%d}")
            return 0
        try:
            isbn13 = normalize_isbn(args.isbn)
        except QueryError as e:
            print(e.message, file=sys.stderr)
            return 2
        if args.takedown_command == "add":
            conn.execute(
                "INSERT INTO gold.takedown (isbn13, reason) VALUES (%s, %s)"
                " ON CONFLICT (isbn13) DO UPDATE SET reason = EXCLUDED.reason",
                (isbn13, args.reason),
            )
        else:
            conn.execute("DELETE FROM gold.takedown WHERE isbn13 = %s", (isbn13,))
        conn.commit()
    print(f"{args.takedown_command} {isbn13}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seoji")
    sub = parser.add_subparsers(dest="command", required=True)

    db = sub.add_parser("db").add_subparsers(dest="db_command", required=True)
    db.add_parser("migrate").set_defaults(func=_cmd_db_migrate)

    lod = sub.add_parser("lod").add_subparsers(dest="lod_command", required=True)
    p = lod.add_parser("load", help="load an LOD dump file into bronze")
    p.add_argument("path", type=Path)
    p.add_argument("--dataset", default="book")
    p.add_argument("--format", choices=sorted(FORMATS), default="ttl")
    p.add_argument("--dump-date")
    p.add_argument("--mark-missing", action="store_true")
    p.set_defaults(func=_cmd_lod_load)
    p = lod.add_parser("fetch", help="fetch resources via SPARQL as RDF/XML")
    p.add_argument("uris", nargs="+")
    p.add_argument("-o", "--output", required=True)
    p.set_defaults(func=_cmd_lod_fetch)
    lod.add_parser("count", help="count bibo:Book via SPARQL").set_defaults(func=_cmd_lod_count)

    p = sub.add_parser("harvest", help="harvest the NLK Seoji API by publish date")
    p.add_argument("--from", dest="date_from")
    p.add_argument("--to", dest="date_to")
    p.add_argument("--window", choices=["daily", "weekly"])
    p.add_argument("--all", action="store_true", help="page through every record (resumable)")
    p.add_argument("--restart", action="store_true", help="with --all: ignore the saved cursor")
    p.add_argument("--max-pages", type=int, help="with --all: stop after N pages")
    p.add_argument("--page-size", type=int, help="default 1000 for --all, 100 otherwise")
    p.set_defaults(func=_cmd_harvest)

    silver = sub.add_parser("silver").add_subparsers(dest="silver_command", required=True)
    silver.add_parser("rebuild", help="recompute silver from bronze").set_defaults(func=_cmd_silver)
    silver.add_parser("refresh", help="re-merge rows changed since the last build").set_defaults(
        func=_cmd_silver
    )

    gold = sub.add_parser("gold").add_subparsers(dest="gold_command", required=True)
    gold.add_parser("rebuild", help="rebuild search documents").set_defaults(func=_cmd_gold_rebuild)

    p = sub.add_parser("search", help="search titles, authors, publishers and series")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--korean-only", action="store_true")
    p.set_defaults(func=_cmd_search)

    sub.add_parser("report", help="coverage, issues and fill rates").set_defaults(func=_cmd_report)

    p = sub.add_parser("serve", help="run the public web, REST API and MCP server")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument(
        "--forwarded-allow-ips", default="127.0.0.1",
        help="proxies trusted for X-Forwarded-For (only with SEOJI_TRUST_FORWARDED_FOR)",
    )  # fmt: skip
    p.set_defaults(func=_cmd_serve)

    takedown = sub.add_parser("takedown", help="hide ISBNs from every public channel")
    takedown_sub = takedown.add_subparsers(dest="takedown_command", required=True)
    p = takedown_sub.add_parser("add")
    p.add_argument("isbn")
    p.add_argument("--reason")
    p.set_defaults(func=_cmd_takedown)
    p = takedown_sub.add_parser("remove")
    p.add_argument("isbn")
    p.set_defaults(func=_cmd_takedown)
    takedown_sub.add_parser("list").set_defaults(func=_cmd_takedown)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
