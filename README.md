# Kataki RPAI

An open-source AI roleplay **harness framework + desktop app**. No models are baked in: connect local models (llama.cpp server, Ollama, LM Studio, KoboldCpp), HuggingFace Inference Providers, or any OpenAI-compatible API, and pick a model per task.

What makes it different:

- **Realism-first memory** in SQLite: characters, places and events are extracted automatically and cross-linked; each character only remembers what they witnessed or were told; memories fade with *story* time, important ones fade slower, and a character told something false will try to remember and challenge it.
- **Token economy** built for small local models: cache-friendly prompt layout, extraction every few turns in idle time, zero extra LLM calls per turn for recall.
- **Per-task model selector**: separate roles for character replies, narrator, utility extraction, reasoning, embeddings (later image and music), with reasoning and standard models handled differently.
- Planned: consistent scene images, location/mood-adaptive music with slow crossfades, and a book/story/chapter library with cross-story canon links.

Status: **pre-alpha**, milestone M0 (scaffold). Design spec: [docs/specs/2026-09-18-m0-m1-design.md](docs/specs/2026-09-18-m0-m1-design.md).

## Layout

- `engine/` — Python package `kataki`: the headless harness (library, CLI, local HTTP server).
- `app/` — Electron + React + TypeScript desktop client.

## Development

Prerequisites: [uv](https://docs.astral.sh/uv/) and Node 22+ with pnpm (`corepack enable pnpm`).

```bash
cd engine && uv sync          # creates engine/.venv, which the desktop shell launches
cd ../app && pnpm install
cd .. && pnpm check           # ruff + pytest + tsc
pnpm dev                      # desktop app (spawns the engine, dev library in .dev/)
pnpm smoke                    # headless end-to-end check: shell -> engine -> renderer
```

The engine also runs on its own: `cd engine && uv run kataki serve` prints `{"token", "port"}`.

## Licence

Licence TBD — all rights reserved until one is chosen. Do not redistribute yet.

See [CONTENT_POLICY.md](CONTENT_POLICY.md).
