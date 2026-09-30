# Track B part 1 (B1–B3): the Host seam, prices and spend, the credit gate

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** The engine is ready to run inside Kataki online without changing anything for a desktop user. Where keys come from, where usage goes, whether a call may run, which channel a user is on and whether this machine's own routes exist are all one `Host`'s answers. Every model call leaves exactly one usage row with its cost (estimated when the provider never said, as for a stopped reply). A story can say what it has cost, by role and by day, and what a turn costs at each mind level. Online, a call the balance cannot cover is refused before it is sent, with `NO_CREDIT`, and every caller surfaces that cleanly.

**Architecture:** A new module `host.py`: a frozen `Host` (name, `get_key`, `meter`, `allow`, `channel`, `prices`, `local_routes`) with `LocalHost` (today's behaviour: keychain/env keys, `usage_log` only, never refuses, `KATAKI_CHANNEL`, local routes on) and `OnlineHost` (everything from constructor callables, fail-closed `allow`, local routes off). `create_app(host=…)` wires it: `llm.on_usage` → `host.on_usage` (a `usage_log` row, then the host's `meter`), `llm.allow` → `host.allow(ep, estimated $)` (not set at all on the desktop), a request dependency puts `host.channel()` in `features.CURRENT` (a ContextVar, so B4's many users per process each see their own), local-only routes depend on `host.local_routes`. `usage.py` grows prices, per-row cost, spend and the per-turn estimate. `llm.py` gets the one gate (`_gate`, before every request of `chat_stream`, `_complete`, `embed`, `speech`) and the one estimate (`_guess`, for a call that ran but never reported usage). `NoCredit(LLMError)` carries `code = "NO_CREDIT"`.

**Tech Stack:** Python 3.12, stdlib only, pytest with the scripted `FakeBackend`.

**Spec:** `docs/specs/2026-09-29-minds.md` §1 (4, 5), §4, §5, §7 Track B (B1–B3), §8.4 (Task 1 refines it), §0 owed items naming B2/B3. Pricing inputs: research note 21 §2 (Arch B call shapes), §3 (voice per character).

## Decisions this plan makes (and why)

- **One `Host`, two constructors, no protocol class.** `LocalHost()` is `Host`'s defaults; `OnlineHost(...)` takes every answer as a callable. Nothing else in the engine asks where it runs: it asks the host.
- **The desktop path is byte-for-byte today's.** `LocalHost.allow` is `None`, so `LLM.allow` stays unset and no gate code runs; `on_usage` still writes the same `usage_log` row (plus the new columns); the channel still comes from `KATAKI_CHANNEL`. The existing suite passes unchanged.
- **Channel through a ContextVar** (`features.CURRENT`), set per request by an app dependency from `host.channel()`; unset (tests, CLI) falls back to `KATAKI_CHANNEL`. The 46 `features.enabled(conn, …)` call sites stay as they are; a turn's task and the worker poked from it inherit the request's channel.
- **Local-only routes are 404 online:** provider CRUD, provider model lists, local server detection, `/storage`, `/backups*`. (There is no in-engine GPU image route: pictures are drawn on HuggingFace.) `PUT /settings` refuses `prices` online (403): the price table there is the service's, never the user's.
- **Cost is stored per row at record time** (v18: `usage_log.cost`, `estimated`, `usage_id`), so a later price change never rewrites what a call cost. `/spend` prices a row recorded before any price was set with today's table (desktop users who add prices later see their history), and counts what is still unpriced.
- **`prices`:** `{model: {"input", "cached", "output"}}` in $ per million tokens (cached defaults to input), and `{"char"}` in $ per million characters for a speech model (role `voice` rows hold characters in `prompt_tokens`). A malformed entry prices nothing; it never breaks a call.
- **Estimated metering:** a request that got a 2xx and started streaming but never got a usage report (stopped by the user, closed by a dropped take, failed mid-stream, or a backend that never reports) is metered once from what it sent and what streamed: prompt characters / 4 and streamed characters (reply and reasoning) / 4, `estimated: true`. The dropped resample take is exactly such a closed stream, so it is covered by the same path. A completion cut off at `finish_reason: length` is metered before it raises (the provider billed it).
- **Exactly once per actual provider call:** the gate and the meter both sit per request inside the retry loops, so a samplers or `response_format` refusal (400/422, not billed by providers) meters nothing and its retry meters once; a busy 429/502/503 retry meters nothing; `complete_json`'s parse retry is a second real call and meters twice.
- **The gate:** `LLM._gate(ep, estimate)` before every request; the estimate is prompt characters / 4 in and the request's `max_tokens` (else 1000) out, priced by the host's table and passed to `host.allow(ep, dollars | None)`. `OnlineHost` wraps the callback fail-closed (an exception refuses). The engine does not cache: the gateway client (B4) caches `allow_url` for 10 s (§8.4).
- **Surfacing a refusal:** a turn (reply, OOC answer) sends SSE `error` with `code: "NO_CREDIT"`; a JSON route answers 402 `{"code": "NO_CREDIT", "detail": {"code", "message"}}` (routes that turn `LLMError` into 502 re-raise it); side calls and the face call are already best-effort after the reply (the reply is kept, the labels are skipped); a refused extraction discards its run (the lines stay unread, retried at the next poke, no attempt counted); a refused diary call stays `pending`; the worker stops at the first refusal instead of trying the next job; embeddings already skip on any `LLMError`.
- **Per-turn estimate by level** (for the UI): lite = the reply plus 0.2 extraction reads; standard adds the side call and 0.05 diary calls; premium 0.1 diary calls. The reply's size is this story's last prompt (`context_log.est_tokens`) and its average reply length from `usage_log`, else 4000 in / 300 out; the others use note 21's shapes. A level is `null` when any model on it has no price. Marked `ponytail:` until real stories give measured averages.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies. One migration (v18, additive columns), tested on a v17 library.
- A metering failure never loses a reply; no secrets in code, logs or tests.
- Commit after every task on `feat/online-host-and-credit`; never push.

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.1/§8.4 contract, §0 Progress | 1, 6 |
| `engine/src/kataki/host.py` (new) | `Host`, `LocalHost`, `OnlineHost` | 2, 5 |
| `engine/src/kataki/features.py` | `CURRENT` channel ContextVar | 2 |
| `engine/src/kataki/server.py` | host wiring, `/health`, local-only routes, `/spend`, 402 | 2, 4, 5 |
| `engine/src/kataki/db.py` | v18 | 3 |
| `engine/src/kataki/usage.py` | prices, cost, spend, per-turn estimate | 3, 4 |
| `engine/src/kataki/llm.py` | estimated metering, the gate, `NoCredit` | 3, 5 |
| `engine/src/kataki/turns.py`, `extract.py`, `between.py` | surfacing a refusal | 5 |

---

### Task 1: The contract

- [x] §8.1: `/health.host` values; §8.4: `Host` answers, `NO_CREDIT` (SSE and 402), `/stories/{id}/spend`, `prices`, meter payload (`usage_id`, `cost`, `estimated`), local-only routes.
- [x] Commit: `docs: track B1-B3 plan and engine-gateway contract`

### Task 2: B1 the Host seam

- [x] Tests: `/health` says `desktop` and the env channel; an `OnlineHost` app says `online` and its channel, and `/features` lists by it; a turn under a beta host sees beta; local-only routes 404 online and work on the desktop; `LocalHost` sets no gate; keys come from the host.
- [x] Commit: `feat(engine): a Host seam: the desktop host is today's engine, the online host takes its answers from the service (B1)`

### Task 3: B2 cost per row, estimated metering

- [x] Tests: v18 on a v17 library; a priced call stores its cost (cached input at the cached price), a voice row by characters, an unpriced one `NULL`, a malformed table `NULL`; a stopped stream, a stream failing mid-way, a dropped take and a backend that never reports are each metered once, `estimated`; a cut-off completion is metered; a refused samplers/format retry and a busy retry meter once; a parse retry meters twice.
- [x] Commit: `feat(engine): every model call costs something on record, estimated when the provider never said (B2)`

### Task 4: B2 spend and the per-turn estimate

- [x] Tests: `GET /stories/{id}/spend` totals by role and by day, unpriced rows counted, today's price for rows recorded before one was set; the per-turn estimate grows lite < standard < premium and is null without prices; 404 for no story.
- [x] Commit: `feat(engine): what a story cost, by role and day, and what a turn costs at each level (B2)`

### Task 5: B3 the credit gate

- [x] Tests: a refused call sends no request (each of chat_stream, complete_json, embed, speech); the gate sees the host's dollar estimate; a turn's reply refused → SSE `error` `NO_CREDIT` and no reply saved; a refused side call keeps the reply; manual extraction → 402 and the lines stay unread; a refused worker read leaves no failed run; a refused diary stays pending; voice → 402; draft → 402; `OnlineHost.allow` fails closed; `PUT /settings` `prices` 403 online; the desktop never refuses.
- [x] Commit: `feat(engine): the credit gate refuses a call before it is sent, and every caller says NO_CREDIT (B3)`

### Task 6: Progress

- [x] §0 Track B lines, owed items; commit `docs: track B1-B3 progress`.
