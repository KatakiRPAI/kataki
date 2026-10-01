"""What is known about a model a connection lists, for the model picker.

A server's `/v1/models` says as much as it likes: OpenRouter gives context, prices, modalities
and whether the model can think; the HuggingFace router gives the same per host; llama.cpp gives
the loaded model's size and context; most others give the id alone. What the server doesn't say
is read off the id (size, and what the model is for). Nothing here calls a model.
"""

import re

# "9B", "0.5b", "350M", "2.4T", "8x7b"; never the "A3B" of a mixture's active part, nor "4bit"
_SIZE = re.compile(r"(?<![a-z0-9.])(?:(\d+)x)?(\d+(?:\.\d+)?)([bmt])(?![a-z])", re.I)
_UNIT = {"m": 0.001, "b": 1.0, "t": 1000.0}


def _word(*names: str) -> str:
    return rf"(?:^|[-_/.:])(?:{'|'.join(names)})(?:[-_/.:]|$)"


# ponytail: names people know these by, not a registry. Add a name when a model is filed wrong;
# a server that says what a model does (modalities, reasoning) is believed over its id.
_BY_ID = {
    "embedding": re.compile(r"embed|" + _word("bge", "e5", "gte", "minilm", "nomic"), re.I),
    "image": re.compile(r"flux|stable-?diffusion|sdxl|dall-?e|imagen|" + _word("image"), re.I),
    "voice": re.compile(_word("tts", "whisper", "kokoro", "speech", "voice", "audio"), re.I),
    "roleplay": re.compile(
        _word("rp", "erp", "roleplay")
        + r"|sao10k|thedrummer|anthracite|neversleep|gryphe|mytho|stheno|euryale|lumimaid"
        r"|noromaid|magnum|rocinante|cydonia|unslop|fimbulvetr|wayfarer|mag-mell|lunaris"
        r"|hermes|dolphin|abliterated|uncensored|celeste|anubis|skyfall",
        re.I,
    ),
    "reasoning": re.compile(_word("r1", "qwq", "o[134]", "think", "thinking", "reason\\w*"), re.I),
    "small": re.compile(
        _word("mini", "small", "tiny", "nano", "lite", "flash", "haiku", "instant"), re.I
    ),
}
SMALL_B = 10  # billions of parameters: what runs fast, and fits an 8 GB card


def size_b(model_id: str) -> float | None:
    """Billions of parameters, read off a model's name; None when it doesn't say."""
    m = _SIZE.search(model_id.rsplit("/", 1)[-1])
    if not m:
        return None
    return round(int(m[1] or 1) * float(m[2]) * _UNIT[m[3].lower()], 3)


def _num(x) -> float | None:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if x >= 0 and x == x and x != float("inf") else None  # OpenRouter's -1: "it varies"


def describe(raw: dict) -> dict:
    """One listed model as the picker shows it: `id` and `kinds` always; `name`, `context`
    (tokens), `params_b`, `input` and `output` ($ per million tokens), `hosts` and `created`
    when the server says them (or, for size, the id does)."""
    mid = str(raw["id"])
    arch = raw.get("architecture") if isinstance(raw.get("architecture"), dict) else {}
    ins, outs = arch.get("input_modalities") or [], arch.get("output_modalities") or []
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}  # llama.cpp
    hosts = [h for h in raw.get("providers") or [] if isinstance(h, dict)]  # HuggingFace router
    named = {k for k, rx in _BY_ID.items() if rx.search(mid)}

    out: dict = {"id": mid}
    if isinstance(raw.get("name"), str) and raw["name"] != mid:
        out["name"] = raw["name"]
    context = max(
        (_num(x) or 0 for x in [raw.get("context_length"), meta.get("n_ctx_train")]
         + [h.get("context_length") for h in hosts]),
        default=0,
    )  # fmt: skip
    if context:
        out["context"] = int(context)
    params = _num(meta.get("n_params"))
    params = round(params / 1e9, 3) if params else size_b(mid)
    if params:
        out["params_b"] = params

    # $ per million tokens: OpenRouter prices one token, as a string; HF prices a million, per
    # host, and the cheapest host is the one shown
    price = raw.get("pricing") if isinstance(raw.get("pricing"), dict) else {}
    offers = [(_num(price.get("prompt")), _num(price.get("completion")), 1e6)]
    offers += [
        (_num(h["pricing"].get("input")), _num(h["pricing"].get("output")), 1)
        for h in hosts
        if isinstance(h.get("pricing"), dict)
    ]
    offers = [(i * per, o * per) for i, o, per in offers if i is not None and o is not None]
    if offers:
        out["input"], out["output"] = (round(x, 4) for x in min(offers, key=sum))
    if hosts:
        out["hosts"] = [str(h.get("provider")) for h in hosts if h.get("provider")]
    if _num(raw.get("created")):
        out["created"] = int(raw["created"])

    kinds = []
    if "text" in outs or (not outs and not named & {"embedding", "image", "voice"}):
        kinds.append("chat")
    if "roleplay" in named:
        kinds.append("roleplay")
    params_said = raw.get("supported_parameters")
    if "reasoning" in params_said if isinstance(params_said, list) else "reasoning" in named:
        kinds.append("reasoning")
    if "small" in named or (params and params <= SMALL_B):
        kinds.append("small")
    if "image" in ins:
        kinds.append("vision")
    if "image" in outs or (not outs and "image" in named):
        kinds.append("image")
    if "audio" in outs or (not outs and "voice" in named):
        kinds.append("voice")
    if "embeddings" in outs or (not outs and "embedding" in named):
        kinds.append("embedding")
    out["kinds"] = kinds
    return out
