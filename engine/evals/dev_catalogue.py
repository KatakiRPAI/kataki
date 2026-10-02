"""A catalogue for running Kataki online on one machine: the fake model and a price for it.

    uv run python evals/dev_catalogue.py ../.dev/catalogue.db

`kataki serve --hosted --catalogue` and the gateway (`KATAKI_CATALOGUE`) both read it; the fake
model is `evals/demo.py serve-model` on :8099, and its key is `KATAKI_KEY_FAKE` (any value).
See docs/specs/2026-10-02-kataki-online.md §6.
"""

import json
import sys
from pathlib import Path

from kataki import db

path = Path(sys.argv[1])
path.unlink(missing_ok=True)
conn = db.connect(path)
with conn:
    conn.execute(
        "INSERT INTO providers(id, name, base_url) VALUES(1, 'fake', 'http://127.0.0.1:8099/v1')"
    )
    conn.execute("INSERT INTO model_roles(role, provider_id, model) VALUES('rp', 1, 'fake-rp')")
    conn.execute(
        "INSERT OR REPLACE INTO settings(key, value) VALUES('prices', ?)",
        (json.dumps({"fake-rp": {"input": 0.15, "output": 0.6}}),),
    )
conn.close()
print(f"catalogue: {path}")
