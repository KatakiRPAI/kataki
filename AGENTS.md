# Kataki RPAI

Open-source AI roleplay app: a Python engine (`engine/`, package `kataki`) owns the library and
serves HTTP; a React UI (`app/`) runs in Electron and in a browser. AI agents maintain this
repo. These rules apply to every agent and every human.

## Where the truth lives

- Each feature has a spec in `docs/specs/`; its **Progress** list says what is done and owed.
  Read the spec before working on its area; add a Progress line when you land something.
- The UI's source of truth is the handoff in `docs/handoff/` (plan:
  `docs/specs/2026-09-28-handoff-3.md`). `docs/design/` and `docs/kataki-design/` are history.
- Repo infrastructure (GitHub, CI, releases, security): `docs/specs/2026-09-29-repo-infrastructure.md`.
  Before touching `.github/`, release config or versioning, read it and follow its phases.
- Commands are the scripts in `package.json` (root and `app/`); `pnpm check` is the gate.

## How a change lands

Until Phase 1 of the infrastructure plan is done there is no remote: commit on `m0-scaffold`
and never push. After it:

1. Branch from `main`: `feat/…`, `fix/…`, `docs/…`, `chore/…` (agents may prefix their tool,
   e.g. `claude/…`). One change per branch; keep it small enough to review in one sitting.
2. Commit in Conventional Commits (`feat(app): …`, `fix(engine): …`, `docs: …`); release-please
   builds versions and the changelog from them. Mark breaking changes with `!`.
3. `pnpm check` passes locally before you open a PR. A UI change also gets a look in the real
   app (see the README's Development section).
4. Open a PR with the template filled in: what changed, how you checked it, the risk. Merge
   only when required checks are green; squash merge.
5. Changes to `.github/`, `AGENTS.md`, `CLAUDE.md`, release or signing config, schema
   migrations (`engine/src/kataki/db.py`) and dependency majors wait for the user's approval
   (CODEOWNERS). Everything else may merge when green.

`main` is always releasable: every merge ships to the alpha channel. A bad change is fixed
forward with a revert PR; history on `main` is never rewritten.

## Guardrails

- Keep secrets in the OS keychain or `.env` (gitignored), and only there: never in code, logs,
  commits, issues or PRs. Push protection blocks known key formats; treat a block as a real
  leak and tell the user.
- Paid APIs (HuggingFace, OpenRouter, Claude in Actions, code signing): state the number of
  calls and the cost, and wait for the user's yes. Default to one smoke-test request.
- Schema changes are forward-only migrations in `db.py`, each with a test on a library from the
  previous version.
- New dependencies need a reason in the PR; prefer what is already installed.
- Workflows: actions pinned to a commit SHA, `permissions: {}` at the top, grants per job.

## Image generation (M3)

Before any image work (generating, changing the render chain, planning the character-sheet
feature, or touching image code in `engine/`), read [`docs/images/README.md`](docs/images/README.md).
It holds the current status and links the rest.

Before any GPU run, read [`docs/images/rules-and-gotchas.md`](docs/images/rules-and-gotchas.md):
the 8 GB limit and the user's run protocol (state the expected time first, check the step rate at
~30 s, kill a spilling run at once).
