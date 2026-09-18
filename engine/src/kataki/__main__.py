"""CLI: `kataki serve`."""

import argparse
import json
import os
import secrets
import socket
import sys
import threading
from pathlib import Path

import uvicorn

from kataki import db
from kataki.server import create_app


def default_db_path() -> Path:
    base = (
        os.environ.get("APPDATA") or os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share"
    )
    return Path(base) / "Kataki" / "library.db"


def serve(db_path: Path, parent_watch: bool) -> None:
    token = os.environ.get("KATAKI_TOKEN")
    hello = {}
    # Headless use: mint a token and tell the user. A parent-supplied token is never echoed.
    if not token:
        token = hello["token"] = secrets.token_urlsafe(32)

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen()  # so clients that race the announcement queue instead of being refused
    hello["port"] = sock.getsockname()[1]
    print(json.dumps(hello), flush=True)

    config = uvicorn.Config(create_app(db.connect(db_path), token), log_level="warning")
    server = uvicorn.Server(config)
    if parent_watch:
        # The desktop shell holds our stdin. EOF means it quit or crashed: never outlive it.
        def watch():
            sys.stdin.buffer.read()
            server.should_exit = True

        threading.Thread(target=watch, daemon=True).start()
    server.run(sockets=[sock])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="kataki")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="run the local engine server")
    s.add_argument("--db", type=Path, default=default_db_path())
    s.add_argument("--parent-watch", action="store_true", help="exit when stdin closes")
    args = parser.parse_args(argv)
    if args.cmd == "serve":
        serve(args.db, args.parent_watch)


if __name__ == "__main__":
    main()
