"""HTTP adapter over the engine: the desktop app's API.

Every route needs the per-launch bearer token. Routes are async on purpose: the engine
shares one SQLite connection, and keeping all work on the event loop means it is never
used from two threads at once (ponytail: fine for one local user; a connection per request
if this ever serves many).
"""

import asyncio
import contextlib
import hmac
import json
import sqlite3
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from kataki import (
    __version__,
    chat,
    clock,
    extract,
    library,
    media,
    retrieve,
    roles,
    signals,
    turns,
)
from kataki.llm import LLM, LLMError

LOCAL_SERVERS = {  # where the first-run wizard looks for a model already running here
    "llama.cpp": "http://127.0.0.1:8080/v1",
    "Ollama": "http://127.0.0.1:11434/v1",
    "LM Studio": "http://127.0.0.1:1234/v1",
    "KoboldCpp": "http://127.0.0.1:5001/v1",
    "vLLM": "http://127.0.0.1:8000/v1",
    "TabbyAPI / text-generation-webui": "http://127.0.0.1:5000/v1",
}


class ProviderIn(BaseModel):
    name: str
    base_url: str
    api_key: str | None = None  # write-only: kept in the OS keychain, never returned


class ProviderPatch(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None


class RoleIn(BaseModel):
    provider_id: int | None = None
    model: str | None = None
    kind: Literal["auto", "reasoning", "standard"] = "auto"
    params: dict = {}


class ItemIn(BaseModel):
    kind: Literal["character", "place", "scenario"]
    name: str
    description: str = ""
    private: str = ""
    data: dict = {}
    tags: list[str] = []


class ItemPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    private: str | None = None
    data: dict | None = None
    tags: list[str] | None = None


class StoryIn(BaseModel):
    title: str
    character_ids: list[int] = []
    place_id: int | None = None
    persona_id: int | None = None
    scenario_id: int | None = None
    epoch_offset_min: int = Field(480, ge=0)  # the clock at the start: 480 = Day 1, 08:00


class StoryPatch(BaseModel):
    title: str | None = None
    minutes_per_turn: int | None = None
    pinned: bool | None = None
    roles: dict | None = None  # per-story role overrides, same shape as PUT /roles/{role}


class TurnIn(BaseModel):
    text: str | None = None
    speaker: int | Literal["narrator"] | None = None
    # who the user's line is for: None = all present, [] = a thought
    audience: list[int] | None = None
    skip: str | None = None  # time that passes first, in words: "the next morning"


class LineIn(BaseModel):
    text: str | None = None
    audience: list[int] | None = None
    skip: str | None = None


class SwipeIn(BaseModel):
    message_id: int
    step: Literal[-1, 1]


class MessagePatch(BaseModel):
    text: str | None = None
    hidden: bool | None = None
    skip_minutes: int | None = None


class PresenceIn(BaseModel):
    entity_id: int
    present: bool


class SceneIn(BaseModel):
    present: list[int]
    place_id: int | None = None  # a place already in the story
    library_place_id: int | None = None  # or one from the library, brought in
    title: str | None = None
    skip: str | None = None  # time that passes before it, in words: "the next morning"


class JoinIn(BaseModel):
    library_id: int


class RereadIn(BaseModel):
    role: Literal["utility", "reasoning"] = "reasoning"


class EntityPatch(BaseModel):
    name: str | None = None
    summary: str | None = None
    description: str | None = None
    private: str | None = None
    hidden: bool | None = None


class MergeIn(BaseModel):
    keep: int
    drop: int


class MemoryIn(BaseModel):
    detail: str
    gist: str | None = None
    importance: int = 5
    kind: Literal["event", "fact"] = "fact"
    knower_ids: list[int] = []
    entity_ids: list[int] = []
    common: bool = False
    pinned: bool = False


class MemoryPatch(BaseModel):
    detail: str | None = None
    gist: str | None = None
    importance: int | None = None
    hidden: bool | None = None
    pinned: bool | None = None
    common: bool | None = None


def _row(conn: sqlite3.Connection, sql: str, args=()) -> dict:
    row = conn.execute(sql, args).fetchone()
    if row is None:
        raise HTTPException(404, "not found")
    return dict(row)


def _patch(conn: sqlite3.Connection, table: str, row_id: int, fields: dict) -> None:
    """UPDATE the given columns. Column names come from pydantic models, never from users."""
    if fields:
        sets = ", ".join(f"{name}=?" for name in fields)
        with conn:
            conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", (*fields.values(), row_id))


def create_app(
    conn: sqlite3.Connection,
    token: str,
    llm: LLM | None = None,
    worker_delay: float = 3.0,
    get_key=roles.get_key,
) -> FastAPI:
    llm = llm or LLM()
    worker = extract.Worker(conn, llm, get_key, delay=worker_delay)
    extract.recover(conn)

    expected = f"Bearer {token}".encode()

    def require_token(request: Request, authorization: str = Header("")):
        if hmac.compare_digest(authorization.encode(), expected):
            return
        # An <img> can't send a header, so media alone also takes the token in the query.
        query = request.query_params.get("token")
        if request.url.path.startswith("/media/") and query is not None:
            if hmac.compare_digest(f"Bearer {query}".encode(), expected):
                return
        raise HTTPException(401, "missing or invalid token")

    app = FastAPI(
        title="Kataki RPAI engine", version=__version__, dependencies=[Depends(require_token)]
    )
    # Any origin is fine: auth is a bearer token, not a cookie, so a foreign page has
    # nothing to ride on.
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    def story_row(story_id: int) -> dict:
        return _row(conn, "SELECT * FROM stories WHERE id=?", (story_id,))

    def check_audience(story_id: int, audience: list[int] | None) -> None:
        """A whisper can only be for people in this story."""
        if audience:
            marks = ",".join("?" * len(audience))
            found = conn.execute(
                f"SELECT count(*) FROM entities WHERE story_id=? AND id IN ({marks})",
                (story_id, *audience),
            ).fetchone()[0]
            if found != len(set(audience)):
                raise HTTPException(422, "a whisper can only be for people in this story")

    def messages(story_id: int) -> list[dict]:
        story = story_row(story_id)
        names = dict(
            conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
        )
        out = []
        # ponytail: one sibling query per message; batch it if very long stories feel slow
        for m in chat.active_path(conn, story_id):
            gen = json.loads(m["gen"]) if m["gen"] else {}
            out.append(
                {
                    "id": m["id"],
                    "parent_id": m["parent_id"],
                    "role": m["role"],
                    "speaker_id": m["speaker_id"],
                    "speaker": names.get(m["speaker_id"]),
                    "text": m["text"],
                    "hidden": bool(m["hidden"]),
                    "edited": m["edited_at"] is not None,
                    "skip_minutes": m["skip_minutes"],
                    "clock": clock.label(m["story_time"], story["epoch_offset_min"]),
                    "scene_id": m["scene_id"],
                    "swipe": chat.sibling_position(conn, m["id"]),
                    "reasoning": gen.get("reasoning"),
                    "finish": gen.get("finish"),
                    "model": gen.get("model"),
                    "audience": chat.audience_of(m),
                    "think_ms": gen.get("think_ms"),
                }
            )
        return out

    def stream(story_id: int, events) -> StreamingResponse:
        """Server-sent events. The turn runs in its own task: if the client goes away, the
        task is cancelled, generation stops, and whatever was written is kept."""

        async def pump(queue: asyncio.Queue):
            try:
                async for event in events:
                    await queue.put(event)
            except Exception as e:  # a bug must still end the stream for the client
                await queue.put(("error", {"message": f"{type(e).__name__}: {e}"}))
            finally:
                queue.put_nowait(None)
                worker.poke(story_id)  # the story may now have lines worth remembering

        async def body():
            queue: asyncio.Queue = asyncio.Queue()
            task = asyncio.create_task(pump(queue))
            try:
                while (event := await queue.get()) is not None:
                    yield f"event: {event[0]}\ndata: {json.dumps(event[1])}\n\n"
            finally:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        return StreamingResponse(
            body(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )

    def make_way(story_id: int) -> None:
        """A reply is about to be generated: the background reader steps aside if it would
        compete for the same model server."""
        if ep := roles.resolve(conn, "rp", story_id, get_key):
            worker.turn_started(story_id, ep.base_url)

    # --- health and settings ---------------------------------------------------------------

    @app.get("/health")
    async def health():
        schema = conn.execute("PRAGMA user_version").fetchone()[0]
        return {"status": "ok", "version": __version__, "schema": schema}

    @app.get("/settings")
    async def get_settings():
        return {r["key"]: json.loads(r["value"]) for r in conn.execute("SELECT * FROM settings")}

    @app.put("/settings")
    async def put_settings(values: dict):
        with conn:
            for key, value in values.items():
                conn.execute(
                    "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)",
                    (key, json.dumps(value)),
                )
        return await get_settings()

    # --- providers and model roles ---------------------------------------------------------

    def provider_out(row) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "base_url": row["base_url"],
            "has_key": bool(get_key(row["name"])),
        }

    @app.get("/providers")
    async def list_providers():
        return [provider_out(r) for r in conn.execute("SELECT * FROM providers ORDER BY name")]

    @app.post("/providers", status_code=201)
    async def add_provider(p: ProviderIn):
        try:
            with conn:
                pid = conn.execute(
                    "INSERT INTO providers(name, base_url) VALUES(?, ?)",
                    (p.name, p.base_url.rstrip("/")),
                ).lastrowid
        except sqlite3.IntegrityError as e:
            raise HTTPException(409, f"a provider named {p.name!r} already exists") from e
        if p.api_key:
            roles.set_key(p.name, p.api_key)
        return provider_out(_row(conn, "SELECT * FROM providers WHERE id=?", (pid,)))

    @app.patch("/providers/{pid}")
    async def edit_provider(pid: int, p: ProviderPatch):
        old = _row(conn, "SELECT * FROM providers WHERE id=?", (pid,))
        fields = p.model_dump(exclude_unset=True, exclude={"api_key"})
        if "base_url" in fields:
            fields["base_url"] = fields["base_url"].rstrip("/")
        _patch(conn, "providers", pid, fields)
        name = fields.get("name", old["name"])
        if name != old["name"] and (key := get_key(old["name"])):
            roles.set_key(name, key)  # the key follows the rename
            roles.delete_key(old["name"])
        if p.api_key:
            roles.set_key(name, p.api_key)
        elif p.api_key == "":  # an empty key clears it
            roles.delete_key(name)
        return provider_out(_row(conn, "SELECT * FROM providers WHERE id=?", (pid,)))

    @app.delete("/providers/{pid}", status_code=204)
    async def remove_provider(pid: int):
        old = _row(conn, "SELECT * FROM providers WHERE id=?", (pid,))
        with conn:
            conn.execute(
                "UPDATE model_roles SET provider_id=NULL, model=NULL WHERE provider_id=?", (pid,)
            )
            conn.execute("DELETE FROM providers WHERE id=?", (pid,))
        roles.delete_key(old["name"])

    @app.get("/providers/detect")
    async def detect_providers():
        """Model servers already running on this machine, for the first-run wizard."""

        async def probe(name, url):
            with contextlib.suppress(LLMError, asyncio.TimeoutError):
                models = await asyncio.wait_for(llm.list_models(url, None), timeout=1.5)
                return {"name": name, "base_url": url, "models": models}

        found = await asyncio.gather(*(probe(n, u) for n, u in LOCAL_SERVERS.items()))
        return [f for f in found if f]

    @app.get("/providers/{pid}/models")
    async def provider_models(pid: int):
        p = _row(conn, "SELECT * FROM providers WHERE id=?", (pid,))
        try:
            return {"models": await llm.list_models(p["base_url"], get_key(p["name"]))}
        except LLMError as e:
            raise HTTPException(502, str(e)) from e

    @app.get("/roles")
    async def list_roles(story_id: int | None = None):
        return roles.routing(conn, story_id)

    @app.put("/roles/{role}")
    async def set_role(role: Literal[roles.ROLES], r: RoleIn):  # type: ignore[valid-type]
        with conn:
            conn.execute(
                "INSERT INTO model_roles(role, provider_id, model, kind, params)"
                " VALUES(?, ?, ?, ?, ?) ON CONFLICT(role) DO UPDATE SET"
                " provider_id=excluded.provider_id, model=excluded.model, kind=excluded.kind,"
                " params=excluded.params,"  # a different model forgets the old probe result
                " detected_kind=CASE WHEN model IS excluded.model THEN detected_kind END",
                (role, r.provider_id, r.model, r.kind, json.dumps(r.params)),
            )
        return next(row for row in roles.routing(conn) if row["role"] == role)

    @app.post("/roles/{role}/probe")
    async def probe_role(role: Literal[roles.ROLES]):  # type: ignore[valid-type]
        """Ask the model one word and watch whether it thinks first."""
        if (ep := roles.resolve(conn, role, None, get_key)) is None:
            raise HTTPException(409, f"no model is set for {role!r}")
        try:
            kind = await roles.probe_kind(llm, ep)
        except LLMError as e:
            raise HTTPException(502, str(e)) from e
        source = next(r for r in roles.routing(conn) if r["role"] == role)
        with conn:
            conn.execute(
                "UPDATE model_roles SET detected_kind=? WHERE role=?",
                (kind, source["inherited_from"] or role),
            )
        return {"role": role, "detected_kind": kind}

    # --- library ---------------------------------------------------------------------------

    @app.get("/library")
    async def list_library(kind: str | None = None, tag: str | None = None):
        return library.list_items(conn, kind, tag)

    @app.post("/library", status_code=201)
    async def add_item(item: ItemIn):
        item_id = library.create_item(conn, **item.model_dump())
        return library.get_item(conn, item_id)

    @app.get("/library/{item_id}")
    async def get_item(item_id: int):
        if (item := library.get_item(conn, item_id)) is None:
            raise HTTPException(404, "not found")
        return item

    @app.patch("/library/{item_id}")
    async def edit_item(item_id: int, item: ItemPatch):
        await get_item(item_id)
        library.update_item(conn, item_id, **item.model_dump(exclude_unset=True))
        return library.get_item(conn, item_id)

    @app.delete("/library/{item_id}", status_code=204)
    async def remove_item(item_id: int):
        library.delete_item(conn, item_id)

    # --- media: portraits and place images ------------------------------------------------

    @app.post("/media", status_code=201)
    async def add_media(request: Request):
        data = await request.body()
        if len(data) > media.MAX_BYTES:
            raise HTTPException(413, "Images can be at most 10 MB.")
        if (ext := media.sniff(data)) is None:
            raise HTTPException(415, "Only PNG, JPEG, GIF or WebP images.")
        return {"name": media.save(conn, data, ext), "bytes": len(data)}

    @app.get("/media/{name}")
    async def get_media(name: str):
        if (path := media.find(conn, name)) is None:
            raise HTTPException(404, "not found")
        return FileResponse(
            path,
            media_type=media.TYPES[path.suffix[1:]],
            headers={
                "Cache-Control": "private, max-age=31536000, immutable",
                "X-Content-Type-Options": "nosniff",
            },
        )

    # --- stories ---------------------------------------------------------------------------

    def ref(entity_id: int | None) -> dict | None:
        """An entity as the Sky shows it: enough to find its portrait in the library."""
        row = conn.execute(
            "SELECT id, name, lib_item_id FROM entities WHERE id IS ?", (entity_id,)
        ).fetchone()
        return dict(row) if row else None

    def new_events(story: dict) -> int:
        """How much of this story's Activity you have not seen. The feed is only worked out
        when a read has finished since you last looked, which is the rare case."""
        newest = conn.execute(
            "SELECT max(id) FROM extraction_runs WHERE story_id=? AND status='ok'", (story["id"],)
        ).fetchone()[0]
        if not newest or newest <= story["seen_run_id"]:
            return 0
        return sum(e["new"] for e in signals.activity(conn, story["id"], limit=None))

    def standing(story: dict) -> dict:
        """Where a story stands now: its clock, who you play, where, and who is there."""
        path = chat.active_path(conn, story["id"])
        now = path[-1]["story_time"] if path else 0
        scene_id = chat.scene_of(conn, story["id"], path)
        scene = conn.execute(
            "SELECT place_id, title FROM scenes WHERE id IS ?", (scene_id,)
        ).fetchone()
        here = {e["id"] for e in chat.present_entities(conn, scene_id, path)}
        ai = conn.execute(
            "SELECT id, name, lib_item_id FROM entities"
            " WHERE story_id=? AND is_ai=1 AND hidden=0 ORDER BY id",
            (story["id"],),
        )
        last = next((m for m in reversed(path) if m["role"] != "system" and not m["hidden"]), None)
        speaker = ref(last["speaker_id"]) if last else None
        return {
            "pinned": bool(story["pinned"]),
            "clock": clock.label(now, story["epoch_offset_min"]),
            "story_time": now,
            "minute_of_day": (now + story["epoch_offset_min"]) % clock.DAY,
            "persona": ref(story["persona_entity_id"]),
            "place": ref(scene["place_id"]) if scene else None,
            "scene_title": scene["title"] if scene else None,
            "cast": [{**dict(e), "present": e["id"] in here} for e in ai],
            "last_line": last and {"speaker": speaker and speaker["name"], "text": last["text"]},
            "new_events": new_events(story),
            "waiting": len(extract.pending(conn, story["id"])),
        }

    @app.get("/stories")
    async def list_stories():
        """Pinned first, then the most recently played. ponytail: one path walk per story;
        cache per story version if a library ever holds hundreds of stories."""
        rows = conn.execute(
            "SELECT s.*, count(m.id) AS messages,"
            " coalesce(max(m.created_at), s.created_at) AS last_at, max(m.id) AS last_id"
            " FROM stories s LEFT JOIN messages m ON m.story_id=s.id GROUP BY s.id"
            " ORDER BY s.pinned DESC, last_at DESC, coalesce(last_id, 0) DESC, s.id DESC"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"],
                "last_at": r["last_at"],
                "messages": r["messages"],
                **standing(dict(r)),
            }
            for r in rows
        ]

    @app.post("/stories", status_code=201)
    async def add_story(s: StoryIn):
        for item_id in [*s.character_ids, s.place_id, s.persona_id, s.scenario_id]:
            if item_id is not None and library.get_item(conn, item_id) is None:
                raise HTTPException(422, f"no library item {item_id}")
        story_id = library.create_story(conn, **s.model_dump())
        return await get_story(story_id)

    @app.get("/stories/{story_id}")
    async def get_story(story_id: int):
        story = story_row(story_id)
        overrides = json.loads(story["overrides"])
        return {
            "id": story["id"],
            "title": story["title"],
            "persona_id": story["persona_entity_id"],
            "minutes_per_turn": story["minutes_per_turn"],
            "epoch_offset_min": story["epoch_offset_min"],
            "start_clock": clock.label(0, story["epoch_offset_min"]),  # for the opening card
            "roles": overrides.get("roles", {}),
            **standing(story),
        }

    @app.patch("/stories/{story_id}")
    async def edit_story(story_id: int, s: StoryPatch):
        story = story_row(story_id)
        fields = s.model_dump(exclude_unset=True, exclude={"roles"})
        if s.roles is not None:
            overrides = json.loads(story["overrides"])
            overrides["roles"] = s.roles
            fields["overrides"] = json.dumps(overrides)
        _patch(conn, "stories", story_id, fields)
        return await get_story(story_id)

    @app.post("/stories/{story_id}/seen", status_code=204)
    async def mark_seen(story_id: int):
        """The user has looked at this story: memory reads up to now are no longer new."""
        story_row(story_id)
        with conn:
            conn.execute(
                "UPDATE stories SET seen_run_id="
                "(SELECT coalesce(max(id), 0) FROM extraction_runs WHERE story_id=?) WHERE id=?",
                (story_id, story_id),
            )

    @app.delete("/stories/{story_id}", status_code=204)
    async def remove_story(story_id: int):
        with conn:
            conn.execute("DELETE FROM stories WHERE id=?", (story_id,))

    @app.get("/activity")
    async def activity(
        story_id: int | None = None,
        kind: str | None = None,
        limit: int = Query(100, ge=1, le=500),
    ):
        """What the stories have signalled, newest first: memory, belief, feeling, time."""
        return signals.activity(conn, story_id, kind, limit)

    @app.get("/stories/{story_id}/signals")
    async def get_signals(story_id: int):
        """Per line: who heard it and how clearly they will remember it; what a reply recalled."""
        story_row(story_id)
        return signals.signals(conn, story_id)

    @app.get("/stories/{story_id}/messages")
    async def get_messages(story_id: int):
        return messages(story_id)

    @app.get("/stories/{story_id}/cast")
    async def get_cast(story_id: int):
        story = story_row(story_id)
        path = chat.active_path(conn, story_id)
        scene_id = chat.scene_of(conn, story_id, path)
        here = {e["id"] for e in chat.present_entities(conn, scene_id, path)}
        times = {m["id"]: m["story_time"] for m in path}
        scene = conn.execute("SELECT * FROM scenes WHERE id IS ?", (scene_id,)).fetchone()
        rows = conn.execute(
            "SELECT id, kind, name, summary, is_ai, lib_item_id FROM entities"
            " WHERE story_id=? AND hidden=0 ORDER BY kind, name",
            (story_id,),
        )
        return {
            "scene": dict(scene) if scene else None,
            "entities": [
                {
                    **dict(r),
                    "present": r["id"] in here,
                    "persona": r["id"] == story["persona_entity_id"],
                }
                for r in rows
            ],
            "changes": [
                {**c, "clock": clock.label(times[c["message_id"]], story["epoch_offset_min"])}
                for c in chat.presence_changes(conn, story_id, path)
            ],
        }

    @app.post("/stories/{story_id}/turn")
    async def take_turn(story_id: int, t: TurnIn):
        story_row(story_id)
        check_audience(story_id, t.audience)
        make_way(story_id)
        return stream(
            story_id,
            turns.turn(conn, llm, story_id, t.text, t.speaker, get_key, t.audience, t.skip),
        )

    @app.post("/stories/{story_id}/line", status_code=201)
    async def add_line(story_id: int, line: LineIn):
        """A line with no reply (a thought, an action), or time passing. Never calls a model."""
        story_row(story_id)
        check_audience(story_id, line.audience)
        try:
            written = turns.say(conn, story_id, line.text, line.audience, line.skip)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        if written is None:
            raise HTTPException(422, "Say something, or let some time pass.")
        worker.poke(story_id)  # the story may now have lines worth remembering
        return messages(story_id)

    @app.post("/stories/{story_id}/regenerate")
    async def regenerate(story_id: int):
        story_row(story_id)
        make_way(story_id)
        return stream(story_id, turns.regenerate(conn, llm, story_id, get_key))

    @app.post("/stories/{story_id}/swipe")
    async def swipe(story_id: int, s: SwipeIn):
        """Show the previous or next alternative at this point in the story."""
        m = _row(conn, "SELECT * FROM messages WHERE id=? AND story_id=?", (s.message_id, story_id))
        ids = [
            r[0]
            for r in conn.execute(
                "SELECT id FROM messages WHERE story_id=? AND parent_id IS ? ORDER BY id",
                (story_id, m["parent_id"]),
            )
        ]
        target = ids[(ids.index(m["id"]) + s.step) % len(ids)]
        chat.set_leaf(conn, story_id, target)
        return messages(story_id)

    @app.patch("/messages/{message_id}")
    async def edit_message(message_id: int, p: MessagePatch):
        m = _row(conn, "SELECT * FROM messages WHERE id=?", (message_id,))
        if p.text is not None:
            chat.edit_message(conn, message_id, p.text)
        if p.hidden is not None:
            _patch(conn, "messages", message_id, {"hidden": p.hidden})
        if p.skip_minutes is not None:
            chat.set_skip(conn, message_id, p.skip_minutes)
        return messages(m["story_id"])

    @app.post("/stories/{story_id}/presence")
    async def set_presence(story_id: int, p: PresenceIn):
        _row(conn, "SELECT id FROM entities WHERE id=? AND story_id=?", (p.entity_id, story_id))
        chat.set_presence(conn, story_id, p.entity_id, p.present)
        return await get_cast(story_id)

    @app.delete("/presence/{presence_id}")
    async def undo_presence(presence_id: int):
        """Undo an arrival or departure, whoever wrote it."""
        row = _row(
            conn,
            "SELECT s.story_id FROM presence p JOIN scenes s ON s.id=p.scene_id WHERE p.id=?",
            (presence_id,),
        )
        with conn:
            conn.execute("DELETE FROM presence WHERE id=?", (presence_id,))
        return await get_cast(row["story_id"])

    @app.post("/stories/{story_id}/cast", status_code=201)
    async def join(story_id: int, j: JoinIn):
        """Bring a library character into the story; they arrive in the current scene."""
        story_row(story_id)
        if library.get_item(conn, j.library_id) is None:
            raise HTTPException(422, f"no library item {j.library_id}")
        entity_id = library.add_to_story(conn, story_id, j.library_id)
        if (
            conn.execute("SELECT kind FROM entities WHERE id=?", (entity_id,)).fetchone()[0]
            == "character"
        ):
            chat.set_presence(conn, story_id, entity_id, True)
        return await get_cast(story_id)

    @app.post("/stories/{story_id}/scene", status_code=201)
    async def new_scene(story_id: int, s: SceneIn):
        story_row(story_id)
        place_id = s.place_id
        if s.library_place_id is not None:
            if library.get_item(conn, s.library_place_id) is None:
                raise HTTPException(422, f"no library item {s.library_place_id}")
            place_id = library.add_to_story(conn, story_id, s.library_place_id)
        try:
            skip = turns.read_skip(conn, story_id, s.skip) if s.skip and s.skip.strip() else 0
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        chat.new_scene(conn, story_id, s.present, place_id, s.title, skip)
        worker.poke(story_id)  # the closed scene is worth a careful read
        return await get_cast(story_id)

    # --- memory: extraction runs and the inspector ------------------------------------------

    def run_out(row) -> dict:
        out = dict(row)
        out["warnings"] = json.loads(row["warnings"]) if row["warnings"] else []
        out.pop("raw")
        count = "SELECT count(*) FROM memories WHERE run_id=?"
        out["filed"] = conn.execute(count, (row["id"],)).fetchone()[0]
        return out

    @app.get("/stories/{story_id}/version")
    async def version(story_id: int):
        """Cheap to poll: changes whenever a memory read starts, finishes or goes away."""
        story_row(story_id)
        top, runs, ok, busy = conn.execute(
            "SELECT coalesce(max(id), 0), count(*), coalesce(sum(status='ok'), 0),"
            " coalesce(sum(status IN ('pending', 'running')), 0)"
            " FROM extraction_runs WHERE story_id=?",
            (story_id,),
        ).fetchone()
        return {"v": f"{top}:{runs}:{ok}:{busy}", "waiting": len(extract.pending(conn, story_id))}

    @app.post("/stories/{story_id}/extract")
    async def extract_now(story_id: int):
        """Read whatever is waiting now, instead of waiting for the next quiet moment."""
        story_row(story_id)
        run_id = await extract.run_due(conn, llm, story_id, get_key, manual=True)
        if run_id is None:
            return {"run": None}
        return {"run": run_out(_row(conn, "SELECT * FROM extraction_runs WHERE id=?", (run_id,)))}

    @app.get("/stories/{story_id}/runs")
    async def list_runs(story_id: int):
        rows = conn.execute(
            "SELECT * FROM extraction_runs WHERE story_id=? ORDER BY id DESC", (story_id,)
        )
        return [run_out(r) for r in rows]

    @app.post("/runs/{run_id}/reread")
    async def reread(run_id: int, r: RereadIn):
        _row(conn, "SELECT id FROM extraction_runs WHERE id=?", (run_id,))
        new_id = await extract.reread(conn, llm, run_id, r.role, get_key)
        if new_id is None:
            raise HTTPException(409, f"no model is set for {r.role!r}")
        return run_out(_row(conn, "SELECT * FROM extraction_runs WHERE id=?", (new_id,)))

    @app.get("/stories/{story_id}/entities")
    async def list_entities(story_id: int):
        rows = conn.execute(
            "SELECT * FROM entities WHERE story_id=? ORDER BY kind, name", (story_id,)
        )
        out = []
        for r in rows:
            aliases = [
                a[0]
                for a in conn.execute("SELECT alias FROM aliases WHERE entity_id=?", (r["id"],))
            ]
            flags = conn.execute(
                "SELECT key, value, story_time, private FROM flags WHERE entity_id=?"
                " ORDER BY story_time, id",
                (r["id"],),
            )
            out.append({**dict(r), "aliases": aliases, "flags": [dict(f) for f in flags]})
        return out

    @app.patch("/entities/{entity_id}")
    async def edit_entity(entity_id: int, p: EntityPatch):
        _row(conn, "SELECT id FROM entities WHERE id=?", (entity_id,))
        _patch(conn, "entities", entity_id, p.model_dump(exclude_unset=True))
        return _row(conn, "SELECT * FROM entities WHERE id=?", (entity_id,))

    @app.post("/entities/merge")
    async def merge(m: MergeIn):
        keep = _row(conn, "SELECT * FROM entities WHERE id=?", (m.keep,))
        drop = _row(conn, "SELECT * FROM entities WHERE id=?", (m.drop,))
        if keep["story_id"] != drop["story_id"] or m.keep == m.drop:
            raise HTTPException(422, "can only merge two different entities of the same story")
        library.merge_entities(conn, m.keep, m.drop)
        return _row(conn, "SELECT * FROM entities WHERE id=?", (m.keep,))

    @app.get("/stories/{story_id}/memories")
    async def list_memories(story_id: int, knower: int | None = None):
        """With `knower`: everything that character knows and how well they recall it now.
        Without: every memory in the story, and who knows it."""
        story_row(story_id)
        if knower is not None:
            return retrieve.inspect(conn, story_id, knower)
        rows = conn.execute("SELECT * FROM memories WHERE story_id=? ORDER BY id", (story_id,))
        out = []
        for r in rows:
            knowers = conn.execute(
                "SELECT DISTINCT knower_id FROM knowledge WHERE memory_id=?", (r["id"],)
            )
            out.append({**dict(r), "knowers": [k[0] for k in knowers]})
        return out

    @app.post("/stories/{story_id}/memories", status_code=201)
    async def add_memory(story_id: int, m: MemoryIn):
        story_row(story_id)
        memory_id = library.add_memory(conn, story_id, **m.model_dump())
        return _row(conn, "SELECT * FROM memories WHERE id=?", (memory_id,))

    @app.patch("/memories/{memory_id}")
    async def edit_memory(memory_id: int, p: MemoryPatch):
        _row(conn, "SELECT id FROM memories WHERE id=?", (memory_id,))
        _patch(conn, "memories", memory_id, p.model_dump(exclude_unset=True))
        return _row(conn, "SELECT * FROM memories WHERE id=?", (memory_id,))

    @app.get("/stories/{story_id}/context")
    async def latest_context(story_id: int):
        """The last prompt assembled for this story: sections, recalled memories, the prompt."""
        return context_out(
            _row(conn, "SELECT * FROM context_log WHERE story_id=? ORDER BY id DESC", (story_id,))
        )

    def context_out(row: dict) -> dict:
        for key in ("sections", "memories", "prompt"):
            row[key] = json.loads(row[key]) if row[key] else None
        return row

    return app
