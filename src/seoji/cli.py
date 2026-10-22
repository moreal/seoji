import argparse
import sys

from seoji.config import load_settings
from seoji.db import connect, migrate


def _cmd_db_migrate(args: argparse.Namespace) -> int:
    with connect(load_settings().database_url) as conn:
        applied = migrate(conn)
    print("\n".join(applied) if applied else "nothing to apply")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seoji")
    sub = parser.add_subparsers(dest="command", required=True)

    db = sub.add_parser("db").add_subparsers(dest="db_command", required=True)
    db.add_parser("migrate").set_defaults(func=_cmd_db_migrate)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
