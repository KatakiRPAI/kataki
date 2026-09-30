"""Model roles. Every engine task routes to a role; an unset role inherits along CHAIN.

Provider, model and kind come from the first role in the chain that names a model. Params
are layered parent-first, so an inheriting role can change how the *same* model is driven
(one hybrid model: thinking off for `rp`, on for `reasoning`).
"""

import contextlib
import json
import os
import re
import sqlite3
from collections.abc import Callable
from dataclasses import replace

import keyring
import keyring.errors

from kataki.llm import LLM, Endpoint

ROLES = ("rp", "narrator", "utility", "reasoning", "embed", "image", "music", "voice")
CHAIN = {"narrator": "rp", "utility": "rp", "reasoning": "utility"}  # the rest never inherit
_EMPTY = {"provider_id": None, "model": None, "kind": "auto", "detected_kind": None, "params": {}}


def get_key(provider_name: str) -> str | None:
    """API keys never live in library.db (people share it): env var first, then the OS keychain."""
    env_name = "KATAKI_KEY_" + re.sub(r"\W", "_", provider_name).upper()
    if key := os.environ.get(env_name):
        return key
    try:
        return keyring.get_password("kataki", provider_name)
    except keyring.errors.KeyringError:  # headless Linux without a Secret Service
        return None


def set_key(provider_name: str, key: str) -> None:
    keyring.set_password("kataki", provider_name, key)


def delete_key(provider_name: str) -> None:
    with contextlib.suppress(keyring.errors.KeyringError):  # includes "there was no key"
        keyring.delete_password("kataki", provider_name)


def _own(conn: sqlite3.Connection, role: str, story_id: int | None) -> dict:
    """The role's own row, with the story's override (if any) laid over it."""
    row = conn.execute("SELECT * FROM model_roles WHERE role=?", (role,)).fetchone()
    own = {**_EMPTY, **({**row, "params": json.loads(row["params"])} if row else {})}
    if story_id is not None:
        raw = conn.execute("SELECT overrides FROM stories WHERE id=?", (story_id,)).fetchone()
        own.update(json.loads(raw["overrides"]).get("roles", {}).get(role, {}) if raw else {})
    return own


def _trace(conn: sqlite3.Connection, role: str, story_id: int | None):
    """Walk the chain to the role that names a model -> (source role, source row, kind, params)."""
    walked = []
    at: str | None = role
    while at:
        own = _own(conn, at, story_id)
        walked.append(own)
        if own["provider_id"] and own["model"]:
            params: dict = {}
            for layer in reversed(walked):  # parent first, so the asking role wins
                params.update(layer["params"])
            override = next((w["kind"] for w in walked if w["kind"] != "auto"), None)
            return at, own, override or own["detected_kind"], params
        at = CHAIN.get(at)
    return None


def resolve(
    conn: sqlite3.Connection,
    role: str,
    story_id: int | None = None,
    get_key: Callable[[str], str | None] = get_key,
) -> Endpoint | None:
    if not (found := _trace(conn, role, story_id)):
        return None
    _, source, kind, params = found
    provider = conn.execute(
        "SELECT * FROM providers WHERE id=?", (source["provider_id"],)
    ).fetchone()
    return Endpoint(
        base_url=provider["base_url"],
        model=source["model"],
        api_key=get_key(provider["name"]),
        reasoning=kind == "reasoning",
        params=params,
        role=role,
        story_id=story_id,
    )


def routing(conn: sqlite3.Connection, story_id: int | None = None) -> list[dict]:
    """For the Models page: each role's own settings, and where its model really comes from."""
    table = []
    for role in ROLES:
        found = _trace(conn, role, story_id)
        source_role, source, kind, _ = found or (None, _EMPTY, None, None)
        table.append(
            {
                "role": role,
                **_own(conn, role, story_id),
                "inherited_from": source_role if source_role != role else None,
                "effective_provider_id": source["provider_id"],
                "effective_model": source["model"],
                "effective_kind": kind,
            }
        )
    return table


async def probe_kind(llm: LLM, ep: Endpoint) -> str:
    """Ask for one word and watch the stream: thoughts before text mean a reasoning model."""
    body = {**ep.params.get("body", {}), "max_tokens": 256}
    natural = replace(ep, params={**ep.params, "thinking": "default", "body": body})
    stream = llm.chat_stream(
        natural, [{"role": "user", "content": "Reply with the single word: ok"}]
    )
    try:
        async for kind, text in stream:
            if kind == "thought":
                return "reasoning"
            if kind == "token" and text.strip():
                return "standard"
    finally:
        await stream.aclose()  # stop generating: we have our answer
    return "standard"
