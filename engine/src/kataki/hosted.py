"""Kataki online's engine process: `kataki serve --hosted` (minds spec §4, §8.4; track B4, B5).

One process, many users, a library each. Who is asking comes only from the gateway's signed
headers; every model call is asked of the gateway first and billed to it after. Each open library
is the desktop's own app (`create_app`) with an `OnlineHost` bound to that one user, so nothing
one user does can be gated or billed as another's.
"""

import asyncio
import contextlib
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import shutil
import sqlite3
import time
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import keyring
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from kataki import db, features, roles, usage
from kataki.host import OnlineHost
from kataki.llm import LLM, DailyCap, Endpoint
from kataki.server import create_app

log = logging.getLogger(__name__)

# a library id names a folder: nothing else gets in. Lowercase only (a case-blind disk would give
# `Alice` and `alice` one folder), and never a Windows device name
USER = re.compile(r"(?!(?:con|prn|aux|nul|com[1-9]|lpt[1-9])$)[a-z0-9_-]{1,64}")
WINDOW = 60  # seconds a signature is good for, either way (clock skew, and no replays after)
# The gateway's own word to the engine, never a browser's (the gateway does not proxy `/_gateway/`):
# POST it, signed as a user, and that user's library is gone (an account deleted, online spec G5)
FORGET = "/_gateway/forget"


def sign(secret: bytes, user: str, channel: str, at: int, method: str, target: str) -> str:
    """The gateway's signature on one request (§8.4). `target` is its path and query as sent,
    `/stories/1/turn?` (the `?` always there), so a captured signature is good for that request
    line only.

    ponytail: no body hash and no nonce cache: a request can be replayed as-is within the window.
    Both are owed before `--bind` is anything but loopback."""
    said = f"{user}\n{channel}\n{at}\n{method}\n{target}"
    return hmac.new(secret, said.encode(), hashlib.sha256).hexdigest()


def who(
    secret: bytes, headers: Mapping[str, str], now: float, method: str, target: str
) -> tuple[str, str] | None:
    """(user, channel) when the headers are the gateway's, signed within the window for this
    method and target; else None."""
    user = headers.get("x-kataki-user", "")
    channel = headers.get("x-kataki-channel", "")
    if not re.fullmatch(r"[0-9]{1,12}", stamp := headers.get("x-kataki-time", "")):
        return None  # digits only: exactly what was signed, never " 12", "+12" or "1_2"
    at = int(stamp)
    said = headers.get("x-kataki-sig", "")
    if not USER.fullmatch(user) or abs(now - at) > WINDOW:
        return None
    if not hmac.compare_digest(
        said.encode(), sign(secret, user, channel, at, method, target).encode()
    ):
        return None
    return user, channel


class Gateway:
    """The engine's client to the service (§8.4): may this call run, and bill the ones that did.

    ponytail: synchronous (the host is asked synchronously), so a slow gateway blocks the event
    loop for up to the timeout; an async client if that ever shows.
    """

    TTL = 10.0  # seconds an `allow` answer is kept, per user

    def __init__(
        self,
        url: str,
        key: str,
        transport: httpx2.BaseTransport | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._http = httpx2.Client(
            base_url=url,
            headers={"Authorization": f"Bearer {key}"},
            timeout=2.0,
            transport=transport,
        )
        self._clock = clock
        self._said: dict[str, tuple[float, bool]] = {}

    def allow(self, user: str, estimate: float) -> bool:
        """Can this user's balance cover a call of about `estimate` dollars? Raises when the
        gateway cannot say (the online host then refuses: it fails closed)."""
        now = self._clock()
        if (said := self._said.get(user)) and now - said[0] < self.TTL:
            return said[1]
        r = self._http.get("/allow", params={"user": user, "estimate": estimate})
        r.raise_for_status()
        ok = bool(r.json()["ok"])
        self._said[user] = (now, ok)
        return ok

    def meter(self, user: str, row: dict) -> None:
        """Bill one call (idempotent on `usage_id`), tried twice. Raises when it could not: the
        row stays `metered=0` for the outbox."""
        for attempt in range(2):
            try:
                self._http.post("/usage", json={"user": user, **row}).raise_for_status()
                return
            except httpx2.HTTPError:
                if attempt:
                    raise

    def resend(self, user: str, conn: sqlite3.Connection) -> int:
        """The outbox: rows the meter could not take, sent again oldest first. Returns how many
        went. A row the gateway refuses as malformed (400, 422) is set aside as `metered=2` and the
        rest still go; 409 means the gateway already has it; any other failure stops it and
        raises, so a wrong URL or a rotated key never parks the outbox."""
        sent = 0
        for r in conn.execute(
            "SELECT * FROM usage_log WHERE metered=0 AND usage_id IS NOT NULL ORDER BY id"
        ).fetchall():
            row = {
                k: r[k]
                for k in (
                    "usage_id",
                    "story_id",
                    "role",
                    "model",
                    "prompt_tokens",
                    "cached_tokens",
                    "completion_tokens",
                    "cost",
                    "at",  # a row resent after midnight is still billed to the day it was used
                )
            }
            try:
                self.meter(user, {**row, "estimated": bool(r["estimated"])})
            except httpx2.HTTPStatusError as e:
                code = e.response.status_code
                if code not in (400, 409, 422):
                    raise
                if code == 409:  # already billed under this usage_id
                    with conn:
                        conn.execute("UPDATE usage_log SET metered=1 WHERE id=?", (r["id"],))
                    sent += 1
                    continue
                log.warning("gateway refused usage %s (%s): set aside", r["usage_id"], code)
                with conn:
                    conn.execute("UPDATE usage_log SET metered=2 WHERE id=?", (r["id"],))
                continue
            with conn:
                conn.execute("UPDATE usage_log SET metered=1 WHERE id=?", (r["id"],))
            sent += 1
        return sent


def secret(name: str) -> str | None:
    """The gateway's shared secrets live in the env or the OS keychain, never in a library:
    `KATAKI_GATEWAY_SECRET` / `KATAKI_GATEWAY_KEY`, else keychain `kataki-gateway`/`secret`|`key`."""
    if said := os.environ.get(f"KATAKI_GATEWAY_{name.upper()}"):
        return said
    with contextlib.suppress(keyring.errors.KeyringError):
        return keyring.get_password("kataki-gateway", name)
    return None


def _catalogue(path: Path) -> tuple[list, list, dict]:
    """The service's providers, model roles and prices, from a library file built for it.

    Read as a file that never changes (`immutable`), so it can sit on a read-only mount and no
    lock or `-shm` is ever made beside it. Changes still in a `-wal` would be missed, so a
    catalogue with one is refused: open it once in Kataki and close it, and they are folded in."""
    wal = Path(f"{path}-wal")
    if wal.exists() and wal.stat().st_size:
        raise ValueError(f"{wal} holds changes not yet in {path}: open and close it once first.")
    c = sqlite3.connect(f"file:{Path(path).resolve().as_posix()}?mode=ro&immutable=1", uri=True)
    try:
        providers = c.execute("SELECT id, name, base_url, extra FROM providers").fetchall()
        models = c.execute(
            "SELECT role, provider_id, model, kind, detected_kind, params FROM model_roles"
        ).fetchall()
        prices = c.execute("SELECT value FROM settings WHERE key='prices'").fetchone()
    finally:
        c.close()
    return providers, models, json.loads(prices[0]) if prices else {}


@dataclass
class Library:
    """One user's open library: its own connection, model client, host and app."""

    user: str
    conn: sqlite3.Connection
    llm: LLM
    token: str
    host: OnlineHost | None = None
    app: FastAPI | None = None
    busy: int = 0  # requests in flight: never closed under them
    last: float = field(default_factory=time.monotonic)


class Hosted:
    """The ASGI app of `kataki serve --hosted`: signed request in, the user's library out."""

    def __init__(
        self,
        root: Path,
        signing: bytes,
        gateway: Gateway,
        catalogue: Path,
        *,
        get_key: Callable[[str], str | None] = roles.get_key,  # the service's keys
        max_open: int = 64,
        idle: float = 900.0,  # seconds unused before a library closes
        daily_cap: float = 5.0,  # dollars a user may spend a day (UTC)
        max_calls: int = 4,  # a user's model calls in flight
        worker_delay: float = 3.0,
        transport: httpx2.AsyncBaseTransport | None = None,  # tests script the providers here
    ):
        self.root, self.signing, self.gateway = Path(root), signing, gateway
        self.providers, self.models, self.prices = _catalogue(catalogue)
        self.get_key, self.max_open, self.idle = get_key, max_open, idle
        self.daily_cap, self.max_calls, self.worker_delay = daily_cap, max_calls, worker_delay
        self.transport = transport
        self._open: OrderedDict[str, Library] = OrderedDict()
        self._sweeper: asyncio.Task | None = None

    def opened(self, user: str) -> Library | None:
        return self._open.get(user)

    def open(self, user: str) -> Library:
        """The user's library, opened now if it is not already. Synchronous, so two first
        requests at once cannot open it twice."""
        if lib := self._open.get(user):
            self._open.move_to_end(user)
            return lib
        conn = db.connect(self.root / user / "library.db")
        with conn:  # the service owns routing: its catalogue, whatever the library held
            conn.execute("DELETE FROM model_roles")
            conn.execute("DELETE FROM providers")
            conn.executemany("INSERT INTO providers VALUES(?, ?, ?, ?)", self.providers)
            conn.executemany(
                "INSERT INTO model_roles(role, provider_id, model, kind, detected_kind, params)"
                " VALUES(?, ?, ?, ?, ?, ?)",
                self.models,
            )
        lib = Library(user, conn, LLM(self.transport, self.max_calls), secrets.token_urlsafe(32))
        lib.host = OnlineHost(
            get_key=self.get_key,
            meter=lambda row: self.gateway.meter(user, row),
            allow=self._allow(user, conn),
            channel=lambda: features.CURRENT.get() or "stable",  # this request's (below)
            prices=lambda: self.prices,
        )
        lib.app = create_app(
            conn, lib.token, lib.llm, worker_delay=self.worker_delay, host=lib.host
        )
        self._open[user] = lib
        try:
            self.gateway.resend(user, conn)  # what the last session could not bill
        except httpx2.HTTPError as e:  # the sweep tries again
            log.warning("outbox for %s not sent: %s", user, type(e).__name__)
        return lib

    async def _evict(self) -> None:
        """Past the limit, close the least recently used libraries with nothing in flight."""
        for user in list(self._open):
            if len(self._open) <= self.max_open:
                return
            await self.close(user)  # skips one a request reached while an earlier close awaited

    def _allow(self, user: str, conn: sqlite3.Connection):
        def allow(ep: Endpoint, estimate: float) -> bool:
            # today's spend as the ledger bills it: whole micro-dollars from each row's tokens
            rows = conn.execute("SELECT * FROM usage_log WHERE at >= date('now')").fetchall()
            today = sum(usage.micros(self.prices, dict(r)) or 0 for r in rows)
            if today + round(estimate * 1e6) > round(self.daily_cap * 1e6):
                raise DailyCap("You have reached today's spending limit. It resets at 00:00 UTC.")
            return self.gateway.allow(user, estimate)

        return allow

    async def close(self, user: str, *, force: bool = False) -> None:
        """Close a library: its background job is cancelled (the read it was doing is discarded
        at the next open, and read again), then its model client and its file. One with a
        request in flight stays open unless `force` (shutdown): checked and removed in one
        synchronous step, so no request can arrive in between."""
        lib = self._open.get(user)
        if lib is None or (lib.busy and not force):
            return
        del self._open[user]
        worker = lib.app.state.worker
        worker.cancel()
        try:
            await worker.idle()
        except Exception as e:  # a job that had failed must not keep the library open
            log.warning("background job for %s ended badly: %s", user, e)
        await lib.llm.aclose()
        lib.conn.close()

    async def forget(self, user: str) -> int:
        """Delete a user's library for good: its file, pictures and backups. 200 when it is gone
        (or was never there); 409 while it holds usage the gateway has not taken, or a request
        is in flight: the gateway asks again later, and nothing is lost unbilled."""
        folder = self.root / user
        if not folder.exists():
            return 200
        lib = self.open(user)
        with contextlib.suppress(httpx2.HTTPError):  # what is still owed is billed first
            self.gateway.resend(user, lib.conn)
        unbilled = lib.conn.execute(
            "SELECT count(*) FROM usage_log WHERE metered=0 AND usage_id IS NOT NULL"
        ).fetchone()[0]
        if unbilled or lib.busy:
            return 409
        await self.close(user, force=True)
        shutil.rmtree(folder)
        return 200

    async def sweep(self) -> None:
        """Close what has been idle too long; send the outbox of what stays open, until the
        gateway fails once (then the rest wait for the next sweep, not a timeout each)."""
        now, down = time.monotonic(), False
        for user, lib in list(self._open.items()):
            if self._open.get(user) is not lib:  # closed (or reopened) while we awaited
                continue
            if not lib.busy and now - lib.last >= self.idle:
                await self.close(user)
            elif not down:
                try:
                    self.gateway.resend(user, lib.conn)
                except httpx2.HTTPError as e:
                    log.warning("outbox for %s not sent: %s", user, type(e).__name__)
                    down = True

    async def _sweeping(self) -> None:
        while True:
            await asyncio.sleep(max(self.idle / 4, 1.0))
            try:
                await self.sweep()
            except Exception as e:  # the sweeper outlives any one bad library
                log.warning("sweep failed: %s", e)

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "lifespan":
            return await self._lifespan(receive, send)
        if scope["type"] != "http":
            return
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        path = scope.get("raw_path") or scope["path"].encode()
        target = f"{path.decode('latin-1')}?{scope['query_string'].decode('latin-1')}"
        if (found := who(self.signing, headers, time.time(), scope["method"], target)) is None:
            refused = JSONResponse({"detail": "missing or invalid gateway signature"}, 401)
            return await refused(scope, receive, send)
        user, channel = found
        if scope["path"] == FORGET:
            status = await self.forget(user) if scope["method"] == "POST" else 405
            return await JSONResponse({"forgotten": status == 200}, status)(scope, receive, send)
        lib = self.open(user)
        features.CURRENT.set(channel)  # this request's task only: never another request's
        # the library's own app still wants its bearer token: the signature stood in for it
        inner = [(k, v) for k, v in scope["headers"] if k.lower() != b"authorization"]
        inner.append((b"authorization", f"Bearer {lib.token}".encode()))
        lib.busy += 1
        try:
            await self._evict()
            await lib.app({**scope, "headers": inner}, receive, send)
        finally:
            lib.busy -= 1
            lib.last = time.monotonic()

    async def _lifespan(self, receive, send) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                self._sweeper = asyncio.create_task(self._sweeping())
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                if self._sweeper:
                    self._sweeper.cancel()
                for user in list(self._open):
                    await self.close(user, force=True)
                await send({"type": "lifespan.shutdown.complete"})
                return
