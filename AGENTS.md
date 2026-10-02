# Kataki RPAI

AI roleplay app: a Python engine (`engine/`, package `kataki`) owns the library and serves
HTTP; a React UI (`app/`) runs in Electron and in a browser. Two products ship from this public
repo: the free, open-source desktop app (the user's own models), and Kataki online, a hosted
website that bills pay-as-you-go for online models. AI agents maintain this repo. These rules
apply to every agent and every human.

## Where the truth lives

- Each feature has a spec in `docs/specs/`; its **Progress** list says what is done and owed.
  Read the spec before working on its area; add a Progress line when you land something.
- The engine's direction (how characters think, feel, remember and change) is
  `docs/specs/2026-09-29-minds.md`, built from the research in
  `docs/research/reports/Human like minds for Kataki.md`; where it conflicts with an older spec,
  it wins. Engine work starts from its roadmap and Progress.
- The UI's source of truth is the handoff in `docs/handoff/` (plan:
  `docs/specs/2026-09-28-handoff-3.md`). `docs/design/` and `docs/kataki-design/` are history.
- Repo infrastructure (GitHub, CI, releases, security): `docs/specs/2026-09-29-repo-infrastructure.md`.
  Before touching `.github/`, release config or versioning, read it and follow its phases.
- Commands are the scripts in `package.json` (root and `app/`); `pnpm check` is the gate.

## How a change lands

The repo is `KatakiRPAI/kataki`. `main` accepts nothing but pull requests. Agents push and open
PRs as the bot account, through `bash .github/as-bot.sh git …` / `bash .github/as-bot.sh gh …`,
so the history shows which changes an agent wrote.

1. Branch from an up-to-date `main`: `feat/…`, `fix/…`, `docs/…`, `chore/…` (agents may prefix their tool,
   e.g. `claude/…`). One change per branch; keep it small enough to review in one sitting.
2. Commit in Conventional Commits (`feat(app): …`, `fix(engine): …`, `docs: …`); release-please
   builds versions and the changelog from them. Mark breaking changes with `!`.
3. `pnpm check` passes locally before you open a PR. A UI change also gets a look in the real
   app (see the README's Development section).
4. Push the branch and open a PR as the bot, with the template filled in: what changed, how
   you checked it, the risk. Give it a Conventional Commits title (squash merge makes it the
   commit on `main`).
5. The owner has delegated review and merging (2026-09-29). When the required checks are green,
   squash-merge the PR yourself with the owner's own `gh` login (the default active account, not
   the bot): `gh pr merge <n> --squash`. Then tell the owner what landed, in plain words. This
   covers every path, including `.github/`, `AGENTS.md`, schema migrations and billing code;
   production deploys, stable releases and live payment keys still wait for the owner.
6. Update the alpha at `https://kataki.qaiskilani.com` after every merge: it is the alpha
   version of the app the owner uses, so it always runs `main`. On the owner's server, in
   `/opt/kataki`: `git pull && docker compose up -d --build`. Done when that checkout is at
   `main`'s tip and the site answers.
7. Start the next change from `main` again, not on top of an unmerged branch, unless it truly
   depends on it (then say so in the PR). When the PR below a stacked one is squash-merged,
   rebase the upper branch onto `main` (`git rebase --onto origin/main <old base tip> <branch>`)
   and force-push that PR branch (`--force-with-lease`) before merging it.

`main` is always releasable: every merge ships to the desktop alpha channel and deploys to
website staging. Production (stable desktop releases, website deploys) always waits for the
user's approval. A bad change is fixed forward with a revert PR; history on `main` is never
rewritten.

## Guardrails

- Keep secrets in the OS keychain or `.env` (gitignored), and only there: never in code, logs,
  commits, issues or PRs. Push protection blocks known key formats; treat a block as a real
  leak and tell the user.
- Paid APIs (HuggingFace, OpenRouter, Claude in Actions, code signing): state the number of
  calls and the cost, and wait for the user's yes. Default to one smoke-test request.
- Schema changes are forward-only migrations in `db.py`, each with a test on a library from the
  previous version. On the website they go expand → migrate → contract, so the previous
  release still runs if it has to be rolled back to.
- Work against staging and the payment processor's test mode. Production data, live payment
  keys and real customer accounts are the user's to touch.
- New dependencies need a reason in the PR; prefer what is already installed.
- Workflows: actions pinned to a commit SHA, `permissions: {}` at the top, grants per job.

## Image generation (M3)

Before any image work (generating, changing the render chain, planning the character-sheet
feature, or touching image code in `engine/`), read [`docs/images/README.md`](docs/images/README.md).
It holds the current status and links the rest.

Before any GPU run, read [`docs/images/rules-and-gotchas.md`](docs/images/rules-and-gotchas.md):
the 8 GB limit and the user's run protocol (state the expected time first, check the step rate at
~30 s, kill a spilling run at once).
