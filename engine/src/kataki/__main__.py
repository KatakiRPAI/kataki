"""CLI: `kataki serve` (the engine for the app) and `kataki chat` (a terminal REPL)."""

import argparse
import asyncio
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


def serve(db_path: Path, parent_watch: bool, port: int = 0) -> None:
    token = os.environ.get("KATAKI_TOKEN")
    hello = {}
    # Headless use: mint a token and tell the user. A parent-supplied token is never echoed.
    if not token:
        token = hello["token"] = secrets.token_urlsafe(32)

    sock = socket.socket()
    sock.bind(("127.0.0.1", port))
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


async def chat(db_path: Path, story_id: int | None) -> None:
    """Play a story in the terminal: the engine with no app around it.

    A line is your turn; an empty line lets the story continue; /again asks for another
    take; /read reads what is waiting into memory now; /quit leaves.
    """
    from kataki import extract, turns  # only the REPL needs these
    from kataki.llm import LLM

    conn, llm = db.connect(db_path), LLM()
    story = conn.execute(
        "SELECT * FROM stories WHERE id=? OR ? IS NULL ORDER BY id DESC", (story_id, story_id)
    ).fetchone()
    if story is None:
        sys.exit("No story yet. Create one in the app first.")
    print(f"{story['title']}  (empty line: continue, /again, /read, /quit)\n")
    while (line := (await asyncio.to_thread(input, "> ")).strip()) != "/quit":
        if line == "/read":
            run_id = await extract.run_due(conn, llm, story["id"], manual=True)
            row = conn.execute("SELECT * FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
            print(f"  read: {row['status']} {row['error'] or ''}" if row else "  nothing waiting")
            continue
        events = (
            turns.regenerate(conn, llm, story["id"])
            if line == "/again"
            else turns.turn(conn, llm, story["id"], line or None)
        )
        async for kind, data in events:
            if kind == "meta":
                print(f"\n{(data['speaker'] or {}).get('name', 'Narrator')}: ", end="", flush=True)
            elif kind == "token":
                print(data, end="", flush=True)
            elif kind == "error":
                print(f"\n  [error] {data['message']}")
        print("\n")
        await extract.run_due(conn, llm, story["id"])  # no background worker here: read inline
    await llm.aclose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="kataki")
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="run the local engine server")
    s.add_argument("--db", type=Path, default=default_db_path())
    s.add_argument("--parent-watch", action="store_true", help="exit when stdin closes")
    s.add_argument("--port", type=int, default=0, help="default: any free port")
    c = sub.add_parser("chat", help="play a story in the terminal")
    c.add_argument("--db", type=Path, default=default_db_path())
    c.add_argument("--story", type=int, help="default: the newest story")
    args = parser.parse_args(argv)
    if args.cmd == "serve":
        serve(args.db, args.parent_watch, args.port)
    elif args.cmd == "chat":
        asyncio.run(chat(args.db, args.story))


if __name__ == "__main__":
    main()
