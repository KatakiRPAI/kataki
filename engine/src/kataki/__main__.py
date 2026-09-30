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

from kataki import backups, data_dir, db, embed, knobs
from kataki.server import create_app


def default_db_path() -> Path:
    return data_dir() / "library.db"


def serve(db_path: Path, parent_watch: bool, port: int = 0, web: Path | None = None) -> None:
    token = os.environ.get("KATAKI_TOKEN")
    hello = {}
    # Headless use: mint a token and tell the user. A parent-supplied token is never echoed.
    if not token:
        token = hello["token"] = secrets.token_urlsafe(32)

    sock = socket.socket()
    sock.bind(("127.0.0.1", port))
    sock.listen()  # so clients that race the announcement queue instead of being refused
    hello["port"] = sock.getsockname()[1]
    if web is not None and "token" in hello:  # headless with the app: where to open it
        hello["open"] = f"http://127.0.0.1:{hello['port']}/app/?token={token}"
    print(json.dumps(hello), flush=True)

    # load (on first run, download) the built-in embedding model now, not on the first turn
    threading.Thread(target=embed.builtin, daemon=True).start()
    backups.apply_pending(db_path)  # a restore asked for last time happens before the library opens
    try:
        conn = db.connect(db_path)
    except db.LibraryTooNew as e:  # the shell reads this second line and says it
        print(json.dumps({"error": {"code": "LIBRARY_TOO_NEW", "message": str(e)}}), flush=True)
        sys.exit(3)
    config = uvicorn.Config(
        create_app(conn, token, web_dir=web, db_path=db_path), log_level="warning"
    )
    threading.Thread(target=_auto_backup, args=(conn, db_path), daemon=True).start()
    server = uvicorn.Server(config)
    if parent_watch:
        # The desktop shell holds our stdin. EOF means it quit or crashed: never outlive it.
        def watch():
            sys.stdin.buffer.read()
            server.should_exit = True

        threading.Thread(target=watch, daemon=True).start()
    server.run(sockets=[sock])


def serve_hosted(args: argparse.Namespace) -> None:
    """Kataki online (spec §8.4, track B4): many users, a library each, behind the gateway."""
    from kataki import hosted

    signing, key = hosted.secret("secret"), hosted.secret("key")
    if not (signing and key and args.root and args.catalogue and args.gateway):
        sys.exit(
            "kataki serve --hosted needs --root, --catalogue and --gateway, and the gateway's"
            " secrets in KATAKI_GATEWAY_SECRET and KATAKI_GATEWAY_KEY (or the keychain)."
        )
    app = hosted.Hosted(
        args.root,
        signing.encode(),
        hosted.Gateway(args.gateway, key),
        args.catalogue,
        max_open=args.max_open,
        idle=args.idle,
        daily_cap=args.daily_cap,
        max_calls=args.max_calls,
    )
    uvicorn.run(app, host=args.bind, port=args.port or 8000, log_level="warning", lifespan="on")


def _auto_backup(conn, db_path: Path) -> None:
    """Settings › Data › Backups: daily by default, in the background once the engine is up."""
    import time

    time.sleep(30)
    every = knobs.setting(conn, "backups.every", "daily")
    if backups.due(db_path, every):
        backups.make(conn, db_path, knobs.setting(conn, "backups.keep", "7"))


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
    s.add_argument("--web", type=Path, help="serve the built app (app/dist-web) under /app/")
    s.add_argument("--hosted", action="store_true", help="Kataki online: a library per user")
    s.add_argument("--root", type=Path, help="hosted: the folder that holds every user's library")
    s.add_argument("--catalogue", type=Path, help="hosted: the service's providers and prices")
    s.add_argument("--gateway", help="hosted: the gateway's base URL (allow, usage)")
    s.add_argument("--bind", default="127.0.0.1", help="hosted: the address to listen on")
    s.add_argument("--daily-cap", type=float, default=5.0, help="hosted: $ per user per day")
    s.add_argument("--max-calls", type=int, default=4, help="hosted: a user's calls in flight")
    s.add_argument("--max-open", type=int, default=64, help="hosted: libraries open at once")
    s.add_argument("--idle", type=float, default=900.0, help="hosted: seconds before one closes")
    c = sub.add_parser("chat", help="play a story in the terminal")
    c.add_argument("--db", type=Path, default=default_db_path())
    c.add_argument("--story", type=int, help="default: the newest story")
    args = parser.parse_args(argv)
    if args.cmd == "serve" and args.hosted:
        serve_hosted(args)
    elif args.cmd == "serve":
        serve(args.db, args.parent_watch, args.port, args.web)
    elif args.cmd == "chat":
        asyncio.run(chat(args.db, args.story))


if __name__ == "__main__":
    main()
