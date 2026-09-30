"""Turning one extraction into memory, deterministically.

The model proposes; this code decides. It decides who witnessed an event (participants plus
whoever the presence log says was in the room, or participants alone if covert), that a
character's words are a claim which can never overwrite the truth, how much a hearer
believes a contested claim, and which story time everything carries.

Every row written here carries the run id. Deleting the run cascades to all of it, so a
retry is idempotent; nothing derived is ever updated in place.
"""

import asyncio
import contextlib
import json
import re
import sqlite3

from kataki import between, chat, db, embed, knobs, library, retrieve, roles
from kataki.activation import FIDELITY
from kataki.llm import LLM, Endpoint, LLMError
from kataki.models import extraction_schema, parse_extraction

BELIEF = {"challenged": 0.1, "doubted": 0.5, "accepted": 0.9}
PRONOUNS = frozenset(
    "i me you he him she her it we us they them someone somebody anyone everybody everyone"
    " this that these those who".split()
)


def _normal(name: str) -> str:
    return re.sub(r"^(the|a|an)\s+", "", name.strip().lower())


def open_run(conn: sqlite3.Connection, story_id: int, first: int, last: int, trigger: str) -> int:
    with conn:
        return conn.execute(
            "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger)"
            " VALUES(?, ?, ?, ?)",
            (story_id, first, last, trigger),
        ).lastrowid


class _Applier:
    def __init__(self, conn: sqlite3.Connection, run: sqlite3.Row, warnings: list[str]):
        self.conn, self.run, self.warnings = conn, run, warnings
        self.story_id, self.run_id = run["story_id"], run["id"]
        end = conn.execute("SELECT * FROM messages WHERE id=?", (run["to_message_id"],)).fetchone()
        self.now, self.scene_id = end["story_time"], end["scene_id"]
        path = chat.path_to(conn, end["id"])
        # transcript line n (1-based) = the n-th visible message of the window
        self.lines = [m for m in path if m["id"] >= run["from_message_id"] and not m["hidden"]]
        characters = conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND kind='character'", (self.story_id,)
        ).fetchall()
        self.heard = {c["id"]: chat.heard_by(conn, path, c["id"]) for c in characters}
        self.new: dict[str, int] = {}
        self.live = db.live_runs(conn, self.story_id, end["id"])

    def at(self, line: int | None) -> sqlite3.Row:
        """The message a transcript line points at; the window's end when unsure."""
        if line is not None and 1 <= line <= len(self.lines):
            return self.lines[line - 1]
        return (
            self.lines[-1]
            if self.lines
            else {"id": self.run["to_message_id"], "story_time": self.now}
        )

    def there_for(self, message_id: int) -> set[int]:
        """The characters who were there when this message happened."""
        return {c for c, heard in self.heard.items() if message_id in heard}

    def entity(self, handle: str | None) -> int | None:
        """Handle -> entity id in this story, or None (the caller records the warning)."""
        if not handle:
            return None
        if handle in self.new:
            return self.new[handle]
        if re.fullmatch(r"E\d+", handle):
            row = self.conn.execute(
                "SELECT id FROM entities WHERE id=? AND story_id=?", (handle[1:], self.story_id)
            ).fetchone()
            return row["id"] if row else None
        return None

    def memory(self, handle: str | None) -> int | None:
        if not handle or not re.fullmatch(r"M\d+", handle):
            return None
        row = self.conn.execute(
            "SELECT id FROM memories WHERE id=? AND story_id=?", (handle[1:], self.story_id)
        ).fetchone()
        return row["id"] if row else None

    def is_live(self, memory_id: int) -> bool:
        """Written by the user, or by a run on this branch."""
        row = self.conn.execute("SELECT run_id FROM memories WHERE id=?", (memory_id,)).fetchone()
        return row["run_id"] is None or row["run_id"] in self.live

    def is_character(self, entity_id: int) -> bool:
        row = self.conn.execute("SELECT kind FROM entities WHERE id=?", (entity_id,)).fetchone()
        return row["kind"] == "character"

    def add_entities(self, items) -> None:
        known = self.conn.execute(
            "SELECT a.alias, e.id, e.kind FROM aliases a JOIN entities e ON e.id=a.entity_id"
            " WHERE e.story_id=?",
            (self.story_id,),
        ).fetchall()
        by_name = {(_normal(r["alias"]), r["kind"]): r["id"] for r in known}
        for item in filter(None, items):
            names = [item.name, *item.aliases]
            if _normal(item.name) in PRONOUNS:
                self.warnings.append(f"new entity '{item.name}' skipped: a pronoun, not a name")
                continue
            # Same normalised name and kind = the same thing. Bias is to under-merge: a
            # duplicate can be merged later in the inspector, a false merge cannot be undone.
            match = next(
                (by_name[k] for n in names if (k := (_normal(n), item.kind)) in by_name), None
            )
            if match is None:
                match = self.conn.execute(
                    "INSERT INTO entities(story_id, kind, name, summary, run_id)"
                    " VALUES(?, ?, ?, ?, ?)",
                    (self.story_id, item.kind, item.name, item.summary, self.run_id),
                ).lastrowid
                for alias in dict.fromkeys(names):
                    self.conn.execute(
                        "INSERT OR IGNORE INTO aliases(entity_id, alias) VALUES(?, ?)",
                        (match, alias),
                    )
                    by_name[(_normal(alias), item.kind)] = match
            self.new[item.handle] = match

    def add_memories(self, items, contradictions) -> None:
        contested: dict[int, list] = {}
        for c in filter(None, contradictions):
            contested.setdefault(c.claim, []).append(c)

        for index, item in enumerate(items):
            if item is None:
                continue
            refs = [(p.ref, p.role) for p in item.participants]
            if item.place:
                refs.append((item.place, "place"))
            links = [(self.entity(ref), role) for ref, role in refs]
            asserter = self.entity(item.asserted_by)
            if any(e is None for e, _ in links) or (item.asserted_by and asserter is None):
                self.warnings.append(f"memories[{index}] skipped: unknown reference")
                continue

            # What a character says is a claim. Only narration is truth, and only truth supersedes.
            is_claim = asserter is not None or item.kind == "claim"
            clashes = [c for c in contested.get(index, []) if self.memory(c.contradicts)]
            supersedes = None if is_claim else self.memory(item.supersedes)
            contradicted = (self.memory(c.contradicts) for c in clashes)
            contradicts = next((m for m in contradicted if self.is_live(m)), None)
            where = self.at(item.line)
            memory_id = self.conn.execute(
                "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance,"
                " emotion, is_true, asserted_by, supersedes_id, covert, tags_text, from_message_id,"
                " to_message_id, run_id, message_id, contradicts_id)"
                " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.story_id,
                    "claim" if is_claim else item.kind,
                    where["story_time"],
                    item.detail,
                    item.gist,
                    item.importance,
                    item.emotion,
                    (0 if clashes else None) if is_claim else 1,
                    asserter,
                    supersedes,
                    item.covert,
                    " ".join(item.tags),
                    self.run["from_message_id"],
                    self.run["to_message_id"],
                    self.run_id,
                    where["id"],  # the exact line; from/to above keep the run's range
                    contradicts,
                ),
            ).lastrowid
            for entity_id, role in dict.fromkeys(links):
                self.conn.execute(
                    "INSERT INTO memory_entities(memory_id, entity_id, role) VALUES(?, ?, ?)",
                    (memory_id, entity_id, role),
                )
            library.set_tags(self.conn, "memory", memory_id, item.tags)

            involved = {e for e, role in links if role in ("actor", "target", "witness")}
            audience = involved | {self.entity(ref) for ref in item.heard_by} - {None}
            if not item.covert:
                audience |= self.there_for(where["id"])
            # Only those the line reached can learn it, whatever the reader claims: a whisper
            # or a secret told while someone was away never reaches them (the asserter is
            # added below, since they know what they said).
            audience &= self.there_for(where["id"])
            belief = {self.entity(c.hearer): BELIEF[c.resolution] for c in clashes}
            when = where["story_time"]
            for knower in sorted(e for e in audience if e != asserter and self.is_character(e)):
                if is_claim:
                    doubt = belief.get(knower, BELIEF["accepted"])
                    if not knobs.can_doubt(self.conn, knower):  # they take it as said
                        doubt = BELIEF["accepted"]
                    self.know(knower, memory_id, "told", asserter, doubt, when)
                else:
                    self.know(knower, memory_id, "witnessed", when=when)
                if contradicts is not None:
                    self.doubt(knower, contradicts, doubt if is_claim else 1.0)
            if asserter is not None:
                self.know(asserter, memory_id, "witnessed", when=when)  # they know what they said

    def doubt(self, knower: int, claim_id: int, believed: float) -> None:
        """Suspicion (minds slice 4): someone who believes what contradicts another's claim
        believes that claim less (never more), as much as they believe the contradiction. A new
        row on this run, with how they came to know the claim kept."""
        claim = self.conn.execute(
            "SELECT kind, asserted_by FROM memories WHERE id=?", (claim_id,)
        ).fetchone()
        if claim["kind"] != "claim" or claim["asserted_by"] == knower:
            return
        where, args = db.live_filter(self.live)
        held = self.conn.execute(
            f"SELECT * FROM knowledge WHERE knower_id=? AND memory_id=? AND {where}"
            " ORDER BY id DESC LIMIT 1",
            [knower, claim_id, *args],
        ).fetchone()
        belief = max(BELIEF["challenged"], round(1 - believed, 2))
        if held is not None and belief < held["belief"]:
            self.know(
                knower, claim_id, held["source"], held["told_by_id"], belief,
                held["learned_story_time"],
            )  # fmt: skip

    def know(self, knower, memory_id, source, told_by=None, belief=1.0, when=None) -> None:
        self.conn.execute(
            "INSERT INTO knowledge(knower_id, memory_id, source, told_by_id, learned_story_time,"
            " fidelity, belief, run_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (
                knower,
                memory_id,
                source,
                told_by,
                self.now if when is None else when,
                FIDELITY[source],
                belief,
                self.run_id,
            ),
        )

    def add_state(self, parsed) -> None:
        for i, k in enumerate(parsed["knowledge"]):
            if k is None:
                continue
            knower, memory_id = self.entity(k.knower), self.memory(k.memory)
            if knower is None or memory_id is None:
                self.warnings.append(f"knowledge[{i}] skipped: unknown reference")
                continue
            self.know(knower, memory_id, k.source, self.entity(k.told_by))
        for i, f in enumerate(parsed["flags"]):
            if f is None:
                continue
            if (entity_id := self.entity(f.entity)) is None:
                self.warnings.append(f"flags[{i}] skipped: unknown reference")
                continue
            self.conn.execute(
                "INSERT INTO flags(entity_id, key, value, story_time, private, run_id)"
                " VALUES(?, ?, ?, ?, ?, ?)",
                (entity_id, f.key, f.value, self.now, f.private, self.run_id),
            )
        for i, e in enumerate(parsed["edges"]):
            if e is None:
                continue
            src, dst = self.entity(e.src), self.entity(e.dst)
            if src is None or dst is None:
                self.warnings.append(f"edges[{i}] skipped: unknown reference")
                continue
            self.conn.execute(
                "INSERT INTO edges(story_id, src_id, dst_id, rel, note, story_time, ended, run_id)"
                " VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (self.story_id, src, dst, e.rel, e.note, self.now, e.ended, self.run_id),
            )
        for i, p in enumerate(parsed["presence"]):
            if p is None:
                continue
            if (entity_id := self.entity(p.entity)) is None:
                self.warnings.append(f"presence[{i}] skipped: unknown reference")
                continue
            self.conn.execute(
                "INSERT INTO presence(scene_id, entity_id, message_id, present, run_id)"
                " VALUES(?, ?, ?, ?, ?)",
                (self.scene_id, entity_id, self.run["to_message_id"], p.present, self.run_id),
            )
        if parsed["scene_summary"]:
            self.conn.execute(
                "INSERT INTO summaries(story_id, scene_id, to_message_id, story_time, text, run_id)"
                " VALUES(?, ?, ?, ?, ?, ?)",
                (
                    self.story_id,
                    self.scene_id,
                    self.run["to_message_id"],
                    self.now,
                    parsed["scene_summary"],
                    self.run_id,
                ),
            )


def apply(conn: sqlite3.Connection, run_id: int, data) -> list[str]:
    """Apply one extraction in ONE transaction. Returns the warnings for skipped items."""
    run = conn.execute("SELECT * FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
    try:
        parsed, warnings = parse_extraction(data)
    except ValueError as e:
        with conn:
            conn.execute(
                "UPDATE extraction_runs SET status='failed', error=?, finished_at=CURRENT_TIMESTAMP"
                " WHERE id=?",
                (str(e), run_id),
            )
        raise
    with conn:
        applier = _Applier(conn, run, warnings)
        applier.add_entities(parsed["new_entities"])
        applier.add_memories(parsed["memories"], parsed["contradictions"])
        applier.add_state(parsed)
        conn.execute(
            "UPDATE extraction_runs SET status='ok', raw=?, warnings=?,"
            " finished_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(data), json.dumps(warnings), run_id),
        )
    return warnings


# --- the pipeline: what to read, when, with which model --------------------------------------

CADENCE = 10  # lines waiting before a run is due (about five exchanges)
MAX_WINDOW = 12  # lines a single run reads; small models lose the thread beyond this
MAX_ATTEMPTS = 3  # automatic tries per window; after that it waits for the user
MAX_ROSTER, MAX_MEMORIES = 40, 20

INSTRUCTIONS = """\
You keep the memory of an ongoing story. Read the new transcript lines and record what \
matters, as JSON.

- Refer to people, places and things ONLY by handle: one from the roster (E12), or a new one \
you declare in new_entities (N1, N2, ...). Never write a name where a handle is asked for.
- new_entities: every person, place, group or notable object that matters and is not in the \
roster yet (a ledger, a ship, someone named in passing). Declare it once, then use its handle.
- Refer to earlier memories only by handle (M31).
- memories: an event (what happened), a fact (what is now true of the world), or a claim \
(what a character SAID, which may be false).
  - participants: who did it, to whom, who else took part, and any object involved. Always \
at least one.
  - Narration and shown actions are events or facts (asserted_by: null). Anything a \
character says aloud is a claim: asserted_by = the speaker, heard_by = who heard it.
  - Unspoken thoughts and feelings are private: an event with covert: true whose only \
participant is the one thinking it. Never a claim, never heard by anyone else.
  - detail: one or two specific sentences: names, numbers, exact words where they matter.
  - gist: the same thing as it is remembered years later: the main people and roughly what \
happened, without the specifics (exact places and hiding spots, numbers, minor names, quoted \
words). "Silas buried forty crowns under the mill's waterwheel" -> "Silas buried some money \
near the mill".
  - importance 1-10: 1 small talk, 5 useful, 8 life-changing, 10 unforgettable.
  - line: the transcript line where it happened.
  - covert: true if only the participants could know (a whisper, a hidden act).
  - supersedes: an earlier memory this replaces because the world changed.
- knowledge: someone learns about an EARLIER memory by being told, overhearing, rumour, or \
working it out.
- contradictions: a claim here that contradicts an earlier memory ("claim" = its index in \
memories), and how the hearer took it: challenged, doubted, or accepted.
- flags: visible state that changed (injured, holding, wearing, mood...). value null clears \
it. private: only that character knows.
- edges: relationships that formed or changed (distrusts, owes, loves, works for...).
- presence: someone arrived (true) or left (false).
- scene_summary: only if the scene clearly ended. Two sentences.
- skip_hint: if time passed without the text saying how much.
Record only what the transcript shows. Empty lists are fine."""


def pending(conn: sqlite3.Connection, story_id: int) -> list[sqlite3.Row]:
    """Lines on the active branch no live run has read yet. The newest reply waits until the
    user answers it: an answer is acceptance, so an ordinary swipe never touches memory."""
    path = chat.active_path(conn, story_id)
    live = sorted(db.live_runs(conn, story_id))
    ends = conn.execute(
        f"SELECT to_message_id FROM extraction_runs WHERE trigger!='between'"
        f" AND id IN ({','.join('?' * len(live))})",
        live,
    )
    covered = max((r[0] for r in ends), default=0)  # ids grow along a path
    todo = [m for m in path if m["id"] > covered and not m["hidden"]]
    if todo and todo[-1]["role"] == "assistant":
        todo.pop()
    return todo


def plan(todo: list, history_from: int = 0, manual: bool = False) -> tuple[list, str | None]:
    """Which lines to read now, and why; ([], None) when nothing is due yet."""
    if not todo:
        return [], None
    first = todo[0]
    end = next(
        (
            i
            for i, m in enumerate(todo[1:], 1)
            if m["skip_minutes"] or m["scene_id"] != first["scene_id"]
        ),
        len(todo),
    )
    chunk = todo[: min(end, MAX_WINDOW)]
    if end < len(todo) and end <= MAX_WINDOW:  # a time skip or a new scene closes the stretch
        return chunk, "skip" if todo[end]["skip_minutes"] else "scene"
    if len(todo) >= CADENCE:
        return chunk, "cadence"
    if first["id"] < history_from:  # about to scroll out of the verbatim window
        return chunk, "evict"
    return (chunk, "manual") if manual else ([], None)


def roster(conn: sqlite3.Connection, story_id: int, chunk: list) -> tuple[list[str], list[str]]:
    """The handles the model may use: who is here, speaking or named, and the memories in play."""
    path = chat.path_to(conn, chunk[-1]["id"]) if chunk else chat.active_path(conn, story_id)
    scene_id = chat.scene_of(conn, story_id, path)
    scene = conn.execute("SELECT place_id FROM scenes WHERE id IS ?", (scene_id,)).fetchone()
    live = db.live_runs(conn, story_id, path[-1]["id"] if path else None)
    live_sql, live_args = db.live_filter(live, "m.run_id")

    ids = [m["speaker_id"] for m in chunk if m["speaker_id"]]
    ids += [e["id"] for e in chat.present_entities(conn, scene_id, path)]
    ids += sorted(retrieve.mentioned(conn, story_id, "\n".join(m["text"] for m in chunk)))
    if scene and scene["place_id"]:
        ids.append(scene["place_id"])
    focus = list(dict.fromkeys(ids))
    memories = []
    if focus:
        memories = conn.execute(
            "SELECT DISTINCT m.* FROM memories m JOIN memory_entities me ON me.memory_id=m.id"
            f" WHERE m.story_id=? AND m.hidden=0 AND {live_sql}"
            " AND m.tags_text NOT LIKE '%offscreen%'"  # a life between scenes is not transcript
            f" AND me.entity_id IN ({','.join('?' * len(focus))}) ORDER BY m.id DESC LIMIT ?",
            [story_id, *live_args, *focus, MAX_MEMORIES],
        ).fetchall()
        for m in memories:  # everyone those memories involve, so the model can refer to them
            involved = conn.execute(
                "SELECT entity_id FROM memory_entities WHERE memory_id=?", (m["id"],)
            )
            focus += [r[0] for r in involved]
    entity_lines = []
    for entity_id in list(dict.fromkeys(focus))[:MAX_ROSTER]:
        e = conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
        aliases = [
            r["alias"]
            for r in conn.execute("SELECT alias FROM aliases WHERE entity_id=?", (entity_id,))
            if r["alias"].lower() != e["name"].lower()
        ][:3]
        line = f"E{e['id']} {e['name']} ({e['kind']})"
        line += f" aka {', '.join(aliases)}" if aliases else ""
        entity_lines.append(line + (f" - {e['summary']}" if e["summary"] else ""))
    memory_lines = [f"M{m['id']} [{m['kind']}] {m['detail'][:160]}" for m in reversed(memories)]
    return entity_lines, memory_lines


def prompt(conn: sqlite3.Connection, story_id: int, chunk: list) -> tuple[list[dict], dict]:
    """The messages and the handle-closed JSON schema for reading this chunk."""
    entity_lines, memory_lines = roster(conn, story_id, chunk)
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
    new = [f"N{i}" for i in range(1, 9)]

    def how(m) -> str:  # who a line reached, when it wasn't everyone there
        audience = chat.audience_of(m)
        if audience is None:
            return ""
        if not audience:
            return " (thinking; no one hears)"
        return f" (whispering to {' and '.join(names.get(i, 'someone') for i in audience)})"

    transcript = "\n".join(
        f"[{i}] {names.get(m['speaker_id'], 'Narration')}{how(m)}: {m['text']}"
        for i, m in enumerate(chunk, 1)
    )
    body = "Roster:\n" + "\n".join(entity_lines)
    body += f"\nNew handles you may declare: {', '.join(new)}"
    if memory_lines:
        body += "\n\nEarlier memories:\n" + "\n".join(memory_lines)
    body += "\n\nTranscript:\n" + transcript
    messages = [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": body}]
    handles = [line.split()[0] for line in entity_lines] + new
    memories = [line.split()[0] for line in memory_lines]
    return messages, extraction_schema(handles, memories, len(chunk))


def _check_document(data):
    parse_extraction(data)  # raises only when the whole document is unusable
    return data


async def read(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    chunk: list,
    trigger: str,
    role: str,
    ep: Endpoint,
    attempts: int = 0,
) -> int:
    """Read one chunk with one model call and apply it. Returns the run id, whatever happened."""
    run_id = open_run(conn, story_id, chunk[0]["id"], chunk[-1]["id"], trigger)
    with conn:
        conn.execute(
            "UPDATE extraction_runs SET status='running', role=?, model=?, attempts=?,"
            " started_at=CURRENT_TIMESTAMP WHERE id=?",
            (role, ep.model, attempts + 1, run_id),
        )
    messages, schema = prompt(conn, story_id, chunk)
    try:
        data = await llm.complete_json(ep, messages, schema, _check_document, "story_memory")
    except LLMError as e:
        with conn:
            conn.execute(
                "UPDATE extraction_runs SET status='failed', error=?,"
                " finished_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(e), run_id),
            )
        return run_id
    except asyncio.CancelledError:
        db.discard_run(conn, run_id)  # stopped to make way for a reply: no trace, retried later
        raise
    if conn.execute("SELECT 1 FROM extraction_runs WHERE id=?", (run_id,)).fetchone() is None:
        return run_id  # another reader took this window over while the model was busy
    with contextlib.suppress(ValueError):  # apply() has already marked the run failed
        apply(conn, run_id, data)
    return run_id


def due(
    conn: sqlite3.Connection, story_id: int, get_key=roles.get_key, manual: bool = False
) -> tuple[list, str, str, Endpoint, int] | None:
    """The next read to do: (chunk, trigger, role, endpoint, attempts so far), or None."""
    story = conn.execute("SELECT overrides FROM stories WHERE id=?", (story_id,)).fetchone()
    history_from = json.loads(story["overrides"]).get("history_from", 0)
    chunk, trigger = plan(pending(conn, story_id), history_from, manual)
    if not chunk:
        return None
    role = "reasoning" if trigger == "scene" else "utility"  # a closing scene gets the careful read
    if (ep := roles.resolve(conn, role, story_id, get_key)) is None:
        return None
    unfinished = conn.execute(
        "SELECT id, attempts FROM extraction_runs"
        " WHERE story_id=? AND from_message_id=? AND status!='ok'",
        (story_id, chunk[0]["id"]),
    ).fetchall()
    attempts = max((r["attempts"] for r in unfinished), default=0)
    if attempts >= MAX_ATTEMPTS and not manual:
        return None
    for r in unfinished:
        db.discard_run(conn, r["id"])
    return chunk, trigger, role, ep, attempts


async def run_due(
    conn: sqlite3.Connection,
    llm: LLM,
    story_id: int,
    get_key=roles.get_key,
    manual: bool = False,
) -> int | None:
    """Do the next due read, if any. Returns its run id."""
    if job := due(conn, story_id, get_key, manual):
        chunk, trigger, role, ep, attempts = job
        run_id = await read(conn, llm, story_id, chunk, trigger, role, ep, attempts)
        await embed.refresh(conn, llm, story_id, get_key)
        return run_id
    return None


async def reread(
    conn: sqlite3.Connection,
    llm: LLM,
    run_id: int,
    role: str = "reasoning",
    get_key=roles.get_key,
) -> int | None:
    """Read a run's window again: it went stale, or deserves a stronger model.

    What the old run filed stays until the new read has succeeded; a failed model call
    raises LLMError and changes nothing."""
    run = conn.execute("SELECT * FROM extraction_runs WHERE id=?", (run_id,)).fetchone()
    if run is None or (ep := roles.resolve(conn, role, run["story_id"], get_key)) is None:
        return None
    story_id = run["story_id"]
    path = chat.path_to(conn, run["to_message_id"])
    chunk = [m for m in path if m["id"] >= run["from_message_id"] and not m["hidden"]]
    if run["status"] != "ok":  # it filed nothing, so there is nothing to keep
        db.discard_run(conn, run_id)
        return await read(conn, llm, story_id, chunk, run["trigger"], role, ep)
    conn.execute("SAVEPOINT peek")  # the prompt sees the story as if the old run were gone
    try:
        db.delete_run(conn, run_id)
        messages, schema = prompt(conn, story_id, chunk)
    finally:
        conn.execute("ROLLBACK TO peek")
        conn.execute("RELEASE peek")
    data = await llm.complete_json(ep, messages, schema, _check_document, "story_memory")
    if conn.execute("SELECT 1 FROM extraction_runs WHERE id=?", (run_id,)).fetchone() is None:
        return run_id  # gone while the model was busy (another reread, a deleted branch)
    # One transaction: the window has one run (UNIQUE), so the old one goes as the new one
    # arrives. apply()'s own `with conn` commits all of it, or its failure rolls all of it back;
    # its bad-document path can't fire here, _check_document already passed this data.
    with conn:
        db.delete_run(conn, run_id)
        new_id = conn.execute(
            "INSERT INTO extraction_runs(story_id, from_message_id, to_message_id, trigger,"
            " status, role, model, attempts, started_at)"
            " VALUES(?, ?, ?, ?, 'running', ?, ?, 1, CURRENT_TIMESTAMP)",
            (story_id, chunk[0]["id"], chunk[-1]["id"], run["trigger"], role, ep.model),
        ).lastrowid
        apply(conn, new_id, data)
    return new_id


def recover(conn: sqlite3.Connection) -> None:
    """At startup: runs that never finished leave no trace; their windows get read again."""
    unfinished = conn.execute(
        "SELECT id FROM extraction_runs WHERE status IN ('pending', 'running', 'cancelled')"
    ).fetchall()
    for r in unfinished:
        db.discard_run(conn, r["id"])


class Worker:
    """Reads the story into memory in the background, once it goes quiet after a reply.

    ponytail: one read at a time for the whole engine; a queue per story if a server ever
    hosts many busy stories at once.
    """

    def __init__(self, conn: sqlite3.Connection, llm: LLM, get_key=roles.get_key, delay=3.0):
        self.conn, self.llm, self.get_key, self.delay = conn, llm, get_key, delay
        self._task: asyncio.Task | None = None
        self._base_url: str | None = None  # set while a model call is in flight

    def poke(self, story_id: int) -> None:
        """Something happened in this story: look for due work once it has been quiet."""
        self.cancel()
        self._task = asyncio.create_task(self._work(story_id))

    def turn_started(self, story_id: int, base_url: str) -> None:
        """A reply is about to be generated. Step aside, unless we run on another endpoint."""
        if self._base_url is None or self._base_url == base_url:
            self.cancel()

    def cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()

    async def idle(self) -> None:
        if self._task:
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _work(self, story_id: int) -> None:
        await asyncio.sleep(self.delay)
        await self._between(story_id)  # first: the time-skip card is waiting for them
        while job := due(self.conn, story_id, self.get_key):
            chunk, trigger, role, ep, attempts = job
            self._base_url = ep.base_url
            try:
                run_id = await read(
                    self.conn, self.llm, story_id, chunk, trigger, role, ep, attempts
                )
            finally:
                self._base_url = None
            status = self.conn.execute(
                "SELECT status FROM extraction_runs WHERE id=?", (run_id,)
            ).fetchone()
            if status is None or status[0] != "ok":
                return  # a failing model is not hammered; the next poke tries again
            await embed.refresh(self.conn, self.llm, story_id, self.get_key)

    async def _between(self, story_id: int) -> None:
        """The diaries a skip still owes (minds slice 5), one call per character, each stepping
        aside for a reply like a memory read does."""
        for run_id, who in between.todo(self.conn, story_id):
            if (ep := roles.resolve(self.conn, "utility", story_id, self.get_key)) is None:
                between._mark(self.conn, run_id, who, "failed")  # no model: never owed forever
                continue
            self._base_url = ep.base_url
            try:
                await between.think(self.conn, self.llm, story_id, run_id, who, self.get_key, ep)
            finally:
                self._base_url = None
