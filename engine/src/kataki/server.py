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

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from kataki import __version__, chat, clock, extract, library, retrieve, roles, turns
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


class StoryPatch(BaseModel):
    title: str | None = None
    minutes_per_turn: int | None = None
    roles: dict | None = None  # per-story role overrides, same shape as PUT /roles/{role}


class TurnIn(BaseModel):
    text: str | None = None
    speaker: int | Literal["narrator"] | None = None


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
    place_id: int | None = None
    title: str | None = None


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

    def require_token(authorization: str = Header("")):
        if not hmac.compare_digest(authorization.encode(), f"Bearer {token}".encode()):
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

    # --- stories ---------------------------------------------------------------------------

    @app.get("/stories")
    async def list_stories():
        rows = conn.execute(
            "SELECT s.id, s.title, s.created_at, count(m.id) AS messages FROM stories s"
            " LEFT JOIN messages m ON m.story_id=s.id GROUP BY s.id ORDER BY s.id DESC"
        )
        return [dict(r) for r in rows]

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
        path = chat.active_path(conn, story_id)
        now = path[-1]["story_time"] if path else 0
        overrides = json.loads(story["overrides"])
        return {
            "id": story["id"],
            "title": story["title"],
            "persona_id": story["persona_entity_id"],
            "minutes_per_turn": story["minutes_per_turn"],
            "clock": clock.label(now, story["epoch_offset_min"]),
            "roles": overrides.get("roles", {}),
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

    @app.delete("/stories/{story_id}", status_code=204)
    async def remove_story(story_id: int):
        with conn:
            conn.execute("DELETE FROM stories WHERE id=?", (story_id,))

    @app.get("/stories/{story_id}/messages")
    async def get_messages(story_id: int):
        return messages(story_id)

    @app.get("/stories/{story_id}/cast")
    async def get_cast(story_id: int):
        story = story_row(story_id)
        path = chat.active_path(conn, story_id)
        scene_id = chat.scene_of(conn, story_id, path)
        here = {e["id"] for e in chat.present_entities(conn, scene_id, path)}
        scene = conn.execute("SELECT * FROM scenes WHERE id IS ?", (scene_id,)).fetchone()
        rows = conn.execute(
            "SELECT id, kind, name, summary, is_ai FROM entities"
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
        }

    @app.post("/stories/{story_id}/turn")
    async def take_turn(story_id: int, t: TurnIn):
        story_row(story_id)
        make_way(story_id)
        return stream(story_id, turns.turn(conn, llm, story_id, t.text, t.speaker, get_key))

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

    @app.post("/stories/{story_id}/scene", status_code=201)
    async def new_scene(story_id: int, s: SceneIn):
        story_row(story_id)
        chat.new_scene(conn, story_id, s.present, s.place_id, s.title)
        worker.poke(story_id)  # the closed scene is worth a careful read
        return await get_cast(story_id)

    # --- memory: extraction runs and the inspector ------------------------------------------

    def run_out(row) -> dict:
        out = dict(row)
        out["warnings"] = json.loads(row["warnings"]) if row["warnings"] else []
        out.pop("raw")
        return out

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
