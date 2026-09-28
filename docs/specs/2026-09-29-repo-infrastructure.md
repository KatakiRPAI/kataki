# Repo infrastructure: GitHub, CI, release channels, security

Kataki moves from one local branch (`m0-scaffold`, never pushed) to a public GitHub repo with
protected `main`, CI on every change, alpha → beta → stable release channels, rollback, and
security scanning. AI agents maintain this repo, so each rule here is enforced by GitHub and
not only written down. [`AGENTS.md`](../../AGENTS.md) holds the day-to-day rules; this file
holds the plan and its Progress.

## Progress

Update this list as phases land (date · phase · what changed · anything left). Items marked
**[user]** need the user; an agent prepares them and asks.

- 2026-09-29 · plan written; `AGENTS.md` added, `CLAUDE.md` now imports it. Nothing pushed yet.

Open decisions (defaults an agent may assume until the user answers):

1. **[user] Owner.** Default: a new GitHub organisation (e.g. `kataki-rpai`) owning `kataki`.
   An org gives a bot identity and a clean handover later. A personal repo (`QaisZAK/kataki`)
   also works.
2. **[user] Commit email.** All 149 commits carry `OLD-EMAIL`, which becomes
   public on push. Keep it, or rewrite history to the GitHub noreply address with
   `git filter-repo` before the first push. A rewrite changes every hash, so hashes quoted in
   `docs/specs/` (e.g. `c30c089`) stop resolving. Default: ask; do not push until answered.
3. **[user] Public from day one.** Default: yes. Rulesets, secret-scanning push protection,
   CodeQL and free Actions minutes are free only on public repos (private ones need GitHub
   Pro/Team).
4. **[user] Bot identity for agents.** Default: a GitHub App (or machine user) that agents push
   and open PRs as. Without it every agent PR is authored by the user, and GitHub will not let
   the user approve their own PR, so "human approval" rules cannot work.
5. **[user] A hosted website.** The web build exists, but the engine is single-user, binds
   127.0.0.1, and has no accounts. A public "live" site needs a multi-user design (its own spec).
   Default: until then, "production" means the installed desktop app, and the only hosted page
   is a static project site on GitHub Pages.
6. **[user] Paid pieces.** Windows code signing (SignPath Foundation's free OSS programme, or
   Azure Artifact Signing, ~$10/month) and Claude running in Actions (API cost per run). Default:
   unsigned alpha builds until the user picks one.

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

[ch]: https://www.electron.build/tutorials/release-using-channels.html
[rs]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
[rp]: https://github.com/googleapis/release-please
[sc]: https://github.com/ossf/scorecard-action
[sp]: https://signpath.io/solutions/open-source-community
[ms]: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
[am]: https://www.morphllm.com/agents-md-guide

## Target shape

| Environment | What it is | How code gets there | Who gets it |
|---|---|---|---|
| dev | `pnpm dev` on the `.dev/` library, the fake model (`engine/evals/demo.py`) | a branch | the agent or user working |
| PR preview | installer + web build uploaded as a CI artifact on each PR | open a PR | whoever reviews |
| alpha | pre-release `vX.Y.Z-alpha.N`, updater channel `alpha` | every merge to `main` | the user (dogfood) |
| beta | pre-release `vX.Y.Z-beta.N`, channel `beta` | "Promote" workflow on a green alpha | opted-in beta users (Settings › update channel) |
| stable | release `vX.Y.Z`, channel `latest`, staged rollout 20% → 100% | merging the release-please PR | everyone |

**Rollback** is roll-forward plus a stop button:

1. Stop the rollout: set `stagingPercentage: 0` in the release's `latest.yml` (or mark the
   release draft), so no one else updates.
2. Revert the bad commit on `main` (a PR like any other), release the next patch.
3. User data survives because the engine backs up the library before any schema migration and
   refuses to open a library newer than itself (both owed, Phase 4).

## Phases

Each phase ends in something checkable. Do them in order.

### Phase 0: clean up before anything is public (local only)

- [ ] Whoever owns the ~200 uncommitted changes and untracked files on `m0-scaffold` commits
      or discards them (parallel sessions left them; commit nothing you did not write).
- [ ] Keep the old designs out of git: `docs/design/` (98 MB) and
      `docs/kataki-design/**/screens/png/` (39 MB) go in `.gitignore`, or into a release asset
      if they must be shared. The handoff (`docs/handoff/`) is the source of truth.
- [ ] Move root `reports/` and `research_notes/` into `docs/research/`.
- [ ] Settle branch `claude/bold-fermi-0b6972` (commit `e3813bb`, not on `m0-scaffold`): merge
      or delete it; prune its dead worktree (`git worktree prune`).
- [ ] Run `gitleaks detect` over full history. (A pattern scan on 2026-09-29 for HF, OpenAI,
      GitHub and AWS keys found nothing; `.env` has always been ignored.)
- [ ] **[user]** Answer decisions 1 and 2; rewrite authorship if chosen.
- [ ] Fast-forward `main` to `m0-scaffold` (`main` is its ancestor), then delete `m0-scaffold`.

Done when `git status` is clean, `main` holds everything, and gitleaks reports nothing.

### Phase 1: the repo and its rules

- [ ] **[user]** Create the repo (decision 1), `git remote add origin`, push `main`.
- [ ] Repo files: `SECURITY.md` (private vulnerability reporting on), `CONTRIBUTING.md`
      (points to `AGENTS.md`; humans and agents follow the same rules), issue templates
      (bug, feature, beta feedback), PR template (what changed, how it was checked, risk),
      `.github/CODEOWNERS`.
- [ ] Ruleset on `main`: PR required, required checks (Phase 2's jobs), linear history
      (squash only), no force-push, no deletion, no bypass for anyone including admins. Tag
      ruleset: only the release workflow creates `v*` tags.
- [ ] Settings: secret scanning + push protection, Dependabot alerts, private vulnerability
      reporting, delete branch on merge, auto-merge allowed.
- [ ] **[user]** Bot identity (decision 4); agents' `gh` uses it.

Done when a direct `git push origin main` is rejected and a PR shows the required checks.

### Phase 2: CI (`.github/workflows/ci.yml`)

- [ ] `engine`: `uv sync`, ruff check + format check, pytest; Windows and Ubuntu.
- [ ] `app`: pnpm install (frozen lockfile), `typecheck`, `build` (runs `checks/copy.mjs`),
      `build:web`.
- [ ] `smoke`: `pnpm smoke` on Windows (Electron end to end).
- [ ] Runs on `pull_request`, `push` to `main`, and `merge_group`. Top-level
      `permissions: {}`, actions pinned by SHA, `concurrency` cancels superseded runs.
- [ ] PR preview: upload the unsigned installer and `dist-web` as artifacts (7-day retention).

Done when a PR that breaks a test cannot merge.

### Phase 3: security automation

- [ ] `.github/dependabot.yml`: `uv` (engine), `npm` (root + app), `github-actions`; weekly,
      grouped minor/patch. Electron stays pinned; its majors are a human-reviewed PR.
- [ ] `codeql.yml`: python, javascript-typescript, actions.
- [ ] `dependency-review` on PRs (fails on high-severity advisories).
- [ ] `zizmor` on workflow changes; `scorecard.yml` weekly with the README badge.

Done when Scorecard publishes and the Security tab shows CodeQL results.

### Phase 4: releases and rollback

- [ ] Engine safety first (a downgrade must never damage a library): in `engine/src/kataki/db.py`
      `connect()`, take a backup (`backups.make`) before running migrations, and refuse to open a
      library whose `user_version` is above `SCHEMA_VERSION`. Today it rewrites `user_version`
      down to the older number, and the next upgrade re-runs a migration on a library that
      already has it. One test each.
- [ ] Packaging (M5 overlaps; share its spec): electron-builder bundles the engine; version
      comes from the tag; `generateUpdatesFilesForAllChannels: true`.
- [ ] release-please: one version for engine + app (`release-please-config.json`, manifest).
- [ ] `release.yml`: on merge to `main`, build and publish `-alpha.N`; on the release-please
      tag, publish stable with `stagingPercentage: 20`; `promote.yml` (manual) re-tags a
      chosen alpha as beta, and raises a stable rollout to 100%. Every release file gets
      `actions/attest-build-provenance` and an SBOM.
- [ ] **[user]** Signing (decision 6), then sign in `release.yml` via GitHub environment
      `release` (secrets live only there; the environment requires the user's approval).
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

## Out of scope until decided

- A multi-user hosted Kataki (decision 5).
- Publishing `kataki` to PyPI (trusted publishing makes it a small add once the engine is a
  library others use).
- macOS and Linux installers (add to the release matrix when someone asks; macOS needs an
  Apple developer account for notarisation).
