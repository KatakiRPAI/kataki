"""What the model picker knows about a listed model: what its server says, else what its id says."""

import pytest

from kataki.catalogue import describe, size_b


@pytest.mark.parametrize(
    "model_id, billions",
    [
        ("Qwen/Qwen3.5-9B", 9),
        ("Qwen/Qwen3.6-35B-A3B", 35),  # a mixture: the whole, not the active part
        ("Qwen/Qwen3.8-2.4T-A95B", 2400),
        ("openai/gpt-oss-120b", 120),
        ("google/gemma-3-4b-it", 4),
        ("meta-llama/Llama-4-Scout-17B-16E-Instruct", 17),
        ("qwen2.5:0.5b", 0.5),
        ("mixtral-8x7b-instruct", 56),
        ("smollm-350M", 0.35),
        ("some-model-8bit", None),
        ("deepseek-ai/DeepSeek-V4-Pro", None),
        ("7B-labs/storyteller", None),  # the maker's name is not the model's size
    ],
)
def test_size_is_read_off_the_name(model_id, billions):
    assert size_b(model_id) == billions


def test_a_bare_id_is_filed_by_its_name():
    assert describe({"id": "fake"}) == {"id": "fake", "kinds": ["chat"]}
    assert describe({"id": "Sao10K/L3-8B-Stheno-v3.2"}) == {
        "id": "Sao10K/L3-8B-Stheno-v3.2",
        "params_b": 8,
        "unfiltered": True,
        "kinds": ["chat", "roleplay", "small"],
    }
    assert describe({"id": "deepseek-ai/DeepSeek-R1"})["kinds"] == ["chat", "reasoning"]
    assert describe({"id": "nomic-embed-text-v1.5"})["kinds"] == ["embedding"]
    assert describe({"id": "black-forest-labs/FLUX.1-dev"})["kinds"] == ["image"]
    assert describe({"id": "hexgrad/Kokoro-82M"})["kinds"] == ["small", "voice"]
    assert "small" in describe({"id": "openai/gpt-5-mini"})["kinds"]


def test_openrouter_says_context_price_and_what_it_can_do():
    m = describe(
        {
            "id": "vendor/big-model",
            "name": "Vendor: Big Model",
            "created": 1790875335,
            "context_length": 262144,
            "architecture": {"input_modalities": ["text", "image"], "output_modalities": ["text"]},
            "pricing": {"prompt": "0.0000002", "completion": "0.0000025"},
            "supported_parameters": ["max_tokens", "reasoning"],
        }
    )
    assert m == {
        "id": "vendor/big-model",
        "name": "Vendor: Big Model",
        "context": 262144,
        "input": 0.2,
        "output": 2.5,
        "created": 1790875335,
        "kinds": ["chat", "reasoning", "vision"],
    }
    # what the server says beats what the name suggests; a price that "varies" is no price
    plain = describe(
        {"id": "x/thinking-rp", "supported_parameters": [], "pricing": {"prompt": "-1"}}
    )
    assert plain["kinds"] == ["chat", "roleplay"] and "input" not in plain


def test_the_hf_router_prices_per_host_and_the_cheapest_shows():
    novita = {"provider": "novita", "context_length": 1000000}
    deepinfra = {"provider": "deepinfra", "context_length": 262144}
    m = describe(
        {
            "id": "Qwen/Qwen3.8-27B",
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "providers": [
                novita | {"pricing": {"input": 0.42, "output": 3}},
                {"provider": "featherless-ai", "status": "live"},
                deepinfra | {"pricing": {"input": 0.2, "output": 2.5}},
            ],
        }
    )
    assert (m["input"], m["output"], m["context"]) == (0.2, 2.5, 1000000)
    assert m["hosts"] == ["novita", "featherless-ai", "deepinfra"]
    assert m["params_b"] == 27 and m["kinds"] == ["chat"]


def test_llama_cpp_says_the_loaded_models_size_and_context():
    m = describe({"id": "qwen", "meta": {"n_params": 8950000000, "n_ctx_train": 32768}})
    assert m == {"id": "qwen", "context": 32768, "params_b": 8.95, "kinds": ["chat", "small"]}


def test_unfiltered_is_what_the_server_says_or_the_id_names_and_never_a_guess():
    def unfiltered(raw):
        return describe(raw).get("unfiltered")

    # OpenRouter says whether it moderates in front of the model
    assert unfiltered({"id": "vendor/base", "top_provider": {"is_moderated": False}}) is True
    assert unfiltered({"id": "vendor/base", "top_provider": {"is_moderated": True}}) is None
    assert unfiltered({"id": "vendor/base", "top_provider": {"is_moderated": None}}) is None
    for named in [
        "cognitivecomputations/dolphin-mistral-24b-venice-edition",
        "huihui-ai/Qwen3-8B-abliterated",
        "mlabonne/gemma-3-27b-it-abliteration",
        "p-e-w/gemma-3-12b-it-heretic",
        "someone/Llama-3-8B-Uncensored",
        "someone/story-nsfw-12b",
        "Sao10K/L3-8B-Stheno-v3.2",
        "anthracite-org/magnum-v4-72b",
        "thedrummer/rocinante-12b",
        "neversleep/llama-3-lumimaid-70b",
    ]:
        assert unfiltered({"id": named}) is True, named
    # a plain base model is never tagged by its name; nor is one only filed under roleplay
    for base in [
        "meta-llama/Llama-3.3-70B-Instruct",
        "Qwen/Qwen3.8-27B",
        "openai/gpt-5-mini",
        "mistralai/Mistral-Nemo-Instruct-2407",
        "nousresearch/hermes-4-70b",
        "latitudegames/wayfarer-large-70b",
        "fake",
    ]:
        assert "unfiltered" not in describe({"id": base}), base


def test_a_malformed_listing_never_breaks_the_picker():
    junk = {"id": 7, "architecture": "?", "pricing": [], "providers": ["x"], "created": "soon"}
    junk["top_provider"] = "?"
    assert describe(junk) == {"id": "7", "kinds": ["chat"]}
