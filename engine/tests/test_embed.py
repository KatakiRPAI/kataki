"""Meaning-based recall: optional, and never required for recall to work."""

import json

import httpx2
import pytest

from kataki import chat, embed, extract, library, retrieve, turns
from kataki.llm import LLM

pytestmark = pytest.mark.anyio

BETRAYAL = "Tobin betrayed the guild at the docks."


def concept(text: str) -> list[float]:
    """A toy embedding model: two directions, 'treachery' and everything else."""
    t = text.lower()
    return [1.0, 0.0] if ("betray" in t or "treacher" in t) else [0.0, 1.0]


class Server:
    """Chat replies are fixed; embeddings come from `concept`. Every request is recorded."""

    def __init__(self):
        self.embedded: list[str] = []
        self.chats: list[dict] = []

    def __call__(self, request):
        body = json.loads(request.content)
        if request.url.path.endswith("/embeddings"):
            self.embedded += body["input"]
            data = [{"index": i, "embedding": concept(t)} for i, t in enumerate(body["input"])]
            return httpx2.Response(200, json={"data": data})
        self.chats.append(body)
        sse = 'data: {"choices": [{"delta": {"content": "Hm."}}]}\n\ndata: [DONE]\n\n'
        return httpx2.Response(200, text=sse)

    @property
    def llm(self):
        return LLM(transport=httpx2.MockTransport(self))


@pytest.fixture
def story(local_model):
    conn = local_model
    mira = library.create_item(conn, "character", "Mira")
    aren = library.create_item(conn, "character", "Aren")
    story = library.create_story(conn, "s", character_ids=[mira], persona_id=aren)
    ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM entities")}
    first = chat.append_message(conn, story, "user", "News from the docks.", ids["Aren"])
    last = chat.append_message(conn, story, "assistant", "Tell me.", ids["Mira"])
    data = {
        "new_entities": [{"handle": "N1", "kind": "character", "name": "Tobin"}],
        "memories": [
            {"kind": "event", "detail": BETRAYAL, "gist": "Tobin turned on the guild.",
             "importance": 8, "participants": [{"ref": "N1", "role": "actor"}]},
            {"kind": "event", "detail": "Tobin ordered an ale.", "gist": "Tobin drank.",
             "importance": 3, "participants": [{"ref": "N1", "role": "actor"}]},
        ],
    }  # fmt: skip
    extract.apply(conn, extract.open_run(conn, story, first, last, "manual"), data)
    chat.append_message(conn, story, "user", "...", ids["Aren"])
    return story


def mira(conn):
    return conn.execute("SELECT id FROM entities WHERE name='Mira'").fetchone()["id"]


def with_embedder(conn):
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('embed', 1, 'emb')")
    conn.commit()


QUESTION = "Tell me about that treachery."  # shares no word with the memory, names no one


def test_without_embeddings_a_paraphrase_finds_nothing(conn, story):
    assert retrieve.recall(conn, story, mira(conn), QUESTION, noise=False, log=False) == []


async def test_memories_get_vectors_once_and_a_paraphrase_finds_them(conn, story):
    server = Server()
    with_embedder(conn)
    assert await embed.refresh(conn, server.llm, story) == 2
    assert await embed.refresh(conn, server.llm, story) == 0  # nothing new to embed
    assert server.embedded == [BETRAYAL, "Tobin ordered an ale."]

    ranks = embed.nearest(conn, story, "emb", concept(QUESTION))
    got = retrieve.recall(
        conn, story, mira(conn), QUESTION, noise=False, log=False, vector_ranks=ranks
    )
    assert [r.text for r in got][0] == BETRAYAL


async def test_a_turn_uses_the_embedder_to_recall_by_meaning(conn, story):
    server = Server()
    with_embedder(conn)
    await embed.refresh(conn, server.llm, story)
    aren = conn.execute("SELECT id FROM entities WHERE name='Aren'").fetchone()["id"]
    later = [chat.append_message(conn, story, "user", f"Filler {i}.", aren) for i in range(5)]
    conn.execute(  # the lines the memory came from have scrolled out of the verbatim window
        "UPDATE stories SET overrides=? WHERE id=?", (json.dumps({"history_from": later[0]}), story)
    )
    await play(turns.turn(conn, server.llm, story, QUESTION, speaker=mira(conn)))
    assert QUESTION in server.embedded[-1]
    assert BETRAYAL in json.dumps(server.chats[-1]["messages"])


async def test_a_broken_embedder_never_breaks_a_turn(conn, story):
    with_embedder(conn)

    def flaky(request):
        if request.url.path.endswith("/embeddings"):
            return httpx2.Response(503, text="embedder is down")
        return httpx2.Response(
            200, text='data: {"choices": [{"delta": {"content": "Hm."}}]}\n\ndata: [DONE]\n\n'
        )

    llm = LLM(transport=httpx2.MockTransport(flaky))
    events = await play(turns.turn(conn, llm, story, QUESTION, speaker=mira(conn)))
    assert events[-1][0] == "done"
    assert await embed.refresh(conn, llm, story) == 0


async def play(stream):
    return [event async for event in stream]
