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
    line: int | None = None  # the transcript line it happened on: decides who witnessed it


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


class Extraction(BaseModel):
    """One whole extraction; its JSON schema is what the model is constrained to."""

    new_entities: list[NewEntity] = []
    memories: list[MemoryItem] = []
    knowledge: list[KnowledgeItem] = []
    flags: list[FlagItem] = []
    edges: list[EdgeItem] = []
    presence: list[PresenceItem] = []
    contradictions: list[Contradiction] = []
    scene_summary: str | None = None
    skip_hint: Literal["none", "hours", "days", "weeks", "months", "years"] = "none"


ENTITY_REFS = {
    "Participant": ["ref"],
    "MemoryItem": ["place", "asserted_by", "heard_by"],
    "KnowledgeItem": ["knower", "told_by"],
    "FlagItem": ["entity"],
    "EdgeItem": ["src", "dst"],
    "PresenceItem": ["entity"],
    "Contradiction": ["hearer"],
}
MEMORY_REFS = {
    "KnowledgeItem": ["memory"],
    "MemoryItem": ["supersedes"],
    "Contradiction": ["contradicts"],
}


def _strings(prop: dict) -> dict:
    """The string schema inside a property: itself, an anyOf branch, or array items."""
    if prop.get("type") == "array":
        return prop["items"]
    return next((b for b in prop.get("anyOf", []) if b.get("type") == "string"), prop)


def extraction_schema(entities: list[str], memories: list[str], lines: int) -> dict:
    """The Extraction schema with every reference closed to the handles in the roster, so a
    grammar-constrained model cannot invent an id, misspell a name, or cite a missing line."""
    schema = Extraction.model_json_schema()
    defs = schema["$defs"]
    for model, fields in ENTITY_REFS.items():
        for name in fields:
            _strings(defs[model]["properties"][name])["enum"] = entities
    defs["NewEntity"]["properties"]["handle"]["enum"] = [h for h in entities if h[0] == "N"]
    for model, fields in MEMORY_REFS.items():
        for name in fields:
            prop = defs[model]["properties"][name]
            if memories:
                _strings(prop)["enum"] = memories
            elif "anyOf" in prop:
                defs[model]["properties"][name] = {"type": "null", "default": None}
    if not memories:  # sections whose items must point at an earlier memory
        schema["properties"]["knowledge"]["maxItems"] = 0
        schema["properties"]["contradictions"]["maxItems"] = 0
    line = next(
        b for b in defs["MemoryItem"]["properties"]["line"]["anyOf"] if b["type"] == "integer"
    )
    line.update(minimum=1, maximum=max(lines, 1))
    return schema


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
