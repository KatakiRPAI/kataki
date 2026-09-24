"""A character from a few words: describe someone however you like, and the memory reader's
model fills in their profile's fields. You then look it over in the editor; nothing is saved
until you do. Characters are adults, whatever the words say."""

from kataki.llm import LLM, Endpoint

FIELDS = ("name", "pronouns", "looks", "description", "secret", "example_dialogue",
          "first_message", "aliases", "tags")  # fmt: skip

SCHEMA = {
    "type": "object",
    "properties": {
        **{f: {"type": "string"} for f in FIELDS if f not in ("pronouns", "aliases", "tags")},
        "pronouns": {"type": "string", "enum": ["she", "he", "they"]},
        "aliases": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": list(FIELDS),
    "additionalProperties": False,
}

ASK = """\
You write character profiles for a roleplay app, in English. From the user's description, fill \
in every field. Keep everything they said, in their own spirit; add only what is needed, \
consistent with it. The character is an adult (18 or older).
- name: their name (invent a fitting one if none is given)
- pronouns: she, he or they
- looks: what anyone sees at a glance: appearance, clothes, an obvious role. 1-3 sentences.
- description: who they are: personality, background, what they want. Others do not know \
this unless they are told. 2-5 sentences.
- secret: something only they know and would never say out loud. One or two sentences.
- example_dialogue: three lines in their voice, one per line, each starting "Name: "
- first_message: what they say or do when a story starts, with actions in *asterisks*
- aliases: other names people call them (may be empty)
- tags: 2-5 short tags that describe them"""


def _profile(data: dict) -> dict:
    missing = [f for f in FIELDS if f not in data]
    if missing or not str(data.get("name", "")).strip():
        raise ValueError(f"missing: {', '.join(missing) or 'name'}")
    pronouns = data["pronouns"] if data["pronouns"] in ("she", "he", "they") else "they"
    listed = lambda v: [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []  # noqa: E731
    text = {f: str(data[f]).strip() for f in FIELDS if f not in ("pronouns", "aliases", "tags")}
    return {
        **text,
        "pronouns": pronouns,
        "aliases": listed(data["aliases"]),
        "tags": listed(data["tags"]),
    }


async def character(llm: LLM, ep: Endpoint, words: str) -> dict:
    """The profile the words describe, every field filled. Raises LLMError if the model can't."""
    messages = [
        {"role": "system", "content": ASK},
        {"role": "user", "content": words.strip()[:4000]},
    ]
    return await llm.complete_json(ep, messages, SCHEMA, _profile, name="character")
