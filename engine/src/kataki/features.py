"""Which features are on (docs/specs/2026-09-29-minds.md §5).

Every feature has a stage; every build (desktop) or account (online) has a channel. A feature
is on when its stage is at or past the channel's: alpha gets everything, beta gets beta and
stable, stable gets stable. The user can switch any feature off, and an earlier-stage one on
unless they are on stable. One registry serves the desktop app and Kataki online.
"""

import os
import sqlite3

from kataki import knobs

STAGES = ("alpha", "beta", "stable")
FEATURES = {
    "mind.affect": "alpha",  # slice 1: moods that last
    "mind.bonds": "alpha",  # slice 2: grudges that hold, pushback, the side call
}


def channel() -> str:
    """The build's channel. Electron sets KATAKI_CHANNEL from the app version (-alpha.N, -beta.N,
    else stable); a source checkout or a headless engine without it is alpha."""
    value = os.environ.get("KATAKI_CHANNEL", "alpha")
    return value if value in STAGES else "stable"


def enabled(conn: sqlite3.Connection, name: str, chan: str | None = None) -> bool:
    chan = chan or channel()
    choice = knobs.setting(conn, f"features.{name}", None)
    if choice is False:
        return False
    if choice is True and chan != "stable":
        return True
    return STAGES.index(FEATURES[name]) >= STAGES.index(chan)


def listing(conn: sqlite3.Connection, chan: str | None = None) -> dict:
    chan = chan or channel()
    return {
        "channel": chan,
        "features": {
            name: {"stage": stage, "on": enabled(conn, name, chan)}
            for name, stage in FEATURES.items()
        },
    }
