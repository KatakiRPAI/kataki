"""Recall by meaning: a vector per memory, and a nearest-neighbour search.

With an `embed` model set, any OpenAI-compatible /v1/embeddings endpoint does the work
(Ollama, llama.cpp, LM Studio...). With none set, a small built-in model does: a static
embedding table, downloaded once from Hugging Face (125 MB) and run on the CPU in about a
millisecond, so "that treachery" can find "Tobin betrayed the guild" with no setup at all.
If neither is available, recall still works on names, words and the graph.

Vectors live in SQLite as float32 blobs; search is a brute-force cosine over one matrix per
story (ponytail: fine to ~200K vectors, sqlite-vec when a library outgrows it).
"""

import asyncio
import functools
import sqlite3
from collections.abc import Awaitable, Callable

import numpy as np

from kataki import data_dir, roles
from kataki.llm import LLM, LLMError

BUILTIN = "minishlab/potion-retrieval-32M"  # static, retrieval-tuned, 125 MB, CPU only
BUILTIN_FILES = ("model.safetensors", "tokenizer.json", "config.json")
BATCH = 64
LIMIT = 30
_matrices: dict[tuple[int, str], tuple[tuple, np.ndarray, np.ndarray]] = {}

Embed = Callable[[list[str]], Awaitable]


@functools.cache
def builtin():
    """The built-in model, loaded (and on first use downloaded) once per process; None when
    it can't be had, e.g. offline on first run. ponytail: M5's installer can ship the file.

    It goes to a plain folder, not the shared Hugging Face cache: that cache needs symlinks,
    which Windows refuses without Developer Mode."""
    folder = data_dir() / "models" / BUILTIN.split("/")[1]
    try:
        from model2vec import StaticModel

        if not all((folder / f).exists() for f in BUILTIN_FILES):
            from huggingface_hub import snapshot_download

            snapshot_download(BUILTIN, local_dir=folder, allow_patterns=["*.json", *BUILTIN_FILES])
        return StaticModel.from_pretrained(folder)
    except Exception:
        return None


async def _embedder(
    conn: sqlite3.Connection, llm: LLM, story_id: int, get_key
) -> tuple[str, Embed] | None:
    """(model name, embed function) for this story: its embed model, else the built-in one."""
    if ep := roles.resolve(conn, "embed", story_id, get_key):
        return ep.model, functools.partial(llm.embed, ep)
    if (model := await asyncio.to_thread(builtin)) is None:
        return None

    async def local(texts: list[str]):
        return model.encode(texts)

    return BUILTIN, local


async def refresh(conn: sqlite3.Connection, llm: LLM, story_id: int, get_key=roles.get_key) -> int:
    """Embed every memory in the story that has no vector for the current model yet.
    Returns how many were embedded. A failing embedder is not an error: recall goes on
    without vectors and the next refresh tries again."""
    if (embedder := await _embedder(conn, llm, story_id, get_key)) is None:
        return 0
    model, embed = embedder
    missing = conn.execute(
        "SELECT m.id, m.detail FROM memories m WHERE m.story_id=? AND NOT EXISTS"
        " (SELECT 1 FROM embeddings e WHERE e.memory_id=m.id AND e.model=?) ORDER BY m.id",
        (story_id, model),
    ).fetchall()
    done = 0
    for start in range(0, len(missing), BATCH):
        batch = missing[start : start + BATCH]
        try:
            vectors = await embed([m["detail"] for m in batch])
        except LLMError:
            break
        with conn:
            for m, vector in zip(batch, vectors, strict=True):
                v = np.asarray(vector, dtype=np.float32)
                conn.execute(
                    "INSERT OR REPLACE INTO embeddings(memory_id, model, dim, vec)"
                    " VALUES(?, ?, ?, ?)",
                    (m["id"], model, v.size, v.tobytes()),
                )
        done += len(batch)
    return done


def _matrix(conn: sqlite3.Connection, story_id: int, model: str) -> tuple[np.ndarray, np.ndarray]:
    """Memory ids and their unit vectors, rebuilt only when the story's vectors changed."""
    where = "FROM embeddings e JOIN memories m ON m.id=e.memory_id WHERE m.story_id=? AND e.model=?"
    version = tuple(
        conn.execute(f"SELECT count(*), max(e.id) {where}", (story_id, model)).fetchone()
    )
    cached = _matrices.get((story_id, model))
    if cached and cached[0] == version:
        return cached[1], cached[2]
    rows = conn.execute(f"SELECT e.memory_id, e.vec {where}", (story_id, model)).fetchall()
    if not rows:
        return np.empty(0, dtype=np.int64), np.empty((0, 0), dtype=np.float32)
    ids = np.array([r[0] for r in rows])
    matrix = np.stack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
    _matrices[(story_id, model)] = (version, ids, matrix)
    return ids, matrix


def nearest(
    conn: sqlite3.Connection, story_id: int, model: str, query: list[float], limit: int = LIMIT
) -> dict[int, int]:
    """The memories closest in meaning to the query: memory id -> rank (1 = closest)."""
    ids, matrix = _matrix(conn, story_id, model)
    if not len(ids):
        return {}
    q = np.asarray(query, dtype=np.float32)
    scores = matrix @ (q / (np.linalg.norm(q) + 1e-9))
    return {int(ids[i]): rank for rank, i in enumerate(np.argsort(-scores)[:limit], 1)}


async def ranks_for(
    conn: sqlite3.Connection, llm: LLM, story_id: int, text: str, get_key=roles.get_key
) -> dict[int, int] | None:
    """Vector ranks for this text, or None when there is no embedder or it is down."""
    if (embedder := await _embedder(conn, llm, story_id, get_key)) is None:
        return None
    model, embed = embedder
    try:
        [query] = await embed([text])
    except LLMError:
        return None
    return nearest(conn, story_id, model, query)
