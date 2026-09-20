"""A story on its way out: Markdown to read, JSONL to keep.

Both are the story as it is read — the takes it runs on, not the ones it does not. A hidden line
is still in it, struck through, because hiding a line keeps it out of the prompt and not out of
the story, which is what the app says as it does it. Neither carries the engine's own
bookkeeping: no ids, no run numbers, no generation metadata.

The text is written by a model and by the person playing, and a document is not a safe place to
put text: the first characters of a line are syntax there. So every line of every body has its
openers escaped before it goes in — a reply of `---` must not turn the name above it into a
chapter heading, and an unclosed fence must not swallow the rest of the book.
"""

import json
import re
import sqlite3
import unicodedata

from kataki import chat, clock, library

SLUG = re.compile(r"[^a-z0-9]+")
INLINE = re.compile(r"([\\`*_{}\[\]()#+\-.!~|<>])")
OPENER = re.compile(
    r"""^(?:
        \#{1,6}(?=\s|$)            # a heading
      | >                          # a quote
      | [-+*](?=\s|$)              # a list item
      | \d{1,9}[.)](?=\s|$)        # a numbered one
      | (?:-{3,}|={3,}|_{3,})\s*$  # a rule, or the underline that makes a heading
      | (?:`{3,}|~{3,})            # a fence, which would swallow everything after it
      | \|                         # a table row
    )""",
    re.VERBOSE,
)


def _body(text: str) -> str:
    """Story text, still itself — `*she turns*` is still emphasis — but unable to open a block."""
    out = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        bare = line.lstrip(" ")
        indent = line[: len(line) - len(bare)][:3]  # four spaces would be a code block
        out.append(f"{indent}\\{bare}" if OPENER.match(bare) else indent + bare)
    return "\n".join(out)


def _inline(text: str) -> str:
    """A name or a title on one line, with nothing in it that can break out of its own block."""
    return INLINE.sub(r"\\\1", " ".join(text.split()))


def _cast(conn: sqlite3.Connection, story_id: int) -> str:
    names = [
        r["name"]
        for r in conn.execute(
            "SELECT name FROM entities WHERE story_id=? AND kind='character' AND hidden=0"
            " ORDER BY id",
            (story_id,),
        )
    ]
    if len(names) < 2:
        return _inline(names[0]) if names else ""
    return f"{', '.join(_inline(n) for n in names[:-1])} and {_inline(names[-1])}"


def _premise(conn: sqlite3.Connection, story: sqlite3.Row) -> str:
    said = json.loads(story["overrides"]).get("premise")
    if said is None and story["scenario_id"]:
        row = conn.execute(
            "SELECT description FROM lib_items WHERE id=?", (story["scenario_id"],)
        ).fetchone()
        said = row and row["description"]
    return (said or "").strip()


def _read(conn: sqlite3.Connection, story_id: int) -> tuple[sqlite3.Row, list, dict, dict, dict]:
    """The story, its lines, and what marks them: who said it, where a chapter starts, and
    where a scene does."""
    story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
    if story is None:
        raise LookupError(f"no story {story_id}")
    path = chat.active_path(conn, story_id)
    names = dict(
        conn.execute("SELECT id, name FROM entities WHERE story_id=?", (story_id,)).fetchall()
    )
    starts = {c["from_message_id"]: c["title"] for c in library.chapters(conn, story_id)}
    scenes = {
        # the title where there is one, so this agrees with the marker `chat.new_scene` writes;
        # the story's own first scene never has one, so that opens with where it is
        r["id"]: (r["title"] or r["name"], r["start_story_time"])
        for r in conn.execute(
            "SELECT s.id, s.title, s.start_story_time, e.name FROM scenes s"
            " LEFT JOIN entities e ON e.id=s.place_id WHERE s.story_id=?",
            (story_id,),
        )
    }
    return story, path, names, starts, scenes


def _who(message, names: dict) -> tuple[str | None, list[str] | None, bool]:
    """(the name that said it, who it was only for, was it a thought). A story nobody plays a
    part in still has a player in it: their lines are theirs, not the world's."""
    audience = chat.audience_of(message)
    said_by = names.get(message["speaker_id"])
    if said_by is None and message["role"] == "user":
        said_by = "You"
    if audience == []:
        return said_by, None, True
    return said_by, [names.get(i, "someone") for i in audience] if audience else None, False


def markdown(conn: sqlite3.Connection, story_id: int) -> str:
    """The story as a page: its title, what it was about, its chapters and its lines."""
    story, path, names, starts, scenes = _read(conn, story_id)
    out = [f"# {_inline(story['title'])}"]
    if premise := _premise(conn, story):
        out.append("\n".join(f"> {line}" for line in _body(premise).split("\n")))
    if path and (cast := _cast(conn, story_id)):
        said = sum(1 for m in path if m["role"] != "system")
        out.append(f"*{cast} · {said} line{'' if said == 1 else 's'}*")

    opened = False
    for m in path:
        if m["id"] in starts:
            out.append(f"## {_inline(starts[m['id']])}")
        # Every later scene and every time skip writes its own marker into the story, so the
        # only one to add is where it opens — that line nobody wrote.
        if not opened and m["role"] != "system":
            opened = True
            where, began = scenes.get(m["scene_id"], (None, m["story_time"]))
            when = clock.label(began, story["epoch_offset_min"])
            out.append(f"*— {_inline(where)} · {when} —*" if where else f"*— {when} —*")
        if m["role"] == "system":
            out.append(f"*{_inline(m['text'])}*")  # the story's own marker, in its own words
            continue

        said_by, to, thought = _who(m, names)
        body = _body(m["text"])
        if m["hidden"]:  # struck through, as the app strikes it: in the story, out of the prompt
            body = "\n".join(f"~~{line}~~" if line.strip() else line for line in body.split("\n"))
        if said_by is None:
            out.append(body)  # the world narrating itself is nobody's line, so nobody is named
            continue
        aside = ""
        if thought:
            aside = " *(thinking)*"
        elif to:
            aside = f" *(whispering to {' and '.join(_inline(n) for n in to)})*"
        out.append(f"**{_inline(said_by)}**{aside}\n{body}")
    return "\n\n".join(out) + "\n"


def jsonl(conn: sqlite3.Connection, story_id: int) -> str:
    """One line per message: what was said, by whom, and when."""
    story, path, names, starts, scenes = _read(conn, story_id)
    lines = []
    scene = None
    for m in path:
        said_by, to, thought = _who(m, names)
        row = {
            "story_time": m["story_time"],
            "clock": clock.label(m["story_time"], story["epoch_offset_min"]),
            "role": m["role"],
            "speaker": names.get(m["speaker_id"]),
            "text": m["text"],
        }
        if m["id"] in starts:
            row["chapter"] = starts[m["id"]]
        if m["scene_id"] != scene:  # always, even when it is nothing: that is what moved
            scene = m["scene_id"]
            row["scene"] = scenes.get(scene, (None, 0))[0]
        if m["skip_minutes"]:
            row["skip"] = m["skip_minutes"]
        if to:
            row["to"] = to
        if thought:
            row["thought"] = True
        if m["hidden"]:
            row["hidden"] = True
        lines.append(json.dumps(row, ensure_ascii=False))
    return "".join(f"{line}\n" for line in lines)


def filename(title: str, suffix: str) -> str:
    """A story can be called anything; a file cannot. What is left of the title in plain
    letters, or `story` when nothing is."""
    plain = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = SLUG.sub("-", plain.lower()).strip("-")
    return f"{slug[:60] or 'story'}.{suffix}"
