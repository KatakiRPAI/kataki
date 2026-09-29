"""The side call (minds slice 2b): its schema, its parser, and the turn it runs in."""

import pytest

from kataki import after, images, inner

HANDLES = ["E3", "E4"]


def labels(**over) -> dict:
    base = {"felt": {"label": "calm", "intensity": 1, "about": None, "cause": ""},
            "events": [], "position": None, "yielded": False, "face": "neutral"}  # fmt: skip
    return base | over


def test_the_schema_closes_every_list():
    s = after.schema(HANDLES)["properties"]
    assert s["felt"]["properties"]["label"]["enum"] == list(inner.FEEL)
    assert s["events"]["items"]["properties"]["target"]["enum"] == HANDLES
    assert s["events"]["maxItems"] == 3
    assert s["face"]["enum"] == list(images.EXPRESSIONS)
    assert after.schema([])["properties"]["events"]["maxItems"] == 0


def test_good_labels_are_read_and_bad_events_dropped():
    got = after.read(
        labels(
            felt={"label": "hurt", "intensity": 3, "about": "E3", "cause": "he broke his promise"},
            events=[
                {"target": "E3", "type": "promise_broken", "intensity": 2},
                {"target": "E9", "type": "insult", "intensity": 2},  # nobody here
                {"target": "E4", "type": "hugged", "intensity": 1},  # not on the list
                {"target": "E4", "type": "insult", "intensity": True},  # not a level
                {"target": "E4", "type": ["insult"], "intensity": 1},  # not even a word
            ],
            position={"text": " won't go ", "firm": 3},
            yielded=True,
        ),
        HANDLES,
    )
    assert got["felt"] == {"label": "hurt", "intensity": 3, "about": "E3",
                           "cause": "he broke his promise"}  # fmt: skip
    assert got["events"] == [{"target": "E3", "type": "promise_broken", "intensity": 2}]
    assert got["position"] == {"text": "won't go", "firm": 3} and got["yielded"] is True


@pytest.mark.parametrize(
    "bad",
    [
        labels(felt={"label": "smug", "intensity": 1, "about": None, "cause": ""}),
        labels(felt={"label": ["hurt"], "intensity": 1, "about": None, "cause": ""}),
        labels(felt={"label": "hurt", "intensity": 5, "about": None, "cause": ""}),
        labels(face="smirk"),
        {"events": []},
    ],
)
def test_unusable_labels_are_refused(bad):
    with pytest.raises(ValueError):
        after.read(bad, HANDLES)
