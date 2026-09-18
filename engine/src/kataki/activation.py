"""How well a character remembers something right now. Pure arithmetic, no DB, no LLM.

    dt_j = max(now - t_j, 10)                          story minutes
    B    = min(0, ln sum_j w_j * dt_j^-d)              ACT-R base level; recall is rehearsal
    A    = B + 3.0*(imp/10) + 1.5*S + 1.0*G + F - 2.0*superseded + noise

Two activations are kept. A_all counts every access and decides whether the memory comes
to mind at all. A_detail counts only accesses where the detail itself was present
(encoding, a detailed retelling, a successful effortful recall) and decides whether the
detail survives. Recalling a gist therefore keeps the gist alive without ever resurrecting
the detail: the detail ratchet.

Stored memories are never altered. Forgetting is what happens when this score is low.
"""

import math
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import blake2b

DECAY = 0.5  # d, the "memory sharpness" slider (0.3 crisp .. 0.8 dreamlike)
MIN_DT = 10  # story minutes; keeps a just-formed memory finite
W_IMPORTANCE, W_RELEVANCE, W_GRAPH, SUPERSEDED_PENALTY = 3.0, 1.5, 1.0, 2.0
SHARP_AT, HAZY_AT = -2.0, -4.0
# additive offset by how the character came to know it
FIDELITY = {
    "witnessed": 0.0,
    "innate": 0.0,
    "told": -0.5,
    "overheard": -0.75,
    "inferred": -1.0,
    "rumor": -1.5,
}


@dataclass(frozen=True)
class Access:
    story_time: int
    weight: float  # encode / retold 1.0, recall 0.5
    sharp: bool  # was the detail present at this access?


@dataclass(frozen=True)
class Score:
    base_all: float
    base_detail: float
    a_all: float
    a_detail: float
    tier: str | None  # "sharp" -> render detail, "hazy" -> render gist, None -> not recalled


def hash01(*parts) -> float:
    """A stable pseudo-random number in (0, 1) for these parts. Same inputs, same number."""
    digest = blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest()
    return (int.from_bytes(digest, "big") + 0.5) / 2**64


def noise(knower: int, memory: int, scene: int) -> float:
    """Small per-scene wobble: constant inside a scene, so the prompt stays cache-stable."""
    u = hash01("noise", knower, memory, scene)
    return max(-0.75, min(0.75, 0.25 * math.log(u / (1 - u))))


def base_level(accesses: Iterable[Access], now: int, d: float = DECAY) -> float:
    total = sum(a.weight * max(now - a.story_time, MIN_DT) ** -d for a in accesses)
    return min(0.0, math.log(total)) if total > 0 else -math.inf


def score(
    accesses: Iterable[Access],
    now: int,
    importance: int,
    relevance: float,  # S: fused BM25 + vector rank, 0..1
    graph: float,  # G: 1.0 shares an entity with the scene, 0.5 two hops away, else 0
    source: str = "witnessed",
    superseded: bool = False,
    noise: float = 0.0,
    d: float = DECAY,
) -> Score:
    accesses = list(accesses)
    rest = (
        W_IMPORTANCE * importance / 10
        + W_RELEVANCE * relevance
        + W_GRAPH * graph
        + FIDELITY[source]
        - SUPERSEDED_PENALTY * superseded
        + noise
    )
    base_all = base_level(accesses, now, d)
    base_detail = base_level((a for a in accesses if a.sharp), now, d)
    a_all, a_detail = base_all + rest, base_detail + rest
    tier = "sharp" if a_detail >= SHARP_AT else "hazy" if a_all >= HAZY_AT else None
    return Score(base_all, base_detail, a_all, a_detail, tier)


def effortful_recall(a_detail: float, knower: int, memory: int, scene: int) -> bool:
    """The character strains to remember a hazy detail. One fixed outcome per scene."""
    chance = 1 / (1 + math.exp(-(a_detail - SHARP_AT)))
    return hash01("effort", knower, memory, scene) < chance
