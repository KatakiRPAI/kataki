"""Where the engine runs (docs/specs/2026-09-29-minds.md §4, §8.4; track B1).

One engine serves the desktop app and Kataki online. Everything that differs between them is one
of the host's answers: where API keys come from, where a call's usage goes, whether a call may
run (credit), which channel this user is on, the price table, and whether this machine's own
routes (providers, backups on disk) exist. The rest of the engine asks the host, never the
product.
"""

import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from kataki import features, roles, usage
from kataki.llm import Endpoint


@dataclass(frozen=True)
class Host:
    name: str = "desktop"
    get_key: Callable[[str], str | None] = roles.get_key
    meter: Callable[[dict], None] | None = None  # after the usage_log row: bill it
    allow: Callable[[Endpoint, float | None], bool] | None = None  # None: never refuses
    channel: Callable[[], str] = features.from_env
    prices: Callable[[], dict] | None = None  # None: the library's own `prices` setting
    local_routes: bool = True

    def on_usage(self, conn: sqlite3.Connection, ep: Endpoint, used: dict) -> None:
        row = usage.record(conn, ep, used)
        if self.meter:
            self.meter(row)


class LocalHost(Host):
    """The desktop: keys from the env or the OS keychain, usage only in usage_log, never
    refuses a call, the build's channel, local routes on. Today's engine exactly."""


class OnlineHost(Host):
    """Kataki online: every answer comes from the service (the gateway client, track B4)."""

    def __init__(
        self,
        *,
        get_key: Callable[[str], str | None],
        meter: Callable[[dict], None],
        allow: Callable[[Endpoint, float | None], bool],
        channel: Callable[[], str],
        prices: Callable[[], dict],
    ):
        def closed(ep: Endpoint, estimate: float | None) -> bool:
            try:  # a balance that cannot be checked is not a balance: refuse
                return bool(allow(ep, estimate))
            except Exception as e:
                logging.getLogger(__name__).warning("credit check failed, refused: %s", e)
                return False

        super().__init__("online", get_key, meter, closed, channel, prices, False)
