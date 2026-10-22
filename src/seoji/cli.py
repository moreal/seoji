import argparse
import sys
from datetime import date
from pathlib import Path

from seoji.config import load_settings
from seoji.db import connect, migrate
from seoji.lod.load import load_dump
from seoji.lod.parse import FORMATS
from seoji.lod.sparql import sparql_construct, sparql_count_books


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

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
