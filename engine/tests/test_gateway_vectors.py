"""The gateway (gateway/src, TypeScript) must bill and sign exactly as the engine does. Both
sides are held to `gateway_vectors.json`: this test here, `money.test.ts` and `sign.test.ts`
there (docs/specs/2026-10-02-kataki-online.md §3)."""

import json
from pathlib import Path

from kataki import hosted, usage

VECTORS = json.loads(Path(__file__).with_name("gateway_vectors.json").read_text("utf8"))


def test_the_engine_bills_what_the_vectors_say():
    for case in VECTORS["money"]:
        assert usage.micros(VECTORS["prices"], case["row"]) == case["micros"], case["row"]


def test_the_engine_signs_what_the_vectors_say():
    for v in VECTORS["sign"]:
        said = hosted.sign(
            v["secret"].encode(), v["user"], v["channel"], v["at"], v["method"], v["target"]
        )
        assert said == v["sig"]
