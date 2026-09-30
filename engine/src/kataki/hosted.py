"""Kataki online's engine process: `kataki serve --hosted` (minds spec §4, §8.4; track B4, B5).

One process, many users, a library each. Who is asking comes only from the gateway's signed
headers; every model call is asked of the gateway first and billed to it after. Each open library
is the desktop's own app (`create_app`) with an `OnlineHost` bound to that one user, so nothing
one user does can be gated or billed as another's.
"""

import hashlib
import hmac
import re
import sqlite3
import time
from collections.abc import Callable, Mapping

import httpx2

USER = re.compile(r"[A-Za-z0-9_-]{1,64}")  # a library id names a folder: nothing else gets in
WINDOW = 60  # seconds a signature is good for, either way (clock skew, and no replays after)


def sign(secret: bytes, user: str, channel: str, at: int) -> str:
    """The gateway's signature on one request (§8.4)."""
    return hmac.new(secret, f"{user}\n{channel}\n{at}".encode(), hashlib.sha256).hexdigest()


def who(secret: bytes, headers: Mapping[str, str], now: float) -> tuple[str, str] | None:
    """(user, channel) when the headers are the gateway's, signed within the window; else None."""
    user = headers.get("x-kataki-user", "")
    channel = headers.get("x-kataki-channel", "")
    try:
        at = int(headers.get("x-kataki-time", ""))
    except ValueError:
        return None
    said = headers.get("x-kataki-sig", "")
    if not USER.fullmatch(user) or abs(now - at) > WINDOW:
        return None
    if not hmac.compare_digest(said.encode(), sign(secret, user, channel, at).encode()):
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
        """The outbox: rows the meter could not take, sent again oldest first, until one fails.
        Returns how many went."""
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
                )
            }
            try:
                self.meter(user, {**row, "estimated": bool(r["estimated"])})
            except httpx2.HTTPError:
                break
            with conn:
                conn.execute("UPDATE usage_log SET metered=1 WHERE id=?", (r["id"],))
            sent += 1
        return sent
