import json

import httpx2
import keyring
import keyring.backend
import pytest

from kataki import after, db, embed
from kataki.llm import LLM


class MemoryKeyring(keyring.backend.KeyringBackend):
    """Tests never touch the real OS keychain."""

    priority = 1

    def __init__(self):
        super().__init__()
        self.store = {}

    def get_password(self, service, username):
        return self.store.get((service, username))

    def set_password(self, service, username, password):
        self.store[(service, username)] = password

    def delete_password(self, service, username):
        self.store.pop((service, username), None)


@pytest.fixture(autouse=True)
def memory_keyring():
    keyring.set_keyring(MemoryKeyring())


@pytest.fixture(autouse=True)
def no_builtin_embedder(monkeypatch):
    """Tests never download the built-in embedding model; the ones about it bring a fake."""
    monkeypatch.setattr(embed, "builtin", lambda: None)


_WANTED = after.wanted


@pytest.fixture(autouse=True)
def no_side_call(monkeypatch):
    """Scripted replies predate the minds side call (slice 2b): a turn makes no call after the
    reply but the old face call, unless the test asks for `side_call`."""
    monkeypatch.setattr(after, "wanted", lambda conn: False)


@pytest.fixture
def side_call(monkeypatch, no_side_call):
    monkeypatch.setattr(after, "wanted", _WANTED)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "library.db")
    yield c
    c.close()


class FakeBackend:
    """A scripted OpenAI-compatible server. Replies stream in small chunks; every request
    body is remembered. A reply is a string (content), a dict of delta fields
    (content, reasoning_content, usage), or a ready httpx2.Response."""

    def __init__(self):
        self.script: list = []
        self.requests: list[dict] = []

    def say(self, *replies):
        self.script.extend(replies)
        return self

    def __call__(self, request):
        body = json.loads(request.content) if request.content else {}
        self.requests.append(body)
        reply = self.script.pop(0)
        if isinstance(reply, httpx2.Response):
            return reply
        if isinstance(reply, str):
            reply = {"content": reply}
        chars = sum(len(m.get("content") or "") for m in body.get("messages", []))
        usage = reply.get("usage", {"prompt_tokens": chars // 4, "completion_tokens": 10})
        if not body.get("stream"):
            message = {"content": reply.get("content", "")}
            return httpx2.Response(200, json={"choices": [{"message": message}], "usage": usage})
        events = []
        if thought := reply.get("reasoning_content"):
            events.append({"choices": [{"delta": {"reasoning_content": thought}}]})
        text = reply.get("content", "")
        events += [
            {"choices": [{"delta": {"content": text[i : i + 6]}}]} for i in range(0, len(text), 6)
        ]
        events.append({"choices": [], "usage": usage})
        sse = "".join(f"data: {json.dumps(e)}\n\n" for e in events) + "data: [DONE]\n\n"
        return httpx2.Response(200, text=sse)

    @property
    def llm(self):
        return LLM(transport=httpx2.MockTransport(self))


@pytest.fixture
def backend():
    return FakeBackend()


@pytest.fixture
def local_model(conn):
    """One local endpoint serving the rp role; every other text role inherits it."""
    conn.execute("INSERT INTO providers(id, name, base_url) VALUES(1, 'local', 'http://fake/v1')")
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, 'rp-model')")
    conn.commit()
    return conn
