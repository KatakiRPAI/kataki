"""Turning one extraction into memory, deterministically.

The model proposes; this code decides. It decides who witnessed an event (participants plus
whoever the presence log says was in the room, or participants alone if covert), that a
character's words are a claim which can never overwrite the truth, how much a hearer
believes a contested claim, and which story time everything carries.

Every row written here carries the run id. Deleting the run cascades to all of it, so a
retry is idempotent; nothing derived is ever updated in place.
"""

import json
import re
import sqlite3

from kataki import chat, library
from kataki.activation import FIDELITY
from kataki.models import parse_extraction

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
        # witnesses: the characters who were there for the window's last line
        path = chat.path_to(conn, end["id"])
        characters = conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND kind='character'", (self.story_id,)
        ).fetchall()
        self.in_room = {
            c["id"] for c in characters if end["id"] in chat.heard_by(conn, path, c["id"])
        }
        self.new: dict[str, int] = {}

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
            memory_id = self.conn.execute(
                "INSERT INTO memories(story_id, kind, story_time, detail, gist, importance,"
                " emotion, is_true, asserted_by, supersedes_id, covert, tags_text, from_message_id,"
                " to_message_id, run_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.story_id,
                    "claim" if is_claim else item.kind,
                    self.now,
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
                audience |= self.in_room
            belief = {self.entity(c.hearer): BELIEF[c.resolution] for c in clashes}
            for knower in sorted(e for e in audience if e != asserter and self.is_character(e)):
                if is_claim:
                    self.know(
                        knower, memory_id, "told", asserter, belief.get(knower, BELIEF["accepted"])
                    )
                else:
                    self.know(knower, memory_id, "witnessed")
            if asserter is not None:
                self.know(asserter, memory_id, "witnessed")  # they know what they said

    def know(self, knower, memory_id, source, told_by=None, belief=1.0) -> None:
        self.conn.execute(
            "INSERT INTO knowledge(knower_id, memory_id, source, told_by_id, learned_story_time,"
            " fidelity, belief, run_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (knower, memory_id, source, told_by, self.now, FIDELITY[source], belief, self.run_id),
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
                "INSERT INTO presence(scene_id, entity_id, message_id, present) VALUES(?, ?, ?, ?)",
                (self.scene_id, entity_id, self.run["to_message_id"], p.present),
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
