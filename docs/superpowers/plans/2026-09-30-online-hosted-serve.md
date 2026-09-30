# Track B part 2 (B4–B6): hosted serve, background jobs online, the gateway contract test

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every task (test first, see it fail, implement, see it pass). Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** One engine process serves Kataki online: many users, each with their own library, opened when their first request arrives and closed when idle. Who the user is comes only from the gateway's signed headers. Every model call is asked of the gateway first (cached 10 s) and billed to it after, and a bill the gateway could not take is sent again later. A user's background reads and diaries run in their own library, never more than a few calls at once, and never past a daily spending cap. A test drives two users through a turn each against a fake gateway: each ledger matches that user's `usage_log`, to the micro-dollar.

**Architecture:** A new module `hosted.py`:
- `sign` / `who` — the signed headers (HMAC-SHA256 over user, channel and a timestamp, 60 s window).
- `Gateway` — the engine's HTTP client to the service: `allow` (cached 10 s per user), `meter` (POST, one retry), `resend` (the outbox: `usage_log` rows with `metered=0`).
- `Hosted` — an ASGI app. It checks the signature, opens the user's library on demand (`root/<user>/library.db`), writes the service's catalogue into it (providers, model roles), builds a per-user `create_app(conn, …, host=OnlineHost(…))` with its own `LLM` and `Worker`, and forwards the request with a per-library bearer token. LRU with a size limit and an idle sweep; closing a library cancels its worker (the read is discarded by `extract.recover` at the next open) and closes its connection.

Per-user isolation is structural: each library has its own `LLM`, `Worker`, `OnlineHost` and meter closure bound to that user id, so a call cannot be billed to another user (B1's one-LLM-per-app guard already refuses a shared `LLM`).

**Tech Stack:** Python 3.12, stdlib (`hmac`, `hashlib`, `decimal`, `collections.OrderedDict`), `httpx2` (already installed) for the gateway client, pytest with `FakeBackend` and `httpx2.MockTransport` as the fake gateway.

**Spec:** `docs/specs/2026-09-29-minds.md` §4, §7 Track B (B4–B6), §8.4 (Task 1 extends it), §0 owed lines naming B4.

## Decisions this plan makes (and why)

- **One FastAPI app per open library, not a connection per request.** `create_app` already is "one library": reusing it per user keeps every route, the worker and the gate identical to the desktop's and to B1–B3's tests. The cost is one app object per open library (cheap) and a cap on how many are open.
- **Headers:** `X-Kataki-User`, `X-Kataki-Channel`, `X-Kataki-Time` (unix seconds), `X-Kataki-Sig` = hex HMAC-SHA256 of `user\nchannel\ntime` with the shared secret. Missing, tampered, or more than 60 s off: 401, and nothing is opened. A user id must match `[A-Za-z0-9_-]{1,64}` (it names a folder). The desktop's `create_app` never reads these headers (only its bearer token counts).
- **Secrets from env or keychain, never the library:** `KATAKI_GATEWAY_SECRET` (inbound HMAC) and `KATAKI_GATEWAY_KEY` (outbound bearer), else keychain service `kataki-gateway`. Provider keys stay `roles.get_key` (env `KATAKI_KEY_*` / keychain), the service's own.
- **The catalogue is a library file** (`--catalogue`): its `providers`, `model_roles` and `prices` setting are the service's. They are written into each user library at every open (the service owns routing; archive.MANAGED already keeps imports off them), and `prices` is the host's table. The operator builds it with the desktop app.
- **Gateway client:** `GET {gateway}/allow?user=&estimate=` → `{"ok"}`, cached per user for 10 s (both answers). `POST {gateway}/usage` with the meter row plus `user`, tried twice (timeout 2 s), idempotent on `usage_id`. A POST that fails raises, so the row stays `metered=0`; the outbox (`Gateway.resend`) sends those rows again on every library open and every idle sweep, oldest first, and stops at the first failure. Synchronous (the host is called synchronously, §8.4); `ponytail:` a blocking call on the event loop, bounded by the 2 s timeout, async client if the gateway is ever slow.
- **Ledger in integer micro-dollars:** `usage.micros(prices, row)` prices a meter / `usage_log` row from its tokens in exact decimal arithmetic, rounded half-up to whole micro-dollars (a price in $ per million tokens is micro-dollars per token). The fake gateway's ledger uses it; the real ledger must compute the same way. `usage_log.cost` stays the display float.
- **Per-user concurrency:** `LLM(max_calls=N)` holds a semaphore around each provider request (default 4 online, none on the desktop). A call past the limit waits, it is not refused. A single task never nests model calls, so it cannot deadlock itself. The worker is already one job at a time per library.
- **Daily cap:** each user's gate first checks today's (UTC) `usage_log` spend plus the call's estimate against the cap (`--daily-cap`, default $5): over it raises `DailyCap(NoCredit)` with code `DAILY_CAP`, which every NO_CREDIT surface already handles (SSE `error` with the code, 402 with the code, background worker stops). `OnlineHost` lets a `NoCredit` from its callback through instead of turning it into a plain refusal. Checked in the engine, before the gateway, so a runaway loop stops even if the gateway is down.
- **Pictures stay 404 online** (`/draw`, `/look`): the B4-blocking owed item is closed by keeping them local-only until images have a price, gate and meter.
- **No schema change.** `usage_log.metered` (v18) is the outbox; today's spend reads `usage_log.at`.
- **Binding:** `kataki serve --hosted` binds `127.0.0.1` unless `--bind` says otherwise.

## Global Constraints

- Commands from `engine/`: `uv run pytest -q`; `uv run ruff check . && uv run ruff format --check .`.
- No new dependencies, no migration, no paid calls.
- Commit after every task on `feat/online-hosted-serve`; never push.

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `docs/specs/2026-09-29-minds.md` | §8.4 contract, §0 Progress | 1, 7 |
| `engine/src/kataki/usage.py` | `micros` | 2 |
| `engine/src/kataki/llm.py` | `max_calls`, `DailyCap` | 3, 4 |
| `engine/src/kataki/host.py` | NoCredit passes through `OnlineHost` | 4 |
| `engine/src/kataki/server.py` | `failed` keeps the refusal's code; `app.state.worker` | 4, 5 |
| `engine/src/kataki/hosted.py` (new) | headers, `Gateway`, `Hosted` | 5, 6 |
| `engine/src/kataki/__main__.py` | `serve --hosted` | 6 |
| `engine/tests/test_hosted.py` (new) | B4, B5 | 5, 6 |
| `engine/tests/test_gateway_contract.py` (new) | B6 | 7 |

---

### Task 1: The contract

- [ ] §8.4: the four headers and the window; `/allow` and `/usage` under one gateway URL; the outbox; `DAILY_CAP`; micro-dollars; pictures stay 404.
- [ ] Commit: `docs: track B4-B6 plan and the hosted contract`

### Task 2: Integer micro-dollars

- [ ] Tests: `micros` of a row with cached tokens is exact (0.3 $/M × 7 tokens = 2.1 → 2; 0.5 → rounds half up); a voice row by characters; unpriced → None; `cost` unchanged.
- [ ] Commit: `feat(engine): the ledger's price of a call in whole micro-dollars (B4)`

### Task 3: Per-user concurrency

- [ ] Tests: with `max_calls=1`, a second call waits until the first's request is done; with none, both run at once.
- [ ] Commit: `feat(engine): a cap on one user's model calls in flight (B5)`

### Task 4: The daily cap

- [ ] Tests: `DailyCap` is a `NoCredit` with code `DAILY_CAP`; `OnlineHost` lets it through; a JSON route answers 402 with `DAILY_CAP`; a turn's SSE error carries `DAILY_CAP`.
- [ ] Commit: `feat(engine): a daily spending cap refuses with its own code (B5)`

### Task 5: Signed headers and the gateway client

- [ ] Tests: a signed request verifies; unsigned, tampered, stale, and a bad user id are refused; `allow` asks once per 10 s per user; `meter` retries once then raises; `resend` sends `metered=0` rows and marks them, stopping at the first failure.
- [ ] Commit: `feat(engine): signed gateway headers and the gateway client with an outbox (B4)`

### Task 6: `kataki serve --hosted`

- [ ] Tests: a signed request opens that user's library under the root; unsigned → 401 and no library; each user sees only their own stories; the catalogue's providers and prices are in the library; the LRU closes the least recent idle library past the limit; the sweep closes idle ones and resends the outbox; closing cancels a running background read and the next open discards it; pictures 404; the desktop app ignores signed headers (401 without its token); the CLI binds 127.0.0.1 by default and refuses to start without a secret.
- [ ] Commit: `feat(engine): kataki serve --hosted: a library per user, opened on demand (B4, B5)`

### Task 7: The gateway contract test, and Progress

- [ ] Test: two users, a turn each, through `Hosted` and a fake gateway; each ledger equals the micro-dollar sum of that user's `usage_log`, and holds only that user's `usage_id`s; a refused user sends nothing to the model and nothing to the ledger; a meter outage leaves rows the outbox then settles to the same totals.
- [ ] §0 Progress and owed lines; commit `test(engine): the gateway contract, two users and their ledgers (B6)` and `docs: track B4-B6 progress`.
