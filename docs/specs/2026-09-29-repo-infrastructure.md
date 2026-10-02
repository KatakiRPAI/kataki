# Repo infrastructure: GitHub, CI, release channels, hosting, security

Kataki is two products from one public repo:

- **Kataki (desktop)**: open source, local, free. The user brings their own models. It ships as
  signed installers through alpha → beta → stable release channels.
- **Kataki online (website)**: the same UI and engine, hosted. Users sign in, the service
  calls online models with its own keys, and users pay as they go (provider cost plus a
  margin). It runs as real servers: staging and production.

The repo moves from one local branch (`m0-scaffold`, never pushed) to a GitHub organisation
with protected `main`, CI on every change, both delivery tracks, rollback and security
scanning. AI agents maintain the repo, so each rule here is enforced by GitHub and not only
written down. [`AGENTS.md`](../../AGENTS.md) holds the day-to-day rules; this file holds the
plan and its Progress.

## Progress

Update this list as phases land (date · phase · what changed · anything left). Items marked
**[user]** need the user; an agent prepares them and asks.

- 2026-09-29 · plan written; `AGENTS.md` added, `CLAUDE.md` now imports it. Nothing pushed yet.
- 2026-09-29 · user's answers folded in: new org, history rewritten to the noreply address,
  public from day one, a hosted pay-as-you-go website, free SignPath signing.
- 2026-09-29 · Phase 0 done. Leftover docs committed (`docs/images/`, research moved under
  `docs/research/`); `docs/design/` and the old design screenshots stay on disk, ignored. The
  stranded fix `e3813bb` (a failed re-read keeps its memories) cherry-picked; the engine was
  failing its own lint (59 long lines, 11 unformatted files), so ruff now leaves line length
  to the formatter and `pnpm check` is green (536 tests). gitleaks: no leaks in 160 commits.
  `main` holds everything; `m0-scaffold` and the old worktree branch are gone. History
  rewritten twice with git filter-repo: authors → the noreply address, and the old address
  scrubbed from file contents; quoted hashes in the specs remapped. Pre-rewrite backup:
  `D:\kataki-before-rewrite.bundle` (delete it after the first push).
- 2026-09-29 · Phases 1–3 written, waiting for the org: `ci.yml`, `security.yml`,
  `scorecard.yml`, `dependabot.yml`, CODEOWNERS, templates, `SECURITY.md`, `CONTRIBUTING.md`,
  the `main` ruleset as JSON, and `.github/setup-repo.sh <org>`, which applies all of it.
  actionlint and zizmor pass; the app builds (`build`, `build:web`) pass locally.
- 2026-09-29 · Phase 1 live: org `KatakiRPAI` (repo creation locked to admins), public repo
  `KatakiRPAI/kataki`, `setup-repo.sh KatakiRPAI QaisBOT` applied every setting, the `main`
  ruleset and the labels; QaisBOT has write access. The first CI run passed on Windows, the
  app and the smoke test, and caught a real bug on Ubuntu (search's numbered SQL placeholders,
  an error from Python 3.14), fixed in its own PR. Security and Scorecard passed. Dependabot
  opened its first grouped PRs. Left for the user: log the bot into gh, 2FA on QaisBOT and
  required org-wide.
- 2026-10-02 · A first hosted Kataki, ahead of Phase 6: `Dockerfile` and `compose.yaml` run the
  single-library engine with the web build (`kataki serve --web`) on the owner's server, behind
  Caddy at `https://kataki.qaiskilani.com/app/` (the token opens it; the checkout, `.env` and
  library are in `/opt/kataki`). Update it there with `git pull && docker compose up -d --build`.
  It is one user's library, not the website: the gateway, GHCR images and `deploy.yml` are
  still owed.
- 2026-10-02 · That hosted Kataki is the alpha: `AGENTS.md` has agents update it after every
  merge, by hand until `deploy.yml` does it.

Decisions made (2026-09-29):

- **Owner:** a new GitHub organisation (the user creates it). Repo name `kataki`.
- **Commit email:** rewrite all history to `70582355+QaisZAK@users.noreply.github.com` before
  the first push (Phase 0). Hashes quoted in `docs/specs/` get a mapping (below).
- **Public from day one.**
- **Signing:** SignPath Foundation's free OSS programme (conditions in Phase 4).
- **Website:** hosted, pay-as-you-go online models with a margin. The engine side (one engine,
  a `Host` seam, many libraries per process, metering, credits) is track B of
  `docs/specs/2026-09-29-minds.md` §4; this plan owns its hosting (Phase 6).

Still open:

1. **[user] Bot token.** The org is `KatakiRPAI` and the bot account `QaisBOT` is a member
   (2026-09-29). Left: the owner logs the bot into gh once (`gh auth login` as QaisBOT, then
   `gh auth switch --user QaisZAK`), after which `.github/as-bot.sh` works; and 2FA on for both
   accounts, then "Require two-factor authentication" in the org's security settings.
2. **[user] Domain** for the website and project pages. Default: none until the user buys one;
   staging uses the host's default address.
3. **[user] Payment processor.** The user owns the legal and payment-provider side (minds spec,
   owner decisions); agents build the ledger and checkout against the processor's test mode
   as if green-lit.
4. **[user] Claude in Actions** (API cost per run), Phase 5.

## Research summary (2026-09-29)

What mature open-source desktop apps with beta users run, and what fits a solo, AI-maintained
repo:

- **Branching: trunk-based.** One long-lived branch, `main`, always releasable. Short-lived
  branches → PR → squash merge. No `develop` or `staging` branches: channels come from tags,
  not branches, so there is nothing to keep in sync.
- **Environments for a local-first desktop app** are release channels, not servers.
  electron-builder/electron-updater ship `latest`, `beta` and `alpha`: a `-beta` version goes to
  beta and alpha users, stable goes to everyone, and `stagingPercentage` in `latest.yml` rolls a
  release out to a share of users first ([electron-builder: release using channels][ch]).
- **Rules GitHub enforces:** repository rulesets on `main` (PR required, required status
  checks, linear history, no force-push, no deletion), CODEOWNERS for sensitive paths, merge
  queue once parallel PRs start breaking `main` ([rulesets][rs]). Required checks must also run
  on `merge_group` when the queue is on.
- **Versioning:** release-please reads Conventional Commits (this repo already writes
  `feat(app): …`), keeps a release PR with the changelog open, and bumps `pyproject.toml` and
  `package.json` together ([release-please][rp]). It is language-agnostic; changesets is
  JS-first.
- **Supply chain:** actions pinned to commit SHAs, `permissions: {}` at the top of every
  workflow with per-job grants, zizmor to lint workflows, OpenSSF Scorecard weekly, CodeQL,
  Dependabot (pip/uv, npm, github-actions), dependency-review on PRs, secret-scanning push
  protection, and build provenance attestations on release files ([scorecard-action][sc]).
- **Signing:** unsigned Windows installers trip SmartScreen. SignPath Foundation signs
  qualifying OSS for free (publisher shows as "SignPath Foundation"); Azure Artifact Signing is
  the cheapest paid route ([SignPath OSS][sp], [Microsoft: signing options][ms]).
- **Agent instructions:** `AGENTS.md` is the cross-tool standard (Codex, Copilot, Cursor,
  Gemini and more read it). Claude Code reads `CLAUDE.md`, so `CLAUDE.md` imports `@AGENTS.md`
  and holds only Claude-specific notes ([AGENTS.md vs CLAUDE.md][am]).
- **AI-authored PRs:** AI review is evidence, not approval. The pattern that holds up: small
  deterministic required checks, a bot identity for agent PRs, and human approval only where
  it matters (CI/release/security config, schema migrations, dependency majors).
- **Hosted service in an open-source repo** (open core, as Cal.com, Plausible and Supabase
  run it): the service code lives in the public repo; what stays private is secrets, customer
  data and the production config values. Each commit builds one immutable container image;
  staging deploys it automatically, production deploys the *same* image after an approval
  (GitHub Environments with required reviewers), and rollback is redeploying the previous
  image. Database changes go expand → migrate → contract so the previous image still runs
  against the new schema. Payments run in the processor's test mode everywhere but production.

[ch]: https://www.electron.build/tutorials/release-using-channels.html
[rs]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
[rp]: https://github.com/googleapis/release-please
[sc]: https://github.com/ossf/scorecard-action
[sp]: https://signpath.io/solutions/open-source-community
[ms]: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
[am]: https://www.morphllm.com/agents-md-guide

## Target shape

One branch (`main`), one version number, two ways out.

**Desktop: release channels**

| Environment | What it is | How code gets there | Who gets it |
|---|---|---|---|
| dev | `pnpm dev` on the `.dev/` library, the fake model (`engine/evals/demo.py`) | a branch | the agent or user working |
| PR preview | installer + web build uploaded as a CI artifact on each PR | open a PR | whoever reviews |
| alpha | pre-release `vX.Y.Z-alpha.N`, updater channel `alpha` | every merge to `main` | the user (dogfood) |
| beta | pre-release `vX.Y.Z-beta.N`, channel `beta` | "Promote" workflow on a green alpha | opted-in beta users (Settings › update channel) |
| stable | release `vX.Y.Z`, channel `latest`, staged rollout 20% → 100% | merging the release-please PR | everyone |

Rollback is roll-forward plus a stop button:

1. Stop the rollout: set `stagingPercentage: 0` in the release's `latest.yml` (or mark the
   release draft), so no one else updates.
2. Revert the bad commit on `main` (a PR like any other), release the next patch.
3. User data survives because the engine backs up the library before any schema migration and
   refuses to open a library newer than itself (both owed, Phase 4).

**Website: servers**

| Environment | What it is | How code gets there | Who gets it |
|---|---|---|---|
| dev | the stack on one machine (`docker compose`), payments in test mode, the fake model | a branch | the agent or user working |
| staging | its own database, payments in test mode, cheap models, `robots: noindex` | every merge to `main` deploys that commit's image | the user, testers |
| production | live payments, real models | the same image, after the user approves the `production` environment | everyone signed up |

Beta users on the website are accounts with a `beta` flag on production (feature flags), not a
separate server. Rollback: redeploy the previous image (one click in the host, or re-run the
deploy workflow on the previous tag). Migrations are expand/contract, so the previous image
still works on the new schema; a database backup runs before every production deploy.

## Phases

Each phase ends in something checkable. Do them in order.

### Phase 0: clean up before anything is public (local only)

- [x] Whoever owns the ~200 uncommitted changes and untracked files on `m0-scaffold` commits
      or discards them (parallel sessions left them; commit nothing you did not write).
- [x] Keep the old designs out of git: `docs/design/` (98 MB) and
      `docs/kataki-design/**/screens/png/` (39 MB) go in `.gitignore`, or into a release asset
      if they must be shared. The handoff (`docs/handoff/`) is the source of truth.
- [x] Move root `reports/` and `research_notes/` into `docs/research/`.
- [x] Settle branch `claude/bold-fermi-0b6972` (commit `e3813bb`, not on `m0-scaffold`): merge
      or delete it; prune its dead worktree (`git worktree prune`).
- [x] Run `gitleaks detect` over full history. (A pattern scan on 2026-09-29 for HF, OpenAI,
      GitHub and AWS keys found nothing; `.env` has always been ignored.)
- [x] Fast-forward `main` to `m0-scaffold` (`main` is its ancestor), then delete `m0-scaffold`.
- [x] Rewrite authorship (needs a clean tree and no other session mid-work; tell the user
      first, since every hash changes):
      `git filter-repo --mailmap <file>` with the line
      `QaisZAK <70582355+QaisZAK@users.noreply.github.com> <OLD-EMAIL>`, then
      `git config user.email 70582355+QaisZAK@users.noreply.github.com` so new commits match.
      Then rewrite the short hashes quoted in `docs/specs/` and `docs/images/` from
      `.git/filter-repo/commit-map` (old → new) and commit that.

Done when `git status` is clean, `main` holds everything, and gitleaks reports nothing.

### Phase 1: the repo and its rules

Everything below except the **[user]** items is written and waits in the repo:
`bash .github/setup-repo.sh <org>` creates the public repo, pushes `main`, and applies the
settings, the ruleset and the labels. Run it as soon as the org exists.

- [x] Org `KatakiRPAI` created by the user; the script run on 2026-09-29.
- [x] Repo files: `SECURITY.md`, `CONTRIBUTING.md`, issue templates (bug, idea, beta
      feedback; security goes to private reporting), PR template (what changed, how it was
      checked, risk), `.github/CODEOWNERS`.
- [x] Ruleset on `main` as code (`.github/rulesets/main.json`): PR required, the four CI checks
      required and up to date, linear history (squash only), no force-push, no deletion,
      code-owner review for the paths in CODEOWNERS. Org admins may merge a PR past a missing
      review (so the user can merge their own PRs until the bot exists) but can't push
      directly. Tag ruleset: Phase 4, with the release workflow.
- [x] Settings in the script: secret scanning + push protection, Dependabot alerts and
      security PRs, private vulnerability reporting, squash-only with the PR title as the
      commit, delete branch on merge, auto-merge allowed.
- [x] Bot account `QaisBOT` in the org; `setup-repo.sh` gives it write access (never admin, so
      it can't bypass the ruleset). Agents run git and gh as the bot through
      `.github/as-bot.sh`, which borrows the bot's gh login for one command.
- [ ] **[user]** Log the bot into gh once; turn on 2FA for QaisBOT and require it org-wide.

Done when a direct `git push origin main` is rejected and a PR shows the required checks.

### Phase 2: CI (`.github/workflows/ci.yml`)

Written 2026-09-29, checked with actionlint and zizmor; first real run on the first push.

- [x] `engine`: `uv sync --locked`, ruff check + format check, pytest; Windows and Ubuntu.
- [x] `app`: pnpm install (frozen lockfile), `typecheck`, `build` (runs `checks/copy.mjs`),
      `build:web`; the web build is a PR artifact for 7 days.
- [x] `smoke`: `pnpm smoke` on Windows (Electron end to end).
- [x] Runs on `pull_request`, `push` to `main`, and `merge_group`. Top-level
      `permissions: {}`, actions pinned by SHA, `concurrency` cancels superseded PR runs.
- [ ] Installer as a PR artifact: waits for packaging (Phase 4).

Done when a PR that breaks a test cannot merge.

### Phase 3: security automation

Written 2026-09-29 (`security.yml`, `scorecard.yml`, `dependabot.yml`).

- [x] Dependabot: `uv` (engine), `npm` (app), `github-actions`; weekly, grouped minor/patch.
      Electron gets security updates only; moving its version is a reviewed PR.
- [x] CodeQL: python, javascript-typescript, actions; weekly as well as on every change.
- [x] `dependency-review` on PRs (fails on high-severity advisories).
- [x] `zizmor` on every change; Scorecard weekly.
- [x] README badges (CI, Scorecard).

Done when Scorecard publishes and the Security tab shows CodeQL results.

### Phase 4: releases and rollback

- [ ] Engine safety first (a downgrade must never damage a library): in `engine/src/kataki/db.py`
      `connect()`, take a backup (`backups.make`) before running migrations, and refuse to open a
      library whose `user_version` is above `SCHEMA_VERSION`. Today it rewrites `user_version`
      down to the older number, and the next upgrade re-runs a migration on a library that
      already has it. One test each. The minds spec's foundation owns this task
      (`docs/specs/2026-09-29-minds.md`, "Library safety").
- [ ] Packaging (M5 overlaps; share its spec): electron-builder bundles the engine; version
      comes from the tag; `generateUpdatesFilesForAllChannels: true`.
- [ ] release-please: one version for engine + app (`release-please-config.json`, manifest).
- [ ] `release.yml`: on merge to `main`, build and publish `-alpha.N`; on the release-please
      tag, publish stable with `stagingPercentage: 20`; `promote.yml` (manual) re-tags a
      chosen alpha as beta, and raises a stable rollout to 100%. Every release file gets
      `actions/attest-build-provenance` and an SBOM.
- [ ] **[user]** Apply to SignPath Foundation. Their conditions (signpath.org/terms): an
      OSI-approved licence in the repo, no commercial dual-licensing of the desktop app, a
      project that is already released (the first alphas ship unsigned), MFA for everyone on
      SignPath and GitHub, roles for authors (the bot), reviewers and release approvers (the
      user), builds made only by CI, a manual approval per signed release, and a "Code signing
      policy" section on the project page. The publisher shown to Windows users is "SignPath
      Foundation".
- [ ] Sign in `release.yml` through SignPath's GitHub action, from GitHub environment
      `release` (its secrets live only there; the environment requires the user's approval).
- [ ] App: Settings › update channel (stable / beta), electron-updater wired to GitHub Releases;
      fills the handoff's `[UPDATE HOST]`.
- [ ] `docs/releasing.md`: how to cut, promote, halt and roll back a release.

Done when an alpha installs, updates itself to the next alpha, and a halted release stops
reaching new users.

### Phase 5: agents in the loop (optional, paid)

- [ ] **[user]** `anthropics/claude-code-action` for `@claude` on issues/PRs and a review on
      every PR (API cost per run; follow the paid-API rule first).
- [ ] Weekly maintenance routine: merge green Dependabot minors, triage new issues with labels
      (`bug`, `beta-feedback`, `needs-human`, `agent-ready`), check Scorecard, prune stale
      branches, report to the user.
- [ ] Beta feedback: the in-app Feedback sheet opens a prefilled GitHub issue (fills
      `[FEEDBACK HOST]`); nothing is sent without the user pressing Send.

### Phase 6: Kataki online (the website)

The engine side is track B of `docs/specs/2026-09-29-minds.md` (§4: one engine, a `Host` seam,
many libraries per process, metering to a ledger, a credit gate, channels as feature flags on
the account). The website's own screens come from a Claude Design handoff (the user is making
it). This phase is the hosting around them; the defaults it assumes:

- **Accounts:** sign-in by passkey or email link through a hosted auth provider; no passwords
  stored by Kataki.
- **Tenancy:** each user gets their own library file, so the engine's single-user SQLite code
  runs unchanged per user; a thin gateway in front checks the session and routes to that
  user's library. Accounts, balances and the billing ledger live in one managed Postgres
  database with point-in-time recovery.
- **Models and money:** the service holds the provider keys (OpenRouter or HuggingFace); every
  model call is metered from the provider's reported usage and debited from a prepaid balance
  at cost × (1 + margin). Users top up through the payment processor's hosted checkout; the
  ledger is append-only. Spending caps per user and a global daily cap guard against runaway
  costs.
- **Payment processor:** the user's (open decision 3); build against test mode.
- **Hosting:** a container host with persistent volumes, separate staging and production apps,
  and image-based rollback (Fly.io fits; the spec confirms it). Images go to GHCR, tagged by
  commit.

Infrastructure work once the spec is approved:

- [ ] `Dockerfile` for engine + web build; image built and attested in CI on every merge.
- [ ] GitHub Environments `staging` (deploys on merge to `main`) and `production` (the user is
      the required reviewer; deploys only from `v*` tags). Each holds its own secrets; nothing
      production-grade exists outside `production`.
- [ ] `deploy.yml`: build once, deploy the same image to staging, then (after approval) to
      production; a database backup before each production deploy; a health check that rolls
      back automatically when it fails.
- [ ] Uptime check and error reporting on production; alerts go to the user.
- [ ] `docs/operations.md`: deploy, roll back, rotate a key, restore a backup, refund a user.

Done when a merge reaches staging on its own, the same image reaches production after one
approval, and a deliberately broken deploy rolls itself back.

## Out of scope until decided

- Publishing `kataki` to PyPI (trusted publishing makes it a small add once the engine is a
  library others use).
- macOS and Linux installers (add to the release matrix when someone asks; macOS needs an
  Apple developer account for notarisation).
