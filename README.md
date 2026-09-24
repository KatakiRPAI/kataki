# Kataki RPAI

An open-source AI roleplay **harness framework + desktop app**. No models are baked in: connect local models (llama.cpp server, Ollama, LM Studio, KoboldCpp), HuggingFace Inference Providers, or any OpenAI-compatible API, and pick a model per task.

What makes it different:

- **Realism-first memory** in SQLite: characters, places and events are extracted automatically and cross-linked; each character only remembers what they witnessed or were told; memories fade with *story* time, important ones fade slower, and a character told something false will try to remember and challenge it.
- **Token economy** built for small local models: cache-friendly prompt layout, extraction every few turns in idle time, zero extra LLM calls per turn for recall.
- **Per-task model selector**: separate jobs for character replies, narrator, the memory reader and careful re-reads, with reasoning and standard models handled differently.
- **A library, not a list of chats**: stories gather into books that read in an order, a long story reads back as chapters, folders are saved sets of tags rather than places things move to, and the same character can walk between stories — tie two together and they bring across only as much as the time between them has left them.
- **Nothing is trapped here**: character cards (PNG, JSON, CHARX), SillyTavern chats and lorebooks or World Info come in, and every story goes out as Markdown or JSONL, or the whole library as one `.kataki` file. Every import shows you what it would make before it makes anything.
- Planned: consistent scene images, and location/mood-adaptive music with slow crossfades.

Status: **pre-alpha**. M1 (chat and the memory engine) and M2 (the library) are done. Design spec and progress: [docs/specs/2026-09-18-m0-m1-design.md](docs/specs/2026-09-18-m0-m1-design.md); the UI rebuild M1 ends with is [docs/specs/2026-09-19-ui-redesign.md](docs/specs/2026-09-19-ui-redesign.md); the library is [docs/specs/2026-09-20-m2-library.md](docs/specs/2026-09-20-m2-library.md).

## The app

Two worlds. **The Sky** is bright and above the clouds: Home (who you are, the story you were in,
what your characters have made of it), Characters, Chats, Books, Places & Plots, Activity, You, and
Settings. Outside a story, times are yours: "Played 2 hours ago".

**The Scene** is where you play: the chat runs the full height of the window over the place, lit by
the story's own clock, with widgets around it that you arrange (⋯ → Edit widgets): each character
with the face they last wore, the story clock, the place, the cast, your notes. Pin one to keep it
out; an unpinned one shows up when something happens to it. The layout is saved with the story.

The composer is **Simple** by default: write, and **Auto** reads how you wrote it (`*an action*`,
`(a thought no one hears)`, `@Mira a whisper`, `>> narration`), or pick a mode for one line.
**Advanced** adds who will hear the line, who answers, passing time, and the prompt's size. The chat
shows how characters feel ("Tobin didn't like that", "Mira trusts you a little more") and, now and
then, what they will remember; who heard what is in Advanced. Edit any line and save it, or play on
from it (the old continuation stays a swipe away). Name a moment ("the storm") and the story's dates
read in its words: "the evening of the storm", "six years after the storm".

Click a character for who they are right now. **Backstage** shows the **Mind** of the last reply:
what reached them, why they were the one to answer, what recall weighed and what made the prompt
(gold) or was cut, how they felt and what they doubted, how they have come to feel about you across
the story; then the prompt, the cast, and what each job did this turn. Memory is one switch away:
every fact a character holds and how clearly.

Places & Plots files every place and plot under the books and stories that use it. Chats and
Characters carry tags and saved folders; Books says what order stories read in; a story reads back
as chapters. Drop a character card, a chat, a lorebook or a whole library anywhere in the app and it
tells you what it would make first; any story goes out as Markdown or JSONL.

## Layout

- `engine/`: Python package `kataki`, the headless harness (library, CLI, local HTTP server).
- `app/`: Electron + React + TypeScript desktop client.

## Development

Prerequisites: [uv](https://docs.astral.sh/uv/) and Node 22+ with pnpm (`corepack enable pnpm`).

```bash
cd engine && uv sync          # creates engine/.venv, which the desktop shell launches
cd ../app && pnpm install
cd .. && pnpm check           # ruff + pytest + tsc
pnpm dev                      # desktop app (spawns the engine, dev library in .dev/)
pnpm smoke                    # headless end-to-end check: shell -> engine -> renderer
```

The engine also runs on its own:

- `uv run kataki serve` prints `{"token", "port"}`. Open the renderer in any browser with `?port=<port>&token=<token>` after the address (the `#…` part is the app's route). For a fixed dev setup: `KATAKI_TOKEN=dev uv run kataki serve --port 8765`, `corepack pnpm -C app exec vite --port 5173`, then `http://localhost:5173/?port=8765&token=dev#/`.
- `uv run kataki chat --db <library.db>` plays the newest story in the terminal.

A demo library and a fake model let you try the whole app without a GPU (from `engine/`):

- `uv run python evals/demo.py build` writes `.dev/demo.db` from scratch: the design brief's friends, places, plots and four stories, including "The Third Floorboard" played through to the six-year skip, with its memories read. It checks the result and exits non-zero if something is off.
- `uv run python evals/demo.py serve-model --think` answers on `http://127.0.0.1:8099/v1` (model `fake`) with streamed lines, and some thinking first with `--think`. The demo library already points at it.
- `KATAKI_DB=.dev/demo.db pnpm dev` opens the desktop app on the demo library; with `kataki serve --db ../.dev/demo.db` any browser can use it.

## Connecting a model

Kataki talks to anything with an OpenAI-compatible `/v1` endpoint. The Models page can find llama.cpp, Ollama, LM Studio, KoboldCpp, vLLM and TabbyAPI when they are already running on this computer, and has presets for OpenRouter and HuggingFace. API keys go to the system keychain, never into the library file.

### A local model on an 8 GB GPU (the reference laptop: RTX 5060 Laptop, 8 GB)

1. **llama.cpp.** Download a Windows CUDA release from [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases). RTX 50-series (Blackwell) cards need a **CUDA 12.8 or newer** build.
2. **A model.** An 8-9B instruct model at Q4_K_M (about 5-6 GB) leaves room for a 16k context. A model with switchable thinking can serve every job alone: thinking off for replies and memory reads, on for the Reasoning job. Tested: **Qwen3.5-9B Q4_K_M** (`Qwen3.5-9B-Q4_K_M.gguf` from [unsloth/Qwen3.5-9B-GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF), 5.7 GB).
3. **Start it.** This command was tested with llama.cpp b11043 (CUDA 13). Flags change between builds, so check `llama-server --help` against yours:

   ```bash
   llama-server -m Qwen3.5-9B-Q4_K_M.gguf --alias qwen3.5-9b -c 32768 -ngl 99 -fa on -ctk q8_0 -ctv q8_0 -np 2 -kvu --port 8080
   ```

   - `-ngl 99` puts every layer on the GPU (about 6 GB of VRAM in total with this model).
   - `-ctk/-ctv q8_0` halves the memory of the context.
   - `-np 2` gives replies and the memory reader a slot each, so reading memory does not throw away the chat's cached prompt. `-kvu` lets the slots share the whole `-c` instead of splitting it.
   - The model's own chat template (on by default in recent builds; older ones need `--jinja`) is what switches thinking on and off.
   - On the reference laptop: first words in 1-2 s, a whole reply in 7-9 s.
4. **In Kataki:** Models → *Look for model servers on this computer* → *Add and use it*. Then set the Characters job's context size (16384 is plenty). For a hybrid model like Qwen3.5, set thinking to *off* on Characters and Memory reader and *on* on Reasoning.

**Recall by meaning** needs no setup: with nothing chosen on that row, a small built-in model ([potion-retrieval-32M](https://huggingface.co/minishlab/potion-retrieval-32M), 125 MB, runs on the CPU) is downloaded once into Kataki's data folder and used. Pick a server on that row only to use your own embedding model.

Ollama works the same way (`ollama pull <model>`, then look for servers). It has no slots, so the chat prompt is re-read after each memory read, which is slower.

### Everything through HuggingFace

With a HuggingFace token, [Inference Providers](https://huggingface.co/docs/inference-providers) can run every job, pictures included, with nothing on your GPU. Models → add the **HuggingFace** preset with your token (a fine-grained token with only *Make calls to Inference Providers* is enough), then give each job a model. Tested on 2026-09-23:

- **Characters:** `Qwen/Qwen3-235B-A22B-Instruct-2507:deepinfra`, context 32k. About $0.0002 a reply. The 9B below muddles who said what and invents backstory; side by side on the same prompt this beat DeepSeek-V3.2 and cost less.
- **Narrator, Memory reader:** `Qwen/Qwen3.5-9B` with thinking *off*. First words in about 2 s, a whole reply in about 6 s.
- **Reasoning:** `Qwen/Qwen3.8-27B:deepinfra` with thinking *on*. A careful re-read of a scene takes about 3 minutes in the background and costs 1-3¢. (Qwen3.5-9B with thinking on does not work here: on a memory read it thinks for 7,000 to 16,000+ tokens and often never answers.)
- **Pictures:** `Tongyi-MAI/Z-Image-Turbo`. Places get *Draw background*. Characters get a **Look** card on their profile: *Draw them* (a first picture from their description), then *Use this look*, which makes five expressions (neutral, smiling, wary, surprised, doubtful) from that one picture with `Qwen/Qwen-Image-Edit-2511` and cuts each out with `briaai/RMBG-2.0`. On stage, each character shows the expression that fits their last line.

Every picture is one click and costs money: a background or a first picture about $0.005, five expressions about $0.24. Nothing is drawn or retried without a click. If a provider refuses a picture, the app says why and offers the other provider. Kataki only draws adults: a character whose own description makes them sound younger than 18 is not drawn.

### Checking memory against a real model

```bash
cd engine
uv run python evals/live_eval.py --base-url http://127.0.0.1:8080/v1 --model <model> --ctx 16384 --hybrid
```

(`--hybrid` for a model with switchable thinking, as in the setup above.)

This plays a scripted story. A secret is told while one character is out of the room, the user lies about it, and the story skips six years. The report covers:

- whether the absent character leaks the secret, and whether he learned it later by honest means
- whether the other character recalls it, and what was actually in her prompt at the six-year reunion: the old conversation, or only her (hazy) memory
- how usable the memory reader's JSON was
- duplicate entities
- prompt-cache reuse
- latency

It runs in a throwaway library.

## Licence

Licence TBD: all rights reserved until one is chosen. Do not redistribute yet.

See [CONTENT_POLICY.md](CONTENT_POLICY.md).
