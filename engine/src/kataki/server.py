"""HTTP adapter over the engine: the desktop app's API.

Every route needs the per-launch bearer token. Routes are async on purpose: the engine
shares one SQLite connection, and keeping all work on the event loop means it is never
used from two threads at once (ponytail: fine for one local user; a connection per request
if this ever serves many).
"""

import asyncio
import contextlib
import functools
import hmac
import json
import logging
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles

from kataki import (
    __version__,
    archive,
    backups,
    between,
    bonds,
    cards,
    catalogue,
    chat,
    chats,
    clock,
    draft,
    extract,
    features,
    growth,
    images,
    intake,
    library,
    lore,
    media,
    mind,
    people,
    profile,
    readable,
    recollect,
    retrieve,
    roles,
    signals,
    speech,
    turns,
    usage,
)
from kataki.host import Host, LocalHost
from kataki.llm import LLM, SAMPLER_KEYS, LLMError, NoCredit

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


class DrawIn(BaseModel):
    provider: str | None = None  # None: the first HF provider that serves the model


class DraftIn(BaseModel):
    words: str  # the character, described however you like


class PickIn(BaseModel):
    name: str  # a media name from the item's history


class LookIn(BaseModel):
    expressions: list[str] | None = None  # None: all five
    provider: str | None = None  # for the edits; the cutout has one provider


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
    first_message: str = ""  # how it opens, when not from a plot
    epoch_offset_min: int = Field(480, ge=0)  # the clock at the start: 480 = Day 1, 08:00
    talk: Literal["person", "text"] = "person"  # How you talk: in person, or texting


class BookIn(BaseModel):
    title: str
    blurb: str = ""


class BookPatch(BaseModel):
    title: str | None = None
    blurb: str | None = None


class BookOrder(BaseModel):
    story_ids: list[int]


class LinkIn(BaseModel):
    to_story_id: int
    kind: Literal["continuation", "shared_universe", "reference"] = "continuation"
    offset_min: int = 0
    note: str | None = None


class ChapterIn(BaseModel):
    title: str
    from_message_id: int


class ChapterPatch(BaseModel):
    title: str | None = None
    to_message_id: int | None = None
    open: bool | None = None  # true reopens it: it runs to the newest line again


class Moment(BaseModel):
    name: str = Field(min_length=1, max_length=80)  # "the storm"
    at: int = Field(ge=0)  # story time, in minutes


class StoryPatch(BaseModel):
    title: str | None = None
    minutes_per_turn: int | None = None
    pinned: bool | None = None
    book_id: int | None = None
    tags: list[str] | None = None
    roles: dict | None = None  # per-story role overrides, same shape as PUT /roles/{role}
    ui: dict | None = None  # the app's own per-story state (widget layout, notes); never read here
    moments: list[Moment] | None = None  # what the story's dates count from
    persona_id: int | None = None  # who you are from now on (a library persona); None = no one
    talk: Literal["person", "text"] | None = None  # How you talk: in person, or texting


class TurnIn(BaseModel):
    text: str | None = None
    speaker: int | Literal["narrator"] | None = None
    # who the user's line is for: None = all present, [] = a thought
    audience: list[int] | None = None
    skip: str | None = None  # time that passes first, in words: "the next morning"
    narrate: bool = False  # the line is narration, not the persona speaking


class LineIn(BaseModel):
    text: str | None = None
    audience: list[int] | None = None
    skip: str | None = None
    narrate: bool = False


class RewriteIn(BaseModel):
    text: str


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
    looks: str | None = None
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
    core_locked: bool | None = None  # Lock (minds slice 6): never distorted, never forgotten


class ReflectionAct(BaseModel):
    action: Literal["accept", "reject", "lock"]


class VersionIn(BaseModel):
    knower: int
    text: str | None = Field(None, max_length=1000)  # None: back on the truth


def moments_of(story) -> list[dict]:
    """The moments a story has named, which its dates count from."""
    return json.loads(story["overrides"]).get("moments", [])


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


class WebApp(StaticFiles):
    """The built app. A path with no file behind it is one of the router's pages, so it gets
    index.html; a missing file (a path with an extension) is still a 404."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as e:
            if e.status_code != 404 or Path(path).suffix:
                raise
            return await super().get_response("index.html", scope)


def create_app(
    conn: sqlite3.Connection,
    token: str,
    llm: LLM | None = None,
    worker_delay: float = 3.0,
    get_key=roles.get_key,
    image_transport=None,  # tests script the HF router here
    web_dir: Path | None = None,  # the built app, served under /app/ for any browser
    db_path: Path | None = None,  # the library's file: backups live beside it
    host: Host | None = None,  # where it runs (track B1); None: the desktop, keys from get_key
) -> FastAPI:
    host = host or LocalHost(get_key=get_key)
    get_key = host.get_key
    llm = llm or LLM()
    billed = host.meter is not None or host.allow is not None
    if billed and (llm.on_usage is not None or llm.allow is not None):
        # one LLM per app: a shared one would bill and gate one user's calls as another's
        raise ValueError("this LLM already meters or gates another app; give each app its own")
    if llm.on_usage is None:  # a test may bring its own meter
        llm.on_usage = functools.partial(host.on_usage, conn)
    if host.allow is not None:  # the credit gate (track B3), priced in dollars for the host

        def gate(ep, ask) -> bool:
            estimate = usage.cost(host.price_table(conn), ep.model, ep.role, ask)
            return estimate is not None and host.allow(ep, estimate)  # unpriced: not billable

        llm.allow = gate
    if not host.local_routes:  # online: a role's raw JSON tunes the sampler, not the bill
        llm.body_keys = SAMPLER_KEYS
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

    async def this_host():
        """Every request runs on its host's channel (async: the ContextVar is set in the
        request's own task, so its turn and anything it pokes inherit it)."""
        features.CURRENT.set(host.channel())

    def local_only():
        """Routes about this machine (providers and keys, backups on disk) exist only here, and
        so do pictures until they are priced, gated and metered (track B4)."""
        if not host.local_routes:
            raise HTTPException(404, "Not Found")

    app = FastAPI(
        title="Kataki RPAI engine",
        version=__version__,
        dependencies=[Depends(require_token), Depends(this_host)],
    )
    app.state.worker = worker  # online, closing a library stops its background job (B5)

    @app.exception_handler(sqlite3.OperationalError)
    async def no_room(request: Request, e: sqlite3.OperationalError):
        """A write that failed for space or permission (N2): said as such, so the app can hold
        the window until it can write again. Anything else is still a plain failure."""
        said = str(e).lower()
        code = (
            "DISK_FULL"
            if "full" in said
            else "DISK_READONLY"
            if "readonly" in said or "read-only" in said
            else None
        )
        if code is None:
            raise e
        return JSONResponse({"detail": {"code": code, "message": str(e)}}, status_code=507)

    @app.exception_handler(NoCredit)
    async def no_credit(request: Request, e: NoCredit):
        """Refused before it was sent (spec §8.4): 402, said as a code the app can act on."""
        detail = {"code": e.code, "message": str(e)}
        return JSONResponse({"code": e.code, "detail": detail}, status_code=402)

    def failed(e: LLMError, said: str = "") -> Exception:
        """A model call that failed is the provider's 502, but a refusal stays a refusal."""
        if isinstance(e, NoCredit):  # a fresh one, so `raise failed(e) from e` is not e from e
            return type(e)(str(e))  # the daily cap stays the daily cap
        return HTTPException(502, f"{said}{e}")

    # Any origin is fine: auth is a bearer token, not a cookie, so a foreign page has
    # nothing to ride on.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        # the app is on another origin, and a browser hides every response header but a handful:
        # without this, a file it saves has no name of ours and lands as "kataki"
        expose_headers=["Content-Disposition"],
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
        moments = moments_of(story)
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
                    "date": clock.date(m["story_time"], story["epoch_offset_min"], moments),
                    "scene_id": m["scene_id"],
                    "swipe": chat.sibling_position(conn, m["id"]),
                    "reasoning": gen.get("reasoning"),
                    "finish": gen.get("finish"),
                    "model": gen.get("model"),
                    "audience": chat.audience_of(m),
                    "think_ms": gen.get("think_ms"),
                    "expression": m["expression"],
                    "ooc": bool(gen.get("ooc")),  # an out-of-character aside (minds slice 4)
                    "delivery": gen.get("delivery"),  # the texting bubbles (minds slice 9)
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
                code = {"code": e.code} if isinstance(e, NoCredit) else {}
                await queue.put(("error", {"message": f"{type(e).__name__}: {e}", **code}))
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

    def meanwhile(story_id: int) -> None:
        """Time passed: each character's life between scenes is worked out now, in code (minds
        slice 5); the diaries follow in the background. Never fails the request."""
        try:
            between.at_skip(conn, story_id, chat.active_path(conn, story_id))
        except Exception as e:
            logging.getLogger(__name__).warning("between skipped for story %s: %s", story_id, e)

    def make_way(story_id: int) -> None:
        """A reply is about to be generated: the background reader steps aside if it would
        compete for the same model server."""
        if ep := roles.resolve(conn, "rp", story_id, get_key):
            worker.turn_started(story_id, ep.base_url)

    # --- health and settings ---------------------------------------------------------------

    @app.get("/health")
    async def health():
        schema = conn.execute("PRAGMA user_version").fetchone()[0]
        return {
            "status": "ok",
            "version": __version__,
            "schema": schema,
            "channel": features.channel(),
            "host": host.name,
        }

    @app.get("/features")
    async def list_features():
        return features.listing(conn)

    @app.get("/search")
    async def search(q: str, limit: int = Query(50, ge=1, le=500)):
        """Names, lines and memories that contain `q` (C5–C9). The app ranks them."""
        like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        rows = lambda sql: [dict(r) for r in conn.execute(sql, (like, limit))]  # noqa: E731
        return {
            "stories": rows("SELECT id, title FROM stories WHERE title LIKE ? ESCAPE '\\' LIMIT ?"),
            # a name, or what the item says about itself ("The palace sends out the gala list");
            # never the private field, which only the character knows
            "items": [
                dict(r)
                for r in conn.execute(
                    "SELECT id, kind, name, description FROM lib_items"
                    " WHERE name LIKE :q ESCAPE '\\' OR description LIKE :q ESCAPE '\\'"
                    " ORDER BY name LIKE :q ESCAPE '\\' DESC, name LIMIT :n",
                    {"q": like, "n": limit},
                )
            ],
            "books": rows("SELECT id, title FROM books WHERE title LIKE ? ESCAPE '\\' LIMIT ?"),
            "lines": rows(
                "SELECT m.id, m.story_id, s.title AS story_title, e.name AS speaker, m.text"
                " FROM messages m JOIN stories s ON s.id=m.story_id LEFT JOIN entities e ON e.id=m.speaker_id"
                " WHERE m.hidden=0 AND m.role!='system' AND m.text LIKE ? ESCAPE '\\'"
                " ORDER BY m.id DESC LIMIT ?"
            ),
            "memories": rows(
                "SELECT m.id, m.story_id, s.title AS story_title, m.detail FROM memories m"
                " JOIN stories s ON s.id=m.story_id WHERE m.hidden=0 AND m.detail LIKE ? ESCAPE '\\'"
                " ORDER BY m.id DESC LIMIT ?"
            ),
        }

    @app.get("/settings")
    async def get_settings():
        return {r["key"]: json.loads(r["value"]) for r in conn.execute("SELECT * FROM settings")}

    @app.put("/settings")
    async def put_settings(values: dict):
        if "prices" in values and host.prices is not None:  # online: the service's table
            raise HTTPException(403, "Prices are set by the service.")
        with conn:
            for key, value in values.items():
                conn.execute(
                    "INSERT OR REPLACE INTO settings(key, value) VALUES(?, ?)",
                    (key, json.dumps(value)),
                )
        return await get_settings()

    @app.get("/profile/stats")
    async def profile_stats():
        """The numbers on the profile card; the card itself is the `profile` setting."""
        return profile.stats(conn)

    # --- providers and model roles ---------------------------------------------------------

    def provider_out(row) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "base_url": row["base_url"],
            "has_key": bool(get_key(row["name"])),
        }

    @app.get("/providers", dependencies=[Depends(local_only)])
    async def list_providers():
        return [provider_out(r) for r in conn.execute("SELECT * FROM providers ORDER BY name")]

    @app.post("/providers", status_code=201, dependencies=[Depends(local_only)])
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

    @app.patch("/providers/{pid}", dependencies=[Depends(local_only)])
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

    @app.delete("/providers/{pid}", status_code=204, dependencies=[Depends(local_only)])
    async def remove_provider(pid: int):
        old = _row(conn, "SELECT * FROM providers WHERE id=?", (pid,))
        with conn:
            conn.execute(
                "UPDATE model_roles SET provider_id=NULL, model=NULL WHERE provider_id=?", (pid,)
            )
            conn.execute("DELETE FROM providers WHERE id=?", (pid,))
        roles.delete_key(old["name"])

    @app.get("/providers/detect", dependencies=[Depends(local_only)])
    async def detect_providers():
        """Model servers already running on this machine, for the first-run wizard."""

        async def probe(name, url):
            with contextlib.suppress(LLMError, asyncio.TimeoutError):
                models = await asyncio.wait_for(llm.list_models(url, None), timeout=1.5)
                return {"name": name, "base_url": url, "models": models}

        found = await asyncio.gather(*(probe(n, u) for n, u in LOCAL_SERVERS.items()))
        return [f for f in found if f]

    @app.get("/providers/{pid}/models", dependencies=[Depends(local_only)])
    async def provider_models(pid: int):
        """The ids a connection lists (`models`), and what is known about each (`info`): what
        the server says, the library's price where it has one, and when it was last used."""
        p = _row(conn, "SELECT * FROM providers WHERE id=?", (pid,))
        try:
            listed = await llm.models(p["base_url"], get_key(p["name"]))
        except LLMError as e:
            raise failed(e) from e
        prices = host.price_table(conn)
        used = dict(conn.execute("SELECT model, MAX(at) FROM usage_log GROUP BY model").fetchall())
        info = []
        for raw in listed:
            m = catalogue.describe(raw)
            ours = prices.get(m["id"])
            if isinstance(ours, dict) and "input" in ours and "output" in ours:
                m["input"], m["output"] = ours["input"], ours["output"]
            if m["id"] in used:
                m["last_used"] = used[m["id"]]
            info.append(m)
        return {"models": [m["id"] for m in info], "info": info}

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
            raise failed(e) from e
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

    @app.get("/library/{item_id}/same")
    async def same_person(item_id: int):
        """Every story this person plays in, and how much that self holds."""
        await get_item(item_id)
        return library.same_person(conn, item_id)

    @app.get("/library/{item_id}/profile")
    async def get_profile(item_id: int):
        """Everywhere this friend has been: their stories, what they are like in each, and the
        places they have played. For a persona, who knows them and how well."""
        await get_item(item_id)
        return people.profile(conn, item_id)

    @app.patch("/library/{item_id}")
    async def edit_item(item_id: int, item: ItemPatch):
        await get_item(item_id)
        library.update_item(conn, item_id, **item.model_dump(exclude_unset=True))
        return library.get_item(conn, item_id)

    @app.delete("/library/{item_id}", status_code=204)
    async def remove_item(item_id: int):
        library.delete_item(conn, item_id)

    # --- pictures, through the image job (M3 spec §7): every one is a click and costs money --

    def picture_job():
        """The image job's endpoint and a client for it, or why there is none."""
        ep = roles.resolve(conn, "image", None, get_key)
        hf = ep and urlparse(ep.base_url).hostname == "router.huggingface.co"
        if not hf or not ep.api_key:
            raise HTTPException(
                409, "Pictures need the image job set to a HuggingFace model, with its key."
            )
        return ep, images.Images(ep.api_key, transport=image_transport)

    def refused(e: images.ImageError) -> dict:
        return {"message": str(e), "refused": e.refused, "alt": e.alt}

    def keep(data: bytes) -> str:
        if (ext := media.sniff(data)) is None:
            raise images.ImageError("the provider sent something that is not a picture")
        return media.save(conn, data, ext)

    @app.post("/library/draft")
    async def draft_character(d: DraftIn):
        """A character profile from your own words, filled in by the memory reader's model. It
        is only a draft: the editor shows it, and nothing is saved until you save it."""
        if not d.words.strip():
            raise HTTPException(422, "Describe them in a few words first.")
        if (ep := roles.resolve(conn, "utility", None, get_key)) is None:
            raise HTTPException(409, "No model is set for the Memory reader or Characters yet.")
        try:
            return await draft.character(llm, ep, d.words)
        except LLMError as e:
            raise failed(e, "The model could not write a profile: ") from e

    @app.post("/library/{item_id}/draw", dependencies=[Depends(local_only)])
    async def draw_item(item_id: int, d: DrawIn):
        """A place's background, or a character's first picture, from their own words: one
        paid call through the image job. It replaces the picture they had."""
        item = await get_item(item_id)
        if item["kind"] not in ("place", "character"):
            raise HTTPException(422, "only places and characters can be drawn")
        if item["kind"] == "character" and images.minor(item):
            raise HTTPException(422, images.MINOR_SAID)
        ep, client = picture_job()
        place = item["kind"] == "place"
        prompt = images.place_prompt(item) if place else images.portrait_prompt(item)
        size = images.PLACE_SIZE if place else images.PORTRAIT_SIZE
        try:
            name = keep(await client.draw(ep.model, prompt, *size, d.provider))
        except images.ImageError as e:
            raise HTTPException(502, refused(e)) from e
        finally:
            await client.aclose()
        library.update_item(
            conn,
            item_id,
            data=images.with_picture(item["data"], "image" if place else "portrait", name),
        )
        return library.get_item(conn, item_id)

    @app.post("/library/{item_id}/picture")
    async def pick_picture(item_id: int, p: PickIn):
        """Go back to an earlier picture: free, no model. The current one joins the history,
        and a character gets back the expressions made from the picture they return to."""
        item = await get_item(item_id)
        key = "image" if item["kind"] == "place" else "portrait"
        if p.name not in item["data"].get("history", []):
            raise HTTPException(422, "that picture is not one of this item's earlier pictures")
        data = images.with_picture(item["data"], key, p.name)
        if pack := (data.get("packs") or {}).get(p.name):
            data["pack"] = pack
        library.update_item(conn, item_id, data=data)
        return library.get_item(conn, item_id)

    @app.post("/library/{item_id}/look", dependencies=[Depends(local_only)])
    async def make_look(item_id: int, d: LookIn):
        """A character's sprites: each asked-for expression edited from their portrait (the
        sheet) and cut out, all at once. Two paid calls each. What worked is kept even when
        some fail; those come back in `failed`, each with its reason."""
        item = await get_item(item_id)
        sheet = item["data"].get("portrait")
        if item["kind"] != "character" or not sheet or not (path := media.find(conn, sheet)):
            raise HTTPException(
                422, "a look is made from a character's picture; draw or add one first"
            )
        if images.minor(item):
            raise HTTPException(422, images.MINOR_SAID)
        if unknown := set(d.expressions or ()) - set(images.EXPRESSIONS):
            raise HTTPException(422, f"no such expression: {', '.join(sorted(unknown))}")
        ep, client = picture_job()
        edit = ep.params.get("edit_model", images.DEFAULTS["edit_model"])
        cutout = ep.params.get("cutout_model", images.DEFAULTS["cutout_model"])
        source = path.read_bytes()

        async def sprite(expression: str) -> str:
            made = await client.edit(
                edit, source, images.sprite_prompt(item, expression), d.provider
            )
            return keep(await client.cutout(cutout, made))

        wanted = d.expressions or list(images.EXPRESSIONS)
        try:
            results = await asyncio.gather(*map(sprite, wanted), return_exceptions=True)
        finally:
            await client.aclose()
        old = item["data"].get("pack") or {}
        # redrawing a few keeps the rest, unless the rest were made from another picture
        sprites = dict(old.get("sprites", {})) if old.get("from") == sheet else {}
        failed = {}
        for expression, result in zip(wanted, results, strict=True):
            if isinstance(result, images.ImageError):
                failed[expression] = refused(result)
            elif isinstance(result, BaseException):
                raise result
            else:
                sprites[expression] = result
        if sprites:
            pack = {"from": sheet, "sprites": sprites}
            # kept per picture too, so going back to an earlier picture brings its faces back
            packs = {**(item["data"].get("packs") or {}), sheet: pack}
            library.update_item(conn, item_id, data={**item["data"], "pack": pack, "packs": packs})
        return {"item": library.get_item(conn, item_id), "failed": failed}

    # --- media: portraits and place images ------------------------------------------------

    @app.post("/media", status_code=201)
    async def add_media(request: Request):
        data = await request.body()
        if len(data) > media.MAX_BYTES:
            raise HTTPException(413, "Images can be at most 20 MB.")
        if (ext := media.sniff(data)) is None:
            raise HTTPException(415, "Only PNG, JPEG, GIF or WebP images.")
        return {"name": media.save(conn, data, ext), "bytes": len(data)}

    # --- in: what other apps made ----------------------------------------------------------

    @app.post("/import/look")
    async def look_at_import(request: Request):
        """What this file would become, before anything is made of it. Makes nothing."""
        try:
            return intake.look(await request.body())
        except cards.BadCard as e:
            raise HTTPException(422, str(e)) from None

    @app.post("/import/card", status_code=201)
    async def import_card(request: Request):
        """A Character Card PNG, JSON or CHARX becomes a new friend. Never a merge: importing
        the same card twice makes two, which is the only safe thing to do with someone's name."""
        try:
            return cards.add(conn, await request.body())
        except cards.BadCard as e:
            raise HTTPException(422, str(e)) from None

    @app.get("/stories/{story_id}/export")
    async def export_story(
        story_id: int, as_: Literal["markdown", "jsonl"] = Query("markdown", alias="as")
    ):
        """One story as a page to read, or a line per message to keep."""
        story = story_row(story_id)
        body = (
            readable.markdown(conn, story_id)
            if as_ == "markdown"
            else readable.jsonl(conn, story_id)
        )
        kind, suffix = (
            ("text/markdown", "md") if as_ == "markdown" else ("application/x-ndjson", "jsonl")
        )
        name = readable.filename(story["title"], suffix)
        return Response(
            body.encode("utf-8"),
            media_type=f"{kind}; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{name}"'},
        )

    @app.get("/export/library")
    async def export_library():
        """The whole library as a `.kataki`: the database, the pictures and a manifest."""
        made = Path(tempfile.mkdtemp(prefix="kataki-")) / "library.kataki"
        try:
            archive.dump(conn, made)
        except BaseException:
            shutil.rmtree(made.parent, ignore_errors=True)  # nothing will come to clean it up
            raise
        return FileResponse(
            made,
            media_type="application/zip",
            filename="library.kataki",
            background=BackgroundTask(shutil.rmtree, made.parent, ignore_errors=True),
        )

    @app.post("/import/kataki", status_code=201)
    async def import_kataki(request: Request):
        """A `.kataki` poured into this library, which must be empty."""
        try:
            keep = () if host.local_routes else archive.MANAGED  # online: the service's own
            return archive.restore(conn, await request.body(), keep)
        except archive.BadArchive as e:
            raise HTTPException(422, str(e)) from None

    @app.post("/import/chat", status_code=201)
    async def import_chat(
        request: Request,
        character_id: int | None = None,
        persona_id: int | None = None,
        title: str | None = None,
    ):
        """A SillyTavern chat becomes a new story, swipes and all. Say which friends it is
        about, or the chat's own two names are made into friends."""
        for item_id in (character_id, persona_id):
            item = library.get_item(conn, item_id) if item_id is not None else None
            if item_id is not None and (item is None or item["kind"] != "character"):
                raise HTTPException(422, f"library item {item_id} is not a character")
        if character_id is not None and character_id == persona_id:
            raise HTTPException(422, "one person cannot be both sides of a chat")
        try:
            return chats.add(
                conn,
                await request.body(),
                character_id=character_id,
                persona_id=persona_id,
                title=title,
            )
        except cards.BadCard as e:
            raise HTTPException(422, str(e)) from None

    @app.post("/stories/{story_id}/lorebook", status_code=201)
    async def import_lorebook(story_id: int, request: Request):
        """A lorebook file, a World Info export, or any card that carries one, becomes facts
        this story knows: the constant entries pinned, the rest waiting on their keywords."""
        story_row(story_id)
        try:
            return lore.add(conn, story_id, lore.read(await request.body()))
        except cards.BadCard as e:
            raise HTTPException(422, str(e)) from None

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
        """Where a story stands now: its clock, who you play, where, who is there, its book."""
        book = story["book_id"] and library.get_book(conn, story["book_id"])
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
            "date": clock.date(now, story["epoch_offset_min"], moments_of(story)),
            "story_time": now,
            "minute_of_day": (now + story["epoch_offset_min"]) % clock.DAY,
            "persona": ref(story["persona_entity_id"]),
            "place": ref(scene["place_id"]) if scene else None,
            "scene_title": scene["title"] if scene else None,
            "cast": [{**dict(e), "present": e["id"] in here} for e in ai],
            # what it is filed with in Places & Plots: the plot it started from, the places it used
            "plot_id": story["scenario_id"],
            "places": [
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT lib_item_id FROM entities WHERE story_id=? AND kind='place'"
                    " AND lib_item_id IS NOT NULL ORDER BY lib_item_id",
                    (story["id"],),
                )
            ],
            "last_line": last
            and {"id": last["id"], "speaker": speaker and speaker["name"], "text": last["text"]},
            "new_events": new_events(story),
            "waiting": len(extract.pending(conn, story["id"])),
            # which book, and where in it: a book is an order, so the order travels with it
            "book": book
            and {"id": book["id"], "title": book["title"], "order": story["book_order"]},
            "tags": library.get_tags(conn, "story", story["id"]),
        }

    @app.get("/stories")
    async def list_stories(tag: str | None = None):
        """Pinned first, then the most recently played; `tag` narrows it to one shelf.
        ponytail: one path walk per story; cache per story version if a library ever holds
        hundreds of stories."""
        shelf = (
            " WHERE s.id IN (SELECT g.obj_id FROM taggings g JOIN tags t ON t.id=g.tag_id"
            " WHERE g.obj='story' AND t.name=? COLLATE NOCASE)"
            if tag is not None
            else ""
        )
        rows = conn.execute(
            "SELECT s.*, count(m.id) AS messages,"
            " coalesce(max(m.created_at), s.created_at) AS last_at, max(m.id) AS last_id"
            f" FROM stories s LEFT JOIN messages m ON m.story_id=s.id{shelf} GROUP BY s.id"
            " ORDER BY s.pinned DESC, last_at DESC, coalesce(last_id, 0) DESC, s.id DESC",
            () if tag is None else (tag,),
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
        # A friend who came from a card brings their own lorebook into the story with them,
        # which is what a character book is for wherever it was written.
        for item_id in s.character_ids:
            if book := lore.of_item(library.get_item(conn, item_id)):
                lore.add(conn, story_id, book, char=library.get_item(conn, item_id)["name"])
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
            "start_date": clock.date(0, story["epoch_offset_min"], moments_of(story)),
            "moments": overrides.get("moments", []),
            "roles": overrides.get("roles", {}),
            "ui": overrides.get("ui", {}),
            "talk": overrides.get("talk", "person"),
            **standing(story),
        }

    @app.patch("/stories/{story_id}")
    async def edit_story(story_id: int, s: StoryPatch):
        story = story_row(story_id)
        fields = s.model_dump(
            exclude_unset=True,
            exclude={"roles", "ui", "moments", "book_id", "tags", "persona_id", "talk"},
        )
        if "persona_id" in s.model_fields_set:
            fields["persona_entity_id"] = (
                None if s.persona_id is None else library.become(conn, story_id, s.persona_id)
            )
        if s.tags is not None:
            with conn:  # its own commit: a patch of tags alone writes nothing else
                library.set_tags(conn, "story", story_id, s.tags)
        if s.roles is not None or s.ui is not None or s.moments is not None or s.talk is not None:
            overrides = json.loads(story["overrides"])
            overrides |= s.model_dump(include={"roles", "ui", "moments", "talk"}, exclude_none=True)
            fields["overrides"] = json.dumps(overrides)
        if "book_id" in s.model_fields_set:
            try:
                library.set_book(conn, story_id, s.book_id)
            except ValueError as e:
                raise HTTPException(422, str(e)) from None
        _patch(conn, "stories", story_id, fields)
        return await get_story(story_id)

    # --- story links --------------------------------------------------------------------------

    @app.get("/stories/{story_id}/links")
    async def list_links(story_id: int):
        """What this story looks back at, and what looks back at it."""
        story_row(story_id)
        return library.links_of(conn, story_id)

    @app.post("/stories/{story_id}/links", status_code=201)
    async def add_link(story_id: int, link: LinkIn):
        """This story looks back at another, `offset_min` minutes later. Its characters recall
        what their other selves there would still recall by now."""
        story_row(story_id)
        try:
            library.link_stories(
                conn, story_id, link.to_story_id, link.kind, link.offset_min, link.note
            )
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        return library.links_of(conn, story_id)

    @app.delete("/links/{link_id}", status_code=204)
    async def remove_link(link_id: int):
        _row(conn, "SELECT id FROM story_links WHERE id=?", (link_id,))
        library.unlink_stories(conn, link_id)

    # --- chapters -----------------------------------------------------------------------------

    def chapter_out(story: dict, c: dict) -> dict:
        """A chapter with the clocks it runs between, for the list and the story's top bar."""
        clock_of = lambda mid: (  # noqa: E731
            (row := conn.execute("SELECT story_time FROM messages WHERE id=?", (mid,)).fetchone())
            and clock.label(row["story_time"], story["epoch_offset_min"])
        )
        return {
            **c,
            "from_clock": clock_of(c["from_message_id"]),
            "to_clock": c["ends_at"] and clock_of(c["ends_at"]),
        }

    @app.get("/stories/{story_id}/chapters")
    async def list_chapters(story_id: int):
        story = story_row(story_id)
        return [chapter_out(story, c) for c in library.chapters(conn, story_id)]

    @app.post("/stories/{story_id}/chapters", status_code=201)
    async def add_chapter(story_id: int, c: ChapterIn):
        """Start a chapter here. Whatever was running ends at the line before."""
        story = story_row(story_id)
        try:
            chapter_id = library.open_chapter(conn, story_id, c.title, c.from_message_id)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        made = next(c for c in library.chapters(conn, story_id) if c["id"] == chapter_id)
        return chapter_out(story, made)

    def chapter_row(chapter_id: int) -> dict:
        return _row(conn, "SELECT * FROM chapters WHERE id=?", (chapter_id,))

    @app.patch("/chapters/{chapter_id}")
    async def edit_chapter(chapter_id: int, c: ChapterPatch):
        row = chapter_row(chapter_id)
        story = story_row(row["story_id"])
        if c.title is not None:
            _patch(conn, "chapters", chapter_id, {"title": c.title})
        if "to_message_id" in c.model_fields_set or c.open is not None:
            library.close_chapter(conn, chapter_id, None if c.open else c.to_message_id)
        made = next(x for x in library.chapters(conn, row["story_id"]) if x["id"] == chapter_id)
        return chapter_out(story, made)

    @app.delete("/chapters/{chapter_id}", status_code=204)
    async def remove_chapter(chapter_id: int):
        chapter_row(chapter_id)
        library.delete_chapter(conn, chapter_id)

    # --- books --------------------------------------------------------------------------------

    @app.get("/tags")
    async def list_tags():
        """Every tag still in use, and how much wears it. Folders are saved views over these,
        kept in settings like any other preference."""
        return library.all_tags(conn)

    @app.get("/books")
    async def list_books():
        return library.list_books(conn)

    @app.post("/books", status_code=201)
    async def add_book(b: BookIn):
        return library.get_book(conn, library.create_book(conn, b.title, b.blurb))

    def book_row(book_id: int) -> dict:
        if (book := library.get_book(conn, book_id)) is None:
            raise HTTPException(404, "not found")
        return book

    @app.get("/books/{book_id}")
    async def get_book(book_id: int):
        return book_row(book_id)

    @app.patch("/books/{book_id}")
    async def edit_book(book_id: int, b: BookPatch):
        book_row(book_id)
        library.update_book(conn, book_id, **b.model_dump(exclude_unset=True))
        return library.get_book(conn, book_id)

    @app.delete("/books/{book_id}", status_code=204)
    async def remove_book(book_id: int):
        book_row(book_id)
        library.delete_book(conn, book_id)

    @app.post("/books/{book_id}/stories")
    async def order_book(book_id: int, o: BookOrder):
        """The order this book reads in. Stories left out keep theirs, after these."""
        book_row(book_id)
        library.order_book(conn, book_id, o.story_ids)
        return library.book_stories(conn, book_id)

    @app.post("/stories/{story_id}/seen", status_code=204)
    async def mark_seen(story_id: int):
        """The user has looked at this story: reads that have finished are no longer new. One
        still working has written nothing to look at, so it stays ahead of the mark — leaving a
        scene mid-read is the usual way out of one."""
        story_row(story_id)
        with conn:
            conn.execute(
                "UPDATE stories SET seen_run_id="
                "(SELECT coalesce(max(id), 0) FROM extraction_runs"
                " WHERE story_id=? AND status='ok') WHERE id=?",
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

    @app.get("/messages/{message_id}/mind")
    async def get_mind(message_id: int):
        """How a reply came about, for Backstage's Mind graph: only what the engine recorded."""
        got = mind.mind(conn, message_id)
        if got is None:
            raise HTTPException(404, "Only a reply has a mind to show.")
        return got

    @app.post("/messages/{message_id}/voice")
    async def voice_message(message_id: int):
        """A reply's audio (minds spec §8.3 slice 10): replayed from the cache for free, or one
        call to the voice model. Never part of a turn: no audio only means no audio."""
        try:
            return await speech.render(conn, llm, message_id, get_key)
        except speech.Refused as e:
            raise HTTPException(e.status, str(e)) from None
        except LLMError as e:
            raise failed(e) from e

    @app.get("/stories/{story_id}/feelings")
    async def get_feelings(story_id: int, who: int, about: int | None = None):
        """How one character has come to feel about another (default: you), read by read."""
        story = story_row(story_id)
        about = about if about is not None else story["persona_entity_id"]
        if about is None:
            raise HTTPException(422, "Say who the feelings are about: this story has no persona.")
        return mind.feelings(conn, story_id, who, about)

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

    @app.get("/stories/{story_id}/people")
    async def get_people(story_id: int):
        """The AI characters as they stand now: where, what they hold, what is on their mind,
        what they know about you, and how they feel about everyone."""
        return people.people(conn, story_row(story_id))

    @app.get("/stories/{story_id}/away")
    async def get_away(story_id: int):
        """While you were away: what each character's time between scenes held (minds slice 5).
        The card polls this until `done`."""
        return between.away(conn, story_row(story_id))

    @app.get("/stories/{story_id}/spend")
    async def get_spend(story_id: int):
        """What this story's model calls cost, by role and day, and a turn at each mind level
        (minds spec §8.4, track B2). No call is made."""
        story_row(story_id)
        prices = host.price_table(conn)
        return {
            **usage.spend(conn, story_id, prices),
            "per_turn": usage.per_turn(conn, story_id, prices),
        }

    @app.post("/stories/{story_id}/turn")
    async def take_turn(story_id: int, t: TurnIn):
        story_row(story_id)
        check_audience(story_id, t.audience)
        make_way(story_id)
        return stream(
            story_id,
            turns.turn(
                conn, llm, story_id, t.text, t.speaker, get_key, t.audience, t.skip, t.narrate
            ),
        )

    @app.post("/stories/{story_id}/line", status_code=201)
    async def add_line(story_id: int, line: LineIn):
        """A line with no reply (a thought, an action), or time passing. Never calls a model."""
        story_row(story_id)
        check_audience(story_id, line.audience)
        try:
            written = turns.say(conn, story_id, line.text, line.audience, line.skip, line.narrate)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        if written is None:
            raise HTTPException(422, "Say something, or let some time pass.")
        meanwhile(story_id)
        worker.poke(story_id)  # the story may now have lines worth remembering
        return messages(story_id)

    @app.post("/stories/{story_id}/regenerate")
    async def regenerate(story_id: int):
        story_row(story_id)
        make_way(story_id)
        return stream(story_id, turns.regenerate(conn, llm, story_id, get_key))

    @app.post("/messages/{message_id}/rewrite")
    async def rewrite(message_id: int, r: RewriteIn):
        """Edit a line and play on from it; the old line and what followed stay as a take."""
        m = _row(conn, "SELECT * FROM messages WHERE id=?", (message_id,))
        make_way(m["story_id"])
        return stream(
            m["story_id"], turns.rewrite(conn, llm, m["story_id"], message_id, r.text, get_key)
        )

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

    @app.post("/messages/{message_id}/rewind")
    async def rewind(message_id: int):
        """End the story at this line; what followed stays as another take (LineMenu › Rewind)."""
        m = _row(conn, "SELECT * FROM messages WHERE id=?", (message_id,))
        chat.rewind(conn, m["story_id"], message_id)
        return messages(m["story_id"])

    @app.delete("/messages/{message_id}", status_code=204)
    async def delete_line(message_id: int):
        """Delete the newest line. Any other is rewound to instead."""
        _row(conn, "SELECT id FROM messages WHERE id=?", (message_id,))
        try:
            chat.delete_newest(conn, message_id)
        except ValueError as e:
            raise HTTPException(409, str(e)) from None

    @app.post("/messages/{message_id}/branch", status_code=201)
    async def branch(message_id: int):
        """A new story, this one up to that line (LineMenu › Branch a new story from here)."""
        _row(conn, "SELECT id FROM messages WHERE id=?", (message_id,))
        return {"story_id": library.branch_story(conn, message_id)}

    @app.patch("/messages/{message_id}")
    async def edit_message(message_id: int, p: MessagePatch):
        m = _row(conn, "SELECT * FROM messages WHERE id=?", (message_id,))
        if p.text is not None:
            chat.edit_message(conn, message_id, p.text)
        if p.hidden is not None:
            _patch(conn, "messages", message_id, {"hidden": p.hidden})
        if p.skip_minutes is not None:
            chat.set_skip(conn, message_id, p.skip_minutes)
            meanwhile(m["story_id"])  # a changed skip gets its life between scenes again
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
        meanwhile(story_id)
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
            "SELECT * FROM extraction_runs WHERE story_id=? AND trigger!=? ORDER BY id DESC",
            (story_id, between.TRIGGER),  # a life between scenes read no transcript
        )
        return [run_out(r) for r in rows]

    @app.post("/runs/{run_id}/reread")
    async def reread(run_id: int, r: RereadIn):
        _row(
            conn,
            "SELECT id FROM extraction_runs WHERE id=? AND trigger!=?",
            (run_id, between.TRIGGER),
        )
        try:
            new_id = await extract.reread(conn, llm, run_id, r.role, get_key)
        except LLMError as e:  # the old reading is still there
            raise failed(e) from e
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

    @app.post("/entities/{entity_id}/adopt", status_code=201)
    async def adopt_entity(entity_id: int):
        """Someone the reader found becomes a friend in the library, and this story's copy
        becomes their first appearance."""
        _row(conn, "SELECT id FROM entities WHERE id=?", (entity_id,))
        return library.get_item(conn, library.adopt(conn, entity_id))

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

    @app.post("/reflections/{reflection_id}", status_code=201)
    async def act_on_reflection(reflection_id: int, a: ReflectionAct):
        """Peek › Growth (minds slice 8): accept, reject or lock a reflection. Append-only; the
        choice holds on every branch. -> the reflection as it now stands."""
        r = _row(conn, "SELECT * FROM reflections WHERE id=?", (reflection_id,))
        try:
            new = growth.act(conn, reflection_id, a.action)
        except LookupError as e:
            raise HTTPException(409, str(e)) from e
        story = story_row(r["story_id"])
        path = chat.active_path(conn, r["story_id"])
        names = dict(conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story["id"],)))
        row = conn.execute("SELECT * FROM reflections WHERE id=?", (new,)).fetchone()
        rows = {x["id"]: x for x in growth.live(conn, r["knower_id"], path)}
        return growth.entry(conn, growth._row(row), path, names, story["epoch_offset_min"], rows)

    @app.post("/opinions/{opinion_id}/reject")
    async def reject_grudge(opinion_id: int):
        """Peek › a grudge › Reject (§6 rule 6): struck from her ledger on every branch."""
        _row(conn, "SELECT id FROM opinions WHERE id=?", (opinion_id,))
        try:
            return {"rejected": bonds.reject(conn, opinion_id)}
        except ValueError as e:
            raise HTTPException(409, str(e)) from e

    @app.post("/memories/{memory_id}/version", status_code=201)
    async def set_version(memory_id: int, v: VersionIn):
        """Ledger › Correct (minds slice 6): the user sets this character's version of a memory,
        or (`text: null`) puts her back on the truth. Append-only; the truth row is untouched.
        -> her ledger row for it."""
        m = _row(conn, "SELECT * FROM memories WHERE id=?", (memory_id,))
        _row(
            conn,
            "SELECT id FROM entities WHERE id=? AND story_id=? AND kind='character'",
            (v.knower, m["story_id"]),
        )
        path = chat.active_path(conn, m["story_id"])
        now = path[-1]["story_time"] if path else 0
        text = (v.text or "").strip() or m["detail"]
        with conn:
            recollect.write(conn, v.knower, memory_id, "user", text, max(now, m["story_time"]))
        rows = retrieve.inspect(conn, m["story_id"], v.knower)
        return next(r for r in rows if r["memory_id"] == memory_id)

    @app.post("/memories/{memory_id}/sharpen")
    async def sharpen_memory(memory_id: int, knower: int):
        """MemoryMenu › Make it sharp again: `knower` goes over it once more, now, with the detail
        in mind — the same sharp rehearsal a successful recall leaves (activation.py)."""
        m = _row(conn, "SELECT * FROM memories WHERE id=?", (memory_id,))
        path = chat.active_path(conn, m["story_id"])
        scene = chat.scene_of(conn, m["story_id"], path)
        if scene is None:
            raise HTTPException(409, "the story has no scene yet")
        now = path[-1]["story_time"] if path else 0
        with conn:
            conn.execute(
                "INSERT INTO accesses(knower_id, memory_id, scene_id, kind, story_time, sharp, weight)"
                " VALUES(?, ?, ?, 'retold', ?, 1, 1.0)"
                " ON CONFLICT DO UPDATE SET sharp=1, weight=1.0, story_time=excluded.story_time",
                (knower, memory_id, scene, now),
            )
        return {"ok": True}

    @app.get("/stories/{story_id}/context")
    async def latest_context(story_id: int):
        """The last prompt assembled for this story: sections, recalled memories, the prompt."""
        return context_out(
            _row(conn, "SELECT * FROM context_log WHERE story_id=? ORDER BY id DESC", (story_id,))
        )

    @app.get("/messages/{message_id}/context")
    async def message_context(message_id: int):
        """The prompt a reply was written from, for Backstage at any turn."""
        return context_out(
            _row(
                conn, "SELECT * FROM context_log WHERE message_id=? ORDER BY id DESC", (message_id,)
            )
        )

    def context_out(row: dict) -> dict:
        for key in ("sections", "memories", "prompt"):
            row[key] = json.loads(row[key]) if row[key] else None
        return row

    if db_path is not None:

        @app.get("/storage", dependencies=[Depends(local_only)])
        async def storage():
            """Where the library lives on this computer, and how big it is (K10)."""

            def size(p: Path) -> int:
                if p.is_dir():
                    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                return p.stat().st_size if p.exists() else 0

            db = db_path.resolve()
            pictures = media.folder(conn)
            disk = shutil.disk_usage(db.parent)
            return {
                "places": [
                    {
                        "what": "library",
                        "path": str(db.parent),
                        "bytes": sum(size(Path(f"{db}{s}")) for s in ("", "-wal")),
                    },
                    {"what": "pictures", "path": str(pictures), "bytes": size(pictures)},
                    {
                        "what": "backups",
                        "path": str(backups.folder(db)),
                        "bytes": size(backups.folder(db)),
                    },
                ],
                # the drive the library is on (N2: "Free on C: 4 MB of 237 GB")
                "drive": db.anchor.rstrip("\\/") or "/",
                "free": disk.free,
                "total": disk.total,
            }

        @app.get("/backups", dependencies=[Depends(local_only)])
        async def list_backups():
            return backups.listing(db_path)

        @app.post("/backups", status_code=201, dependencies=[Depends(local_only)])
        async def back_up_now():
            keep = conn.execute("SELECT value FROM settings WHERE key='backups.keep'").fetchone()
            return backups.make(conn, db_path, json.loads(keep[0]) if keep else "7")

        @app.post("/backups/{name}/restore", status_code=202, dependencies=[Depends(local_only)])
        async def restore_backup(name: str):
            """Asked for now, done at the next start (the app restarts to finish)."""
            try:
                backups.request_restore(db_path, name)
            except FileNotFoundError:
                raise HTTPException(404, "no such backup") from None
            return {"restart": True}

    if web_dir is not None:
        # The app's own files carry no data, so they need no token; every API call still does.
        app.mount("/app", WebApp(directory=web_dir, html=True), name="app")

    return app
