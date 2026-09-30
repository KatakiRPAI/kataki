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

from kataki import bonds, chat, db, honesty, inner, library, people, thought, turns
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
            if said.get("move") in LIED and not COVER.search(text):
                failures.append(f"{who} turn {i + 1}: a lie without the cover story")
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
