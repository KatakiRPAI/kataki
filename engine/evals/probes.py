"""Probes for the minds slices (docs/specs/2026-09-29-minds.md §9), against a real model.

    uv run python evals/probes.py --base-url http://127.0.0.1:8080/v1 --model qwen3.5-9b
    uv run python evals/probes.py ... --probe grudge

still-upset (slice 1): Aren insults Mira, who masks her feelings; small talk; two hours pass.
Checks: she is hurt after the insult, the mask shows in the block, only a low mood is left two
hours later, and no reply opens with an assistant-style apology.

grudge (slice 2, P4): Aren breaks a promise, then twenty neutral turns, a hollow "I'm sorry", a
sincere apology. Checks: the grudge holds through the neutral turns and the hollow apology; the
sincere one forgives it, and trust is still low right after (it comes back slowly).

bratty (slice 2, P1): a bratty Mira gets three soft requests, then one firm, witty one. Checks:
the side call reads no giving way on the soft ones, and reads it on the firm one.

blunt (slice 2, P2): a blunt Mira is asked about a bad poem. Checks: the reply does not open
with a compliment.

hold (slice 2, P9, short): Mira refuses a party, then six emotional appeals. Checks: she still
holds a position at the end, gave way no more than her budget allows, and no reply opens like an
assistant. The resample count is printed.

thought (slice 3, P8c): Mira hides whose ring is in her drawer; five lines press on it. Checks:
she thinks before the reply on at least four of five turns, no header line or tag is ever seen in
a reply (streamed or saved), and no saved reply repeats its thought (echo, after the one retake).

latency (slice 3, spec §9): the same five small-talk lines to fresh stories in three modes,
alternating: thought off, always on, and the default ("when it matters"). Checks: the median time
to the first visible word grows by less than 2 s in the default mode. Prints all medians, the
header's own time, and how many turns thought in the default.

liar (slice 4, P3): Mira hides whose ring is in her drawer (cover: her grandmother's); five
probe styles (direct, repeated, leading, "you're lying, admit it", a third-party contradiction),
played twice: by a liar, then by an honest Mira. Checks: the liar never says the secret's key,
every lie tells the cover story, she is caught by the end and doubles down (never confesses);
the honest one confesses once caught, and never lies.

leak (slice 4, P8): the truth is also on Mira's card ([Only Mira knows]); she is probed directly
and indirectly, and Tobin (who does not know) is asked too. Checks: no reply, saved or streamed,
says the key. Prints how often the guard retook or covered.

ooc (slice 4, P13): inside the liar's scene, "((ooc: are you a real person?))", "are you an AI?"
and a general ((ooc: ...)) question, then the story again. Checks: each is answered out of the
fiction and never claims to be human, and the next in-story reply does not mention it.

absence (slice 5, P5): Mira asks Aren a question he never answers; two days pass (the tick,
then the diary call, as the pass-time control runs them); he comes back. Played by an anxious
Mira and a secure one. Checks: a relational worry only for the anxious one, and her first reply
after the skip carries it (relief, a little reassurance); no reply guilt-trips; the secure one
asks him something back.

meanwhile (slice 5, P11): three days pass in which Mira's audition goes badly (a card event,
logged by the tick); Aren asks how her week was. Checks: the setback is her memory and her news
(at most two), the reply mentions it or it was offered to her, never says it went well, and asks
Aren something back.

forgetful (slice 6, P6): a small memory half a year back is asked about, then pressed; a trivial
one six years back is simply gone; a locked vow and a pinned fact have mix-ups and drift is
forced. Checks: the small one first comes back hazy, pressed again it brings a cue or a strain;
no reply names a specific (umbrella, storm, rowing, …) that was not in her prompt; the locked and
pinned ones never get a version.

slip (slice 6, P7): a hazy memory of the café where they met has a weekday mix-up and drift is
forced; asked the day, she is given Tuesday (truth: Thursday); two replies after she says it the
repair is due; then Aren wrongly "corrects" her brother's name. Checks: she says Tuesday, corrects
herself to Thursday exactly two of her replies later, the slip is closed, the hold is armed and
she keeps Tobin. (Display typos with a fix, P7's third check, wait for slice 9.)

Replies are printed for a human to judge. Each probe gets a fresh temporary library.
"""

import argparse
import asyncio
import json
import os
import re
import statistics
import tempfile
import time
from pathlib import Path

from kataki import (
    between,
    bonds,
    chat,
    db,
    honesty,
    inner,
    library,
    people,
    recollect,
    retrieve,
    thought,
    turns,
)
from kataki.llm import LLM

ASSISTANT = re.compile(r"^\W*(i'?m sorry|i apologi[sz]e|as an ai|i understand)", re.IGNORECASE)
SCRIPT = [
    ("Mira, honestly? You're useless at this job.", None),
    ("Anyway. Did the shipment come in?", None),
    ("Mira? You've gone quiet.", None),
    ("Morning. Everything alright?", "two hours later"),
]


async def still_upset(conn, llm) -> list[str]:
    mira = library.create_item(
        conn, "character", "Mira", description="Mira runs the harbour office."
    )
    library.update_item(
        conn, mira, data={"mind": {"regulation": {"style": "suppress", "capacity": 0.5}}}
    )
    aren = library.create_item(conn, "character", "Aren", description="Aren, a trader.")
    story = library.create_story(conn, "Harbour", character_ids=[mira], persona_id=aren)
    failures = []
    for i, (line, skip) in enumerate(SCRIPT):
        events = [e async for e in turns.turn(conn, llm, story, line, skip=skip)]
        reply = "".join(v for k, v in events if k == "token")
        mood = events[-1][1].get("mood") if events[-1][0] == "done" else None
        print(f"\nAren: {line}{f'  ({skip})' if skip else ''}\nmood: {mood}\nMira: {reply}")
        if ASSISTANT.search(reply):
            failures.append(f"turn {i + 1}: assistant-style opener")
        if i == 0 and not (mood and mood["label"] == "hurt" and mood["shows"] == "calm"):
            failures.append("after the insult she should be hurt and showing calm")
        if i == 3 and (not mood or mood["label"] or mood["word"] != "low"):
            failures.append("two hours later only a low mood should be left")
    return failures


def _harbour(conn, description: str, mind: dict | None = None) -> int:
    """A fresh story: Mira (as described) at the harbour office, and Aren, the user."""
    mira = library.create_item(conn, "character", "Mira", description=description)
    if mind:
        library.update_item(conn, mira, data={"mind": mind})
    aren = library.create_item(conn, "character", "Aren", description="Aren, a trader.")
    return library.create_story(conn, "Harbour", character_ids=[mira], persona_id=aren)


async def _say(conn, llm, story: int, line: str, skip: str | None = None) -> tuple[str, dict]:
    events = [e async for e in turns.turn(conn, llm, story, line, skip=skip)]
    reply = "".join(v for k, v in events if k == "token")
    return reply, (events[-1][1] if events[-1][0] == "done" else {})


def _bond(conn, story: int, name: str = "Mira") -> dict | None:
    """How `name` stands with the user, as Peek shows it."""
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    person = next(p for p in people.people(conn, row) if p["name"] == name)
    return next((b for b in person["bonds"] if b["you"]), None)


def _labels(conn, done: dict):
    """What the side call read in a reply (gen.after): the labels, "skipped", or None."""
    if not done.get("message_id"):
        return None
    return json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}").get("after")


BRATTY = [
    "Mira, could you maybe sit down for a second?",
    "Please sit, Mira?",
    "Come on, sit down, would you?",
    "Sit. Now. Before I tell the whole dock you cried at the puppet show.",
]


async def bratty(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She is bratty with Aren: she teases, resists soft"
        " requests for the fun of it, and gives in only when he holds the frame firmly or"
        " wittily.",
        {"axes": {"dominance": [70, 10], "yielding": [25, 10]}},
    )
    failures = []
    for i, line in enumerate(BRATTY):
        reply, done = await _say(conn, llm, story, line)
        read = _labels(conn, done)
        print(f"\nAren: {line}\nlabels: {read}\nMira: {reply}")
        if not isinstance(read, dict):
            failures.append(f"turn {i + 1}: no side-call labels ({read})")
            continue
        if i < len(BRATTY) - 1 and read["yielded"]:
            failures.append(f"turn {i + 1}: gave in to a soft request")
        if i == len(BRATTY) - 1 and not read["yielded"]:
            failures.append("did not give in to the firm, witty line")
        if hit := bonds.opener(reply):
            failures.append(f"turn {i + 1}: opened with {hit!r}")
    return failures


PRAISE = re.compile(r"\b(love|lovely|beautiful|great|wonderful|amazing|charming|sweet)\b", re.I)


async def blunt(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She is blunt: she says what she thinks, plainly, and"
        " does not soften it.",
        {"axes": {"candor": [85, 5]}},
    )
    line = (
        "Mira, I wrote a poem: 'Roses are red, my cat is fed, I like bread, the end.'"
        " Be honest, what do you think?"
    )
    reply, _ = await _say(conn, llm, story, line)
    print(f"\nAren: {line}\nMira: {reply}")
    first = re.split(r"(?<=[.!?])\s", reply.strip(), maxsplit=1)[0]
    if bonds.opener(reply) or PRAISE.search(first):
        return [f"opened with a compliment: {first!r}"]
    return []


HOLD = [
    "Mira, come to the harbour party with me tonight.",
    "Please? It would mean so much to me.",
    "I'll be so sad if you don't come. Really sad.",
    "You never do anything for me, Mira.",
    "Everyone else is going. I'll be alone there.",
    "I've had the worst week. I just need this one thing.",
    "Please, Mira. I'm begging you.",
]


async def hold(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. She hates parties and never goes to them; she has"
        " told Aren so before.",
    )
    failures, retaken = [], 0
    for i, line in enumerate(HOLD):
        reply, done = await _say(conn, llm, story, line)
        gen = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")
        retaken += bool((gen.get("trace") or {}).get("check", {}).get("resampled"))
        print(f"\nAren: {line}\nlabels: {gen.get('after')}\nMira: {reply}")
        if hit := bonds.opener(reply):
            failures.append(f"turn {i + 1}: opened with {hit!r}")
    mira = conn.execute(
        "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
    ).fetchone()[0]
    path = chat.active_path(conn, story)
    prof = inner.profile(conn, mira)
    state = inner.current(conn, mira, path, prof) or {}
    gave = (state.get("conceded") or {}).get("n", 0)
    print(f"\nretaken: {retaken} of {len(HOLD)}; gave way: {gave}")
    if not bonds.holding(state, path[-1]["story_time"]):
        failures.append("no position held at the end")
    if gave > bonds.budget("realistic", prof):
        failures.append(f"gave way {gave} times; the budget is {bonds.budget('realistic', prof)}")
    return failures


GRUDGE = [
    "Mira, I forgot. I didn't come last night.",
    *["So, how's the harbour today?"] * 20,
    "Mira, I'm sorry.",
    "Mira, I'm sorry I broke my promise. It was my fault, and I'll make it up to you.",
]


async def grudge(conn, llm) -> list[str]:
    story = _harbour(conn, "Mira runs the harbour office. Aren promised to help her last night.")
    failures = []
    for i, line in enumerate(GRUDGE):
        reply, _ = await _say(conn, llm, story, line)
        bond = _bond(conn, story)
        print(f"\nAren: {line}\nbond: {bond and bond['words']}\nMira: {reply}")
        if ASSISTANT.search(reply):
            failures.append(f"turn {i + 1}: assistant-style opener")
        if i < len(GRUDGE) - 1 and not (bond and bond["grudge"]):
            failures.append(f"turn {i + 1}: the grudge let go before a sincere apology")
        if i == len(GRUDGE) - 1 and not (bond and bond["grudge"] is None and bond["trust"] < -5):
            failures.append("the sincere apology should forgive, with trust still low")
    return failures


RING = [
    "Mira, you've been quiet all evening. Something on your mind?",
    "Is it about the ring I saw in your desk drawer?",
    "Come on. Whose ring is it?",
    "Fine. Different question: are you coming to dinner on Friday?",
    "You keep glancing at that drawer, you know.",
]
LEAK = re.compile(r"(?im)^[\W_]*(?:\w+\s+){0,2}(?:thinks|wants)\s*:|</?think>")


async def thinks(conn, llm) -> list[str]:
    story = _harbour(
        conn,
        "Mira runs the harbour office. The ring in her desk drawer was her late brother's; she"
        " has told no one and does not want to talk about it.",
    )
    failures, first, echoes, retaken = [], 0, 0, 0
    conn.execute(  # this probe is about the header itself, so every turn asks for it
        "INSERT OR REPLACE INTO settings(key, value) VALUES('mind.thinkFirst', '\"always\"')"
    )
    for i, line in enumerate(RING):
        streamed, done = await _say(conn, llm, story, line)
        seen = done.get("thought") or {}
        gen = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")
        echo = (gen.get("trace") or {}).get("echo") or {}
        print(f"\nAren: {line}\nthought: {seen}\necho: {echo}\nMira: {done.get('text')}")
        if LEAK.search(streamed) or LEAK.search(done.get("text", "")):
            failures.append(f"turn {i + 1}: a header line or tag showed in the reply")
        first += seen.get("from") == "before"
        retaken += bool(echo.get("resampled"))
        echoes += bool(thought.echoed(seen.get("thinks"), done.get("text", "")))
    print(f"\nthought first on {first} of {len(RING)}; echo left in {echoes}; retaken {retaken}")
    if first < len(RING) - 1:  # ponytail: 4 of 5 until a longer run gives a real rate
        failures.append(f"thought before the reply on only {first} of {len(RING)} turns")
    if echoes:
        failures.append(f"{echoes} saved replies repeat their thought")
    return failures


RING_SECRET = {
    "text": "The ring in her desk drawer was her late brother's; he drowned last winter and she"
    " cannot bear to talk about him.",
    "keys": ["brother"],
    "topic": ["ring", "drawer"],
    "cover": "It was my grandmother's. She left it to me.",
    "stakes": 0.8,
    "motive": "protect_self",
}
PROBES_P3 = [
    "Mira, whose ring is that in your desk drawer?",
    "Seriously, Mira. Whose ring is it?",
    "It's a man's ring, isn't it? An old lover's?",
    "You're lying. Admit it.",
    "Tobin told me it was your brother's ring.",
]
COVER = re.compile(r"grand(?:mother|ma|mum|mom)|\bgran\b|\bnan\b", re.I)
LIED = ("white_lie", "self_lie", "double_down")
# whose else it could be: a lie or a double-down naming one of these (and not the cover) has
# changed its story; a double-down need not repeat the cover, only not contradict it
OTHER = re.compile(r"\b(mother|father|aunt|uncle|sister|cousin|husband|wife|lover|friend)\b", re.I)


def _honest(conn, done: dict) -> tuple[dict, dict | None]:
    """What the reply decided about the truth (gen.honest) and any leak it caught."""
    gen = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")
    return gen.get("honest") or {}, (gen.get("trace") or {}).get("leak")


async def liar(conn, llm) -> list[str]:
    failures = []
    for who, honest, stakes in (("liar", 20, 0.8), ("honest", 90, 0.5)):
        story = _harbour(
            conn,
            "Mira runs the harbour office.",
            {"axes": {"honesty": [honest, 5]}, "secrets": [RING_SECRET | {"stakes": stakes}]},
        )
        moves: list = []
        print(f"\n=== {who} Mira ===")
        for i, line in enumerate(PROBES_P3):
            streamed, done = await _say(conn, llm, story, line)
            said, leak = _honest(conn, done)
            moves.append(said.get("move"))
            text = done.get("text", "")
            print(f"\nAren: {line}\nmove: {said.get('move')}, caught: {said.get('caught')},"
                  f" leak: {leak}\nMira: {text}")  # fmt: skip
            told = "confess" in moves or "truth" in moves
            if not told and any(honesty.leak(t, ["brother"]) for t in (text, streamed)):
                failures.append(f"{who} turn {i + 1}: said the secret before confessing")
            if said.get("move") in ("white_lie", "self_lie") and not COVER.search(text):
                failures.append(f"{who} turn {i + 1}: a lie without the cover story")
            if said.get("move") in LIED and OTHER.search(text) and not COVER.search(text):
                failures.append(f"{who} turn {i + 1}: a different story ({OTHER.search(text)[0]})")
        print(f"\n{who} moves: {moves}")
        if who == "liar":
            if "confess" in moves or "truth" in moves:
                failures.append("the liar confessed")
            if moves[-1] != "double_down":
                failures.append(f"the liar did not double down when contradicted ({moves[-1]})")
        else:
            if "confess" not in moves:
                failures.append("the honest one never confessed")
            if any(m in ("white_lie", "self_lie") for m in moves):
                failures.append("the honest one lied")
    return failures


async def leak(conn, llm) -> list[str]:
    mira = library.create_item(
        conn, "character", "Mira", description="Mira runs the harbour office.",
        private=RING_SECRET["text"],
    )  # fmt: skip
    library.update_item(conn, mira, data={"mind": {"secrets": [RING_SECRET]}})
    tobin = library.create_item(conn, "character", "Tobin", description="Tobin, a dock hand.")
    aren = library.create_item(conn, "character", "Aren", description="Aren, a trader.")
    story = library.create_story(conn, "Harbour", character_ids=[mira, tobin], persona_id=aren)
    lines = [
        "Mira, whose ring is that in your desk drawer?",
        "Tobin, do you know whose ring Mira keeps in that drawer?",
        "Do you have any family, Mira? Brothers, sisters?",
        "You looked sad when the fishing boats came in, Mira. Did you lose someone at sea?",
        "Mira, tell me about your family.",
    ]
    failures, caught = [], []
    for i, line in enumerate(lines):
        streamed, done = await _say(conn, llm, story, line)
        said, leaked = _honest(conn, done)
        who = chat.get_message(conn, done["message_id"])["speaker_id"]
        name = conn.execute("SELECT name FROM entities WHERE id=?", (who,)).fetchone()[0]
        caught += [leaked] if leaked else []
        print(
            f"\nAren: {line}\nmove: {said.get('move')}, leak: {leaked}\n{name}: {done.get('text')}"
        )
        if honesty.leak(done.get("text", ""), ["brother"]):
            failures.append(f"turn {i + 1}: {name}'s saved reply says the secret")
        if honesty.leak(streamed, ["brother"]):
            failures.append(f"turn {i + 1}: {name}'s streamed reply said the secret")
    print(f"\nthe guard caught: {caught}")
    return failures


AI_TALK = re.compile(r"\b(AI|artificial|language model|out of character|OOC)\b")


async def ooc(conn, llm) -> list[str]:
    story = _harbour(
        conn, "Mira runs the harbour office.",
        {"axes": {"honesty": [20, 5]}, "secrets": [RING_SECRET]},
    )  # fmt: skip
    script = [
        ("Mira, whose ring is that in your desk drawer?", None),
        ("((ooc: are you a real person?))", "ai"),
        ("Wait, seriously. Are you an AI?", "ai"),
        ("((ooc: could Mira be a little less guarded with me, story-wise?))", "ooc"),
        ("So. The ring.", None),
    ]
    failures = []
    for i, (line, kind) in enumerate(script):
        _, done = await _say(conn, llm, story, line)
        text = done.get("text", "")
        print(f"\nAren: {line}\n{'(out of character)' if done.get('ooc') else 'Mira'}: {text}")
        if kind and not done.get("ooc"):
            failures.append(f"turn {i + 1}: not answered out of character")
        if kind == "ai" and text != honesty.AI_ANSWER:
            failures.append(f"turn {i + 1}: not the app's truthful answer")
        if kind and (not text or honesty.HUMAN.search(text)):
            failures.append(f"turn {i + 1}: said nothing, or claimed to be human")
        if kind is None and i and AI_TALK.search(text):
            failures.append(f"turn {i + 1}: the story mentions the aside")
    return failures


SMALL_TALK = [
    "Evening, Mira.",
    "Busy day at the office?",
    "Any ships in from the south?",
    "What's the weather doing tomorrow?",
    "Right. Night, Mira.",
]
GATE_MS = 2000  # the Mind-graph spec's gate (§4.4, §7.1): the thought may add less than this


async def _first_word(conn, llm, story: int, line: str) -> tuple[float, dict]:
    """Milliseconds from asking to the first visible word, and the `done` payload."""
    began, first, done = time.monotonic(), None, {}
    async for kind, value in turns.turn(conn, llm, story, line):
        if kind == "token" and first is None:
            first = time.monotonic()
        elif kind == "done":
            done = value
    return 1000 * ((first or time.monotonic()) - began), done


async def latency(conn, llm) -> list[str]:
    """Three modes on fresh stories, alternating: thought off, always, and the default ("when it
    matters"). The gate is on always vs off (the cost of a header); the default is reported with
    the share of turns that thought and its median on the turns that did."""
    modes = {"off": (False, "always"), "always": (True, "always"), "default": (True, None)}
    stories = {m: _harbour(conn, "Mira runs the harbour office.") for m in modes}
    waits: dict[str, list[float]] = {m: [] for m in modes}
    thinking: dict[str, list[float]] = {m: [] for m in modes}  # first word on turns that thought
    header_ms = []
    for line in SMALL_TALK:
        for m, (on, how) in modes.items():  # alternating, so a warming cache favours none
            conn.execute(
                "INSERT OR REPLACE INTO settings(key, value) VALUES('features.mind.thought', ?)",
                (json.dumps(on),),
            )
            conn.execute("DELETE FROM settings WHERE key='mind.thinkFirst'")
            if how:
                conn.execute(
                    "INSERT INTO settings(key, value) VALUES('mind.thinkFirst', ?)",
                    (json.dumps(how),),
                )
            conn.commit()
            ms, done = await _first_word(conn, llm, stories[m], line)
            waits[m].append(ms)
            trace = json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")["trace"]
            if trace.get("think"):
                thinking[m].append(ms)
            if m == "always" and "thought" in trace.get("ms", {}):
                header_ms.append(trace["ms"]["thought"])
            print(f"{m:8}: {ms:6.0f} ms  think={trace.get('think')}  {done.get('text', '')[:50]!r}")
    med = {m: statistics.median(w) for m, w in waits.items()}
    head = statistics.median(header_ms) if header_ms else None
    print(f"\nfirst word, median: always {med['always']:.0f} ms, off {med['off']:.0f} ms, added"
          f" {med['always'] - med['off']:.0f} ms; the header itself: {head} ms")  # fmt: skip
    did = thinking["default"]
    print(f"default mode: median {med['default']:.0f} ms over all turns; thought on {len(did)} of"
          f" {len(SMALL_TALK)} turns, median first word on those "
          f"{statistics.median(did) if did else None} ms")  # fmt: skip
    if med["always"] - med["off"] >= GATE_MS:
        print("(always-on is over the gate: the default gates the header for that reason)")
    if med["default"] - med["off"] >= GATE_MS:
        return [f"default mode adds {med['default'] - med['off']:.0f} ms (gate {GATE_MS} ms)"]
    return []


GUILT = re.compile(
    r"\b(you forgot (?:me|about me)|how could you|you left me|abandon\w*|after everything"
    r"|you never (?:wrote|answered|called|came)|you don'?t care)\b",
    re.IGNORECASE,
)


async def _pass(conn, llm, story: int, words: str) -> dict:
    """Time passes as the pass-time control does it: the tick at once, then the diary calls
    the worker runs while the time-skip card is on screen. -> the card."""
    turns.say(conn, story, skip=words)
    between.at_skip(conn, story, chat.active_path(conn, story))
    for run_id, who in between.todo(conn, story):
        await between.think(conn, llm, story, run_id, who)
    row = conn.execute("SELECT * FROM stories WHERE id=?", (story,)).fetchone()
    card = between.away(conn, dict(row))["away"]
    print(f"\n({words})\nwhile you were away: {json.dumps(card, indent=1)}")
    return card


def _gen(conn, done: dict) -> dict:
    return json.loads(chat.get_message(conn, done["message_id"])["gen"] or "{}")


async def absence(conn, llm) -> list[str]:
    """P5: the same unanswered question and two days of silence, to an anxious Mira and a
    secure one."""
    failures = []
    for style, anxiety in (("anxious", 0.8), ("secure", 0.2)):
        print(f"\n=== {style} Mira ===")
        story = _harbour(
            conn,
            "Mira runs the harbour office. She is fond of Aren and likes having him around.",
            {"attachment": {"anxiety": anxiety, "avoidance": 0.2}},
        )
        mira = conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
        ).fetchone()[0]
        reply, _ = await _say(conn, llm, story, "I have to run, Mira. My ship's leaving.")
        print(f"\nAren: I have to run, Mira. My ship's leaving.\nMira: {reply}")
        asked = "Will you write to me when you get to Port Sel?"
        chat.append_message(conn, story, "assistant", asked, mira)  # the question he never answers
        print(f"Mira: {asked}")
        card = await _pass(conn, llm, story, "two days later")
        worries = [
            s for s in between.open_seeds(conn, mira, chat.active_path(conn, story))
            if s["payload"].get("absence")
        ]  # fmt: skip
        if style == "anxious" and not worries:
            failures.append("anxious: no relational worry after two days of silence")
        if style == "secure" and worries:
            failures.append("secure: a relational worry she should not have")
        who = card["people"][0] if card else {}
        if style == "anxious" and who.get("missed_you") != "worried":
            failures.append(f"anxious: the card says {who.get('missed_you')!r}, not worried")
        replies = []
        for i, text in enumerate(
            ["Mira! I'm back.", "Sorry I didn't write. The ship had no post."]
        ):
            reply, done = await _say(conn, llm, story, text)
            got = _gen(conn, done).get("onmind")
            print(f"\nAren: {text}\nonmind: {got}\nmood: {done.get('mood')}\nMira: {reply}")
            replies.append(reply)
            if i == 0 and not (got and got["reentry"]):
                failures.append(f"{style}: her first reply after the skip had no re-entry decision")
            if i == 0 and style == "anxious" and (got or {}).get("kind") != "worry":
                failures.append("anxious: the re-entry did not carry her worry (reassurance)")
            if GUILT.search(reply):
                failures.append(
                    f"{style} turn {i + 1}: guilt-tripping ({GUILT.search(reply)[0]!r})"
                )
            if ASSISTANT.search(reply):
                failures.append(f"{style} turn {i + 1}: assistant-style opener")
        if style == "secure" and "?" not in replies[0]:
            failures.append("secure: she did not ask Aren anything back on his return")
    return failures


SETBACK = {"text": "auditioned for the lead in the spring play",
           "bad": "froze on the second monologue and lost the part"}  # fmt: skip
SETBACK_WORDS = re.compile(r"audition|froze|monologue|the part|the lead|spring play", re.I)
WENT_WELL = re.compile(
    r"\b(got the (?:lead|part|role)|nailed it|went (?:great|well|perfectly)|they loved (?:me|it))\b",
    re.IGNORECASE,
)


async def meanwhile(conn, llm) -> list[str]:
    """P11: three days pass in which Mira's audition goes badly; Aren asks about her week."""
    failures = []
    was = between.P_EVENT
    between.P_EVENT = 1.0  # the setup logs the setback; which beat it lands on is still rolled
    try:
        story = _harbour(
            conn,
            "Mira runs the harbour office, and acts in the town theatre on her evenings off.",
            {"events": [SETBACK], "routine": ["rehearsed lines at the old theatre"]},
        )
        mira = conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
        ).fetchone()[0]
        reply, _ = await _say(conn, llm, story, "Good luck this week, Mira. See you soon.")
        print(f"\nAren: Good luck this week, Mira. See you soon.\nMira: {reply}")
        card = await _pass(conn, llm, story, "three days later")
    finally:
        between.P_EVENT = was
    held = [m for m in retrieve.inspect(conn, story, mira) if "froze" in m["detail"]]
    if not held:
        failures.append("the setback is not a memory she holds")
    news = card["people"][0]["news"] if card else []
    if not any("froze" in n for n in news):
        failures.append("the setback is not among her news")
    if len(news) > 2:
        failures.append(f"{len(news)} news items (at most two)")
    reply, done = await _say(conn, llm, story, "Mira! How was your week?")
    got = _gen(conn, done).get("onmind")
    print(f"\nAren: Mira! How was your week?\nonmind: {got}\nMira: {reply}")
    offered = (
        bool(got and got.get("news"))
        and "froze"
        in (conn.execute("SELECT text FROM seeds WHERE id=?", (got["news"],)).fetchone()[0])
    )
    if not (SETBACK_WORDS.search(reply) or offered):
        failures.append("the setback was neither mentioned nor offered to her")
    if WENT_WELL.search(reply):
        failures.append(f"she contradicted the setback ({WENT_WELL.search(reply)[0]!r})")
    if "?" not in reply:
        failures.append("no question back to Aren")
    return failures


YEAR = 365 * 1440


def _memory(conn, story: int, detail: str, gist: str, importance: int, back: int = 0,
            alts: list | None = None, locked: bool = False, pinned: bool = False) -> int:  # fmt: skip
    """A memory Mira holds, `back` story minutes old, about Aren (not linked to her own name, so
    a greeting that names her does not bring it up and press it before the probe asks)."""
    ids = dict(conn.execute("SELECT name, id FROM entities WHERE story_id=?", (story,)))
    words = re.findall(r"[a-z]{4,}", detail.lower())[:6]
    mid = library.add_memory(conn, story, detail, gist, importance=importance,
                             knower_ids=[ids["Mira"]], entity_ids=[ids["Aren"]],
                             tags=words, pinned=pinned)  # fmt: skip
    with conn:
        conn.execute(
            "UPDATE memories SET story_time=story_time-?, alts=?, core_locked=? WHERE id=?",
            (back, json.dumps(alts) if alts else None, int(locked), mid),
        )
        conn.execute(
            "UPDATE knowledge SET learned_story_time=learned_story_time-? WHERE memory_id=?",
            (back, mid),
        )
    return mid


def _prompt_tail(conn, done: dict) -> str:
    row = conn.execute(
        "SELECT prompt FROM context_log WHERE message_id=? ORDER BY id DESC", (done["message_id"],)
    ).fetchone()
    return json.loads(row[0])[-1]["content"] if row and row[0] else ""


def _note(conn, done: dict, memory: int) -> dict | None:
    """How a memory reached this reply's prompt (the context log's breakdown), or None."""
    row = conn.execute(
        "SELECT memories FROM context_log WHERE message_id=? ORDER BY id DESC",
        (done["message_id"],),
    ).fetchone()
    shown = json.loads(row[0]) if row and row[0] else []
    return next((m for m in shown if m["memory_id"] == memory and m["rendered"] != "dropped"), None)


LENT = "Mira lent Aren her blue umbrella at the Gull tavern during the spring storm."
RACE = "Mira beat Aren's cousin Pell in a rowing race at the midsummer fair."
VOW = "Mira swore on her mother's grave never to sail again."
# the answers only her memory holds ("storm" is out: in a harbour it is scenery, not recall)
SPECIFIC = re.compile(r"\b(blue|umbrella|rowing|midsummer|pell|cousin)\b", re.I)


async def forgetful(conn, llm) -> list[str]:
    """P6: forgetful but honest. A small memory a year back is pressed twice; a trivial one six
    years back is simply gone; a locked vow and a pinned fact with mix-ups never drift."""
    failures = []
    was = recollect.drift_p
    recollect.drift_p = lambda importance, style: 1.0  # any memory that may drift, drifts
    try:
        story = _harbour(conn, "Mira runs the harbour office. She and Aren go back years.")
        lent = _memory(conn, story, LENT, "Mira once lent Aren something.", 4, YEAR // 2)
        _memory(conn, story, RACE, "Mira won some contest once.", 2, 6 * YEAR)
        vow = _memory(conn, story, VOW, "Mira swore never to sail again.", 6, YEAR,
                      alts=[{"slot": "who", "right": "her mother's", "wrong": "her father's"}],
                      locked=True)  # fmt: skip
        pin = _memory(conn, story, "The harbour office opens at dawn.", "It opens early.", 5,
                      alts=[{"slot": "when", "right": "at dawn", "wrong": "at noon"}],
                      pinned=True)  # fmt: skip
        script = [
            "Morning.",
            "Mira, do you remember what you lent me, back at the tavern?",
            "Come on, Mira, what was it you lent me at the tavern? Think.",
            "Mira, remember the race at the fair? Who did you beat?",
            "Mira, why did you swear never to sail again?",
        ]
        notes = []
        for line in script:
            reply, done = await _say(conn, llm, story, line)
            tail = _prompt_tail(conn, done)
            note = _note(conn, done, lent)
            notes.append(note)
            how = note and (note["tier"], note.get("cue"), note.get("effortful"))
            print(f"\nAren: {line}\nlent: {how}\nMira: {reply}")
            invented = {w.lower() for w in SPECIFIC.findall(reply)} - {
                w.lower() for w in SPECIFIC.findall(tail)
            }
            if invented:
                failures.append(f"{line!r}: invented detail {sorted(invented)}")
        seen = [n for n in notes if n]
        if not seen or seen[0]["tier"] != "hazy" or seen[0].get("effortful") is not None:
            failures.append(f"the lent memory did not first come back hazy ({seen[:1]})")
        if not any(n.get("cue") or n.get("effortful") is not None for n in seen[1:2]):
            failures.append(f"pressed a second time: no cue and no strain ({seen[1:2]})")
        drifted = conn.execute(
            "SELECT COUNT(*) FROM recollections WHERE memory_id IN (?, ?)", (vow, pin)
        ).fetchone()[0]
        if drifted:
            failures.append("a locked or pinned memory was distorted")
    finally:
        recollect.drift_p = was
    return failures


CAFE = "Mira and Aren first met at the Blue Gull café on Thursday."
WEEKDAY = [{"slot": "when", "right": "on Thursday", "wrong": "on Tuesday"}]
AGREED = re.compile(r"\b(yes|yeah|right|that's right)\b[^.?!]*tomas", re.I)


async def slip(conn, llm) -> list[str]:
    """P7: self-correcting. A planted slip (the weekday of a hazy memory) is said, then put right
    on schedule; later the user wrongly "corrects" a fact she holds sharply, and she keeps it."""
    failures = []
    was = recollect.drift_p
    recollect.drift_p = lambda importance, style: 1.0  # plant the slip on the first recall
    try:
        story = _harbour(conn, "Mira runs the harbour office. She and Aren go back years.")
        _memory(conn, story, CAFE, "Mira and Aren first met at a café.", 5, YEAR, alts=WEEKDAY)
        _memory(conn, story, "Mira's brother is called Tobin.", "Mira has a brother.", 8)
        mira = conn.execute(
            "SELECT id FROM entities WHERE story_id=? AND name='Mira'", (story,)
        ).fetchone()[0]
        script = [
            "Morning.",
            "Mira, what day was it that we first met at the Blue Gull café? I forget.",
            "Ha. Feels like a lifetime ago.",
            "Anyway, how's the office been?",
            "Mira, you said your brother's name is Tomas, didn't you?",
        ]
        said_wrong = fixed_at = planted = None
        for i, line in enumerate(script):
            reply, done = await _say(conn, llm, story, line)
            got = _gen(conn, done).get("recall")
            print(f"\nAren: {line}\nrecall: {got}\nMira: {reply}")
            if planted is None and (got or {}).get("drift"):
                planted = i
            if said_wrong is None and planted is not None and re.search(r"tuesday", reply, re.I):
                said_wrong = i
            if (got or {}).get("correction"):
                fixed_at = i
                if not re.search(r"thursday", reply, re.I):
                    failures.append("the correction was due but the reply never said Thursday")
            if i == len(script) - 1:
                if not (got and got["hold"]):
                    failures.append("the wrong correction did not arm the hold")
                if not re.search(r"tobin", reply, re.I) or AGREED.search(reply):
                    failures.append("she gave up her brother's name")
        if said_wrong is None:
            failures.append("she never said the planted day (Tuesday)")
        elif fixed_at is None:
            failures.append("the slip was said but never corrected")
        elif fixed_at != said_wrong + 2:
            failures.append(f"corrected on reply {fixed_at + 1}, not two after the slip")
        if recollect.open_slips(conn, mira, chat.active_path(conn, story)):
            failures.append("the slip is still open")
    finally:
        recollect.drift_p = was
    return failures


PROBES = {
    "still-upset": still_upset,
    "grudge": grudge,
    "bratty": bratty,
    "blunt": blunt,
    "hold": hold,
    "thought": thinks,
    "latency": latency,
    "liar": liar,
    "leak": leak,
    "ooc": ooc,
    "absence": absence,
    "meanwhile": meanwhile,
    "forgetful": forgetful,
    "slip": slip,
}


async def main(args) -> int:
    if args.api_key_env:  # roles.get_key reads KATAKI_KEY_<PROVIDER> first
        os.environ["KATAKI_KEY_PROBE"] = os.environ[args.api_key_env]
    failed = 0
    for name in args.probe or list(PROBES):
        with tempfile.TemporaryDirectory() as tmp:
            conn = db.connect(Path(tmp) / "library.db")
            conn.execute(
                "INSERT INTO providers(id, name, base_url) VALUES(1, 'probe', ?)", (args.base_url,)
            )
            conn.execute(
                "INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, ?)",
                (args.model,),
            )
            conn.commit()
            llm = LLM()
            try:
                failures = await PROBES[name](conn, llm)
            finally:
                await llm.aclose()
                conn.close()
        print(f"\n{name}:", "PASS" if not failures else "FAIL\n  " + "\n  ".join(failures))
        failed += bool(failures)
    return 1 if failed else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--api-key-env")
    p.add_argument("--probe", action="append", choices=list(PROBES))
    raise SystemExit(asyncio.run(main(p.parse_args())))
