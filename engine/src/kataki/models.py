"""The shape of one extraction, and a lenient parser for it.

References are handles, never names: `E12` an existing entity, `M31` an existing memory,
`N1..N8` an entity declared in this same output. With grammar-constrained decoding the
handles are an enum the model cannot escape; without it, a bad item is dropped with a
warning instead of failing the whole run.
"""

from typing import Literal

from pydantic import BaseModel, Field, ValidationError

EntityKind = Literal["character", "place", "item", "faction", "other"]


class NewEntity(BaseModel):
    handle: str = Field(pattern=r"^N\d+$")
    kind: EntityKind
    name: str = Field(min_length=1)
    aliases: list[str] = []
    summary: str = ""


class Participant(BaseModel):
    ref: str
    role: Literal["actor", "target", "witness", "item", "subject"]


class MemoryItem(BaseModel):
    kind: Literal["event", "fact", "claim"]
    detail: str = Field(min_length=1)  # rendered while the memory is sharp
    gist: str = Field(min_length=1)  # rendered once it has gone hazy: no names, numbers, quotes
    importance: int = Field(5, ge=1, le=10)
    emotion: str | None = None
    participants: list[Participant] = []
    place: str | None = None
    asserted_by: str | None = None  # who said it; None = narration, i.e. what really happened
    heard_by: list[str] = []
    covert: bool = False  # only the participants know
    supersedes: str | None = None
    tags: list[str] = []


class KnowledgeItem(BaseModel):  # someone learns of an EXISTING memory
    knower: str
    memory: str
    source: Literal["told", "overheard", "rumor", "inferred"]
    told_by: str | None = None


class FlagItem(BaseModel):
    entity: str
    key: str = Field(min_length=1)
    value: str | None = None  # None clears the flag
    private: bool = False


class EdgeItem(BaseModel):
    src: str
    dst: str
    rel: str = Field(min_length=1)
    note: str | None = None
    ended: bool = False


class PresenceItem(BaseModel):
    entity: str
    present: bool


class Contradiction(BaseModel):
    claim: int  # index into this output's memories[]
    contradicts: str
    hearer: str
    resolution: Literal["challenged", "doubted", "accepted"]


SECTIONS: dict[str, type[BaseModel]] = {
    "new_entities": NewEntity,
    "memories": MemoryItem,
    "knowledge": KnowledgeItem,
    "flags": FlagItem,
    "edges": EdgeItem,
    "presence": PresenceItem,
    "contradictions": Contradiction,
}


def parse_extraction(data) -> tuple[dict, list[str]]:
    """-> (sections, warnings). Invalid items become None so list indices stay meaningful.

    Raises ValueError only when the document itself is unusable.
    """
    if not isinstance(data, dict):
        raise ValueError("extraction output must be a JSON object")
    parsed: dict = {}
    warnings: list[str] = []
    for name, model in SECTIONS.items():
        raw = data.get(name) or []
        if not isinstance(raw, list):
            raise ValueError(f"'{name}' must be a list")
        parsed[name] = []
        for i, item in enumerate(raw):
            try:
                parsed[name].append(model.model_validate(item))
            except ValidationError as e:
                parsed[name].append(None)
                first = e.errors()[0]
                where = ".".join(map(str, first["loc"]))
                warnings.append(f"{name}[{i}] skipped: {where}: {first['msg']}")
    summary = data.get("scene_summary")
    parsed["scene_summary"] = summary if isinstance(summary, str) and summary.strip() else None
    parsed["skip_hint"] = data.get("skip_hint") or "none"
    return parsed, warnings
