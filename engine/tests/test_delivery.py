"""The courier (minds slice 9): length and register from state, and the delivery plan."""

import re

from kataki import context, delivery

HURT = {"label": "hurt", "shows": "calm", "word": "low"}  # felt hurt, masked as calm
ANGRY = {"label": "angry", "shows": "angry", "word": "on edge"}
BUZZING = {"label": "excited", "shows": "excited", "word": "buzzing"}


def test_the_setting_is_where_the_length_starts():
    for setting in ("short", "medium", "long"):
        assert (
            delivery.style(setting, "What did you do today, then?", None, False, None)["length"]
            == setting
        )


def test_a_curt_line_a_low_mood_and_tiredness_each_shorten_it():
    line = "So what did you get up to today at the docks?"
    assert delivery.style("medium", "Hm.", None, False, None)["length"] == "short"
    assert delivery.style("medium", line, HURT, False, None)["length"] == "short"
    assert delivery.style("medium", line, None, True, None)["length"] == "short"
    assert delivery.style("medium", "Hm.", HURT, True, None)["length"] == "brief"  # at most two
    assert delivery.style("short", "Hm.", HURT, True, None)["length"] == "brief"


def test_a_long_line_lengthens_it_by_one_at_most():
    long = " ".join(["word"] * 45)
    assert delivery.style("medium", long, None, False, None)["length"] == "long"
    assert delivery.style("long", long, BUZZING, False, None)["length"] == "long"


def test_register_follows_what_she_shows_and_where_she_stands():
    line = "Hello there, how are you?"
    grudge = {"trust": -20, "closeness": -5, "grudge": {"event": "promise_broken"}}
    assert delivery.style("medium", line, HURT, False, None)["register"] == "plain"  # masked
    assert delivery.style("medium", line, ANGRY, False, None)["register"] == "clipped"
    assert delivery.style("medium", line, None, False, grudge)["register"] == "clipped"
    wary = {"trust": -12, "closeness": 0, "grudge": None}
    assert delivery.style("medium", line, None, False, wary)["register"] == "guarded"
    assert delivery.style("medium", line, BUZZING, False, None)["register"] == "animated"
    close = {"trust": 3, "closeness": 14, "grudge": None}
    assert delivery.style("medium", line, None, False, close)["register"] == "warm"


def test_the_words_replace_the_setting_and_carry_no_numbers():
    got = delivery.style("medium", "Hello there, how are you?", None, False, None)
    assert got["words"] == context.LENGTHS["medium"]  # plain: the length line only
    got = delivery.style("medium", "Hm.", ANGRY, True, None)
    assert got["length"] == "brief" and got["register"] == "clipped"
    assert delivery.REGISTER_WORDS["clipped"] in got["words"]
    assert not re.search(r"\d", got["words"])


def test_bad_inputs_never_raise():
    got = delivery.style("nonsense", None, {"shows": None}, False, {"trust": "x"})
    assert got["length"] == "medium" and got["register"] == "plain"


CHAT = "hey, you made it\nhonestly i thought you'd forgotten about tonight. the others are here already. come find us by the window?"


def _plan(text=CHAT, dial="natural", **kw):
    args = {"name": "Mira", "heard": "Hi Mira, I'm outside.", "mood": None, "tired": False,
            "weighty": False, "typo_ok": False, "seed": "1"} | kw  # fmt: skip
    return delivery.plan(text, dial, **args)


def _words(bursts):
    return " ".join(b["text"] for b in bursts if not b.get("correction")).split()


def test_prose_is_never_split_retimed_or_roughened():
    for prose in (
        '*Mira looks up from the ledger.* "You came."',
        "She looks up from the ledger and smiles.",
        "Mira looks up from the ledger and smiles.",
        "\u201cYou came,\u201d she says.",
        "_quietly_ you came",
    ):
        assert not delivery.chatty(prose, "Mira")
        got = _plan(prose, "messy", typo_ok=True)
        assert got["mode"] == "prose" and got["bursts"] == [] and got["typo"] is None
    assert delivery.chatty(CHAT, "Mira")


def test_chat_splits_on_its_lines_then_sentences_up_to_the_dials_cap():
    light = _plan(dial="light")["bursts"]
    assert [b["text"] for b in light][0] == "hey, you made it" and len(light) == 2
    natural, messy = _plan(dial="natural")["bursts"], _plan(dial="messy")["bursts"]
    assert len(natural) == 3 and len(messy) == 4
    for bursts in (light, natural, messy):
        assert _words(bursts) == CHAT.split()  # joined, the bursts are the saved text


def test_abbreviations_and_ellipses_do_not_end_a_sentence():
    text = "i saw Mr. Vey at the dock... he looked tired. anyway"
    got = delivery.split(text, 4, lines_only=False)
    assert got == ["i saw Mr. Vey at the dock... he looked tired.", "anyway"]


def test_one_short_line_is_one_burst():
    assert [b["text"] for b in _plan("ok, see you soon", "messy")["bursts"]] == ["ok, see you soon"]


def test_timing_follows_the_line_the_mood_and_the_effort_within_bounds():
    base = _plan()["bursts"]
    long_heard = _plan(heard="x" * 90)["bursts"]
    assert long_heard[0]["delay_ms"] > base[0]["delay_ms"]  # she had more to read
    assert base[-1]["typing_ms"] > base[0]["typing_ms"]  # a longer bubble takes longer to type
    low = _plan(mood={"label": "sad", "shows": "sad", "word": "low"})["bursts"]
    assert low[0]["typing_ms"] > base[0]["typing_ms"] and low[0]["delay_ms"] > base[0]["delay_ms"]
    weighty = _plan(weighty=True)["bursts"]
    assert weighty[0]["delay_ms"] > base[0]["delay_ms"]
    huge = _plan(" ".join(["word"] * 400), heard="x" * 5000, weighty=True, tired=True)["bursts"]
    for b in [*base, *huge]:
        assert 400 <= b["typing_ms"] <= delivery.TYPING_MAX
        assert 0 <= b["delay_ms"] <= delivery.DELAY_MAX


def test_a_typo_only_when_allowed_and_always_corrected():
    assert all(_plan(dial="light", typo_ok=True, seed=str(s))["typo"] is None for s in range(60))
    assert all(_plan(typo_ok=False, seed=str(s))["typo"] is None for s in range(60))
    got = [_plan(dial="messy", typo_ok=True, seed=str(s)) for s in range(60)]
    typos = [g for g in got if g["typo"]]
    assert 3 <= len(typos) <= 30  # about one in five
    for g in typos:
        wrong, right = g["typo"]["wrong"], g["typo"]["right"]
        assert wrong != right and len(right) >= 4 and right.islower() and right in CHAT
        i = next(i for i, b in enumerate(g["bursts"]) if b.get("typo"))
        assert wrong in g["bursts"][i]["text"].split() or wrong in g["bursts"][i]["text"]
        fix = g["bursts"][i + 1]
        assert fix == {**fix, "text": f"*{right}", "correction": True}
        assert sum(bool(b.get("typo")) for b in g["bursts"]) == 1
        clean = [b["text"].replace(wrong, right) for b in g["bursts"] if not b.get("correction")]
        assert " ".join(clean).split() == CHAT.split()


def test_names_and_capitalised_words_never_get_a_typo():
    text = "Tobin Harrow Vellan Calloway"
    assert all(_plan(text, "messy", typo_ok=True, seed=str(s))["typo"] is None for s in range(60))


def test_the_same_reply_always_gets_the_same_plan_and_off_gets_none():
    assert _plan(dial="messy", typo_ok=True, seed="7") == _plan(
        dial="messy", typo_ok=True, seed="7"
    )
    assert _plan(dial="off") is None
    assert _plan(dial="nonsense")["dial"] == "light"
