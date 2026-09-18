"""Recall by meaning: a vector per memory, and a nearest-neighbour search.

Optional. With no `embed` model set, recall still works on words and the graph; with one,
"that treachery" can find "Tobin betrayed the guild". Any OpenAI-compatible /v1/embeddings
endpoint works (Ollama, llama.cpp, LM Studio...). Vectors live in SQLite as float32 blobs;
search is a brute-force cosine over one matrix per story (ponytail: fine to ~200K vectors,
sqlite-vec when a library outgrows it).
"""

import sqlite3

import numpy as np

from kataki import roles
from kataki.llm import LLM, LLMError

BATCH = 64
LIMIT = 30
_matrices: dict[tuple[int, str], tuple[tuple, np.ndarray, np.ndarray]] = {}


async def refresh(conn: sqlite3.Connection, llm: LLM, story_id: int, get_key=roles.get_key) -> int:
    """Embed every memory in the story that has no vector for the current model yet.
    Returns how many were embedded. A failing embedder is not an error: recall goes on
    without vectors and the next refresh tries again."""
    if (ep := roles.resolve(conn, "embed", story_id, get_key)) is None:
        return 0
    missing = conn.execute(
        "SELECT m.id, m.detail FROM memories m WHERE m.story_id=? AND NOT EXISTS"
        " (SELECT 1 FROM embeddings e WHERE e.memory_id=m.id AND e.model=?) ORDER BY m.id",
        (story_id, ep.model),
    ).fetchall()
    done = 0
    for start in range(0, len(missing), BATCH):
        batch = missing[start : start + BATCH]
        try:
            vectors = await llm.embed(ep, [m["detail"] for m in batch])
        except LLMError:
            break
        with conn:
            for m, vector in zip(batch, vectors, strict=True):
                v = np.asarray(vector, dtype=np.float32)
                conn.execute(
                    "INSERT OR REPLACE INTO embeddings(memory_id, model, dim, vec)"
                    " VALUES(?, ?, ?, ?)",
                    (m["id"], ep.model, v.size, v.tobytes()),
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
    if (ep := roles.resolve(conn, "embed", story_id, get_key)) is None:
        return None
    try:
        [query] = await llm.embed(ep, [text])
    except LLMError:
        return None
    return nearest(conn, story_id, ep.model, query)
