# Desktop profiles (P1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The desktop app keeps several profiles, each a folder holding a library, and can add, switch, rename and forget them.

**Architecture:** The Electron shell owns a `profiles.json` in its userData and starts the engine on the chosen profile's folder; the engine keeps opening exactly one library per process. Switching restarts the app, as a restored backup already does. The engine takes an OS lock beside the library so two engines never share a folder.

**Tech Stack:** Electron main process (TypeScript, Node stdlib), the Python engine (stdlib `msvcrt`/`fcntl`), React with the vendored design system. No new dependencies.

**Spec:** `docs/specs/2026-10-02-profiles-and-accounts.md` (§2, §4 decisions 1–2, §5 P1, §6).

## Global Constraints

- The page never names a path. The shell shows the folder dialog and keeps the answer.
- Forgetting a profile never deletes a file.
- A library is never created at a path the user did not just choose.
- `KATAKI_DB` and `--smoke` bypass profiles (CI and the demo library keep working).
- Every string a component shows comes from `app/src/strings/en.json` through `t()`.
- No new dependencies. `pnpm check` passes.
- Windows scripts write `\n` line endings.

---

### Task 1: The engine's library lock

**Files:**
- Create: `engine/src/kataki/lock.py`
- Modify: `engine/src/kataki/__main__.py` (`serve`, after the hello line and before `backups.apply_pending`)
- Test: `engine/tests/test_lock.py`

**Interfaces:**
- Produces: `lock.hold(folder: Path) -> IO` (keeps `folder/library.lock` locked while the returned file is open; raises `lock.InUse`), and `kataki serve` exiting 4 after printing `{"error": {"code": "LIBRARY_IN_USE", "message": …}}` as its second line.

- [ ] Test: `hold(tmp)` succeeds; a second `hold(tmp)` while the first is open raises `InUse`; after closing the first, `hold(tmp)` succeeds again.
- [ ] Run `uv run pytest tests/test_lock.py -q` and see it fail on the import.
- [ ] Implement: open `library.lock` with `a+`, `seek(0)`, then `msvcrt.locking(fd, LK_NBLCK, 1)` on Windows or `fcntl.flock(f, LOCK_EX | LOCK_NB)` elsewhere; on `OSError` close and raise `InUse`.
- [ ] Call it in `serve` and keep the handle in a local for the life of the process.
- [ ] Run the test, then `uv run ruff check . && uv run ruff format --check .`
- [ ] Commit `feat(engine): a lock so two engines never open one library`.

### Task 2: The profile list

**Files:**
- Create: `app/electron/profiles.ts`, `app/electron/profiles.check.ts`
- Modify: `app/electron/tsconfig.json` (include `profiles.ts`)

**Interfaces:**
- Produces, from `profiles.ts` (Node stdlib only, erasable TypeScript so `node` can run the check):
  - `type Profile = { id: string; name: string; folder: string }`
  - `type Profiles = { last: string; profiles: Profile[] }`
  - `load(file: string, first: Profile): Profiles`: the file's list, or `{last: first.id, profiles: [first]}` when it is missing, unreadable or empty.
  - `save(file: string, p: Profiles): void`
  - `current(p: Profiles): Profile`: the `last` one, else the first.
  - `kind(folder: string): 'library' | 'empty' | 'other' | 'missing'`: has a `library.db`; exists with nothing in it; exists with other files; does not exist.
  - `synced(folder: string): string | null`: `'OneDrive' | 'Dropbox' | 'iCloud' | 'Google Drive' | 'a network drive'` by path segment or a `\\` / `//` prefix, else null.
  - `add(p: Profiles, name: string, folder: string): { profiles: Profiles; profile: Profile; existing: boolean }`: a folder already listed (compared resolved, case-insensitive on Windows) returns that profile.
  - `rename(p: Profiles, id: string, name: string): Profiles`
  - `forget(p: Profiles, id: string): Profiles`: throws for the current profile.
  - `cleanName(name: unknown): string`: trimmed, at most 40 characters, `'Profile'` when empty.

- [ ] Write `profiles.check.ts` (run with `node app/electron/profiles.check.ts`) asserting each line above in a temp folder, including: a corrupt file loads the fallback; `add` twice on one folder returns `existing: true` and one entry; `forget` of the current throws; `synced('C:\\Users\\a\\OneDrive\\Kataki') === 'OneDrive'`, `synced('\\\\nas\\share')` is the network answer, `synced('D:\\Kataki')` is null.
- [ ] Run it and see it fail; implement; run it and see `profiles: ok`.
- [ ] Commit `feat(app): the desktop's list of profiles`.

### Task 3: The shell starts the engine on a profile

**Files:**
- Modify: `app/electron/main.ts`, `app/electron/preload.cts`, `app/src/kataki.d.ts`

**Interfaces:**
- Consumes: Task 2's functions; Task 1's exit code 4 (and the existing 3, `LIBRARY_TOO_NEW`).
- Produces on `window.kataki` (absent when `KATAKI_DB` or `--smoke` bypasses profiles):
  - `profiles(): Promise<{ current: string; list: Profile[] }>`
  - `profileAdd(name: string): Promise<Profile | null>`: the shell asks for the folder; null when cancelled.
  - `profileSwitch(id: string): void`: restarts on that profile.
  - `profileRename(id: string, name: string): Promise<Profile[]>`
  - `profileForget(id: string): Promise<Profile[]>`

- [ ] `home` is `KATAKI_HOME` when set, else `<repo>/.dev`. The first profile is `{id: 'main', name: 'Main', folder: home}`; when `profiles.json` does not exist yet, create `home` and write the file.
- [ ] Before starting the engine: while the chosen profile's folder is `missing`, ask with `dialog.showMessageBoxSync` (Retry · Find the folder · each other profile, up to three · Quit). "Find the folder" accepts only a folder whose `kind` is `library`.
- [ ] `startEngine(token, folder)` passes `--db <folder>/library.db`. An engine exit with code 3 or 4 asks the same way (no Retry for 3), then restarts on the pick.
- [ ] `profileAdd`: `dialog.showOpenDialog({properties: ['openDirectory', 'createDirectory']})`; a folder of `kind` `other` is refused with a message and the dialog opens again; a `synced` folder gets a warning with "Choose another folder" and "Use it anyway".
- [ ] `tsc -p electron --noEmit` passes.
- [ ] Commit `feat(app): the shell opens the chosen profile's library`.

### Task 4: Settings › Profiles

**Files:**
- Create: `app/src/sky/settings/Profiles.tsx`
- Modify: `app/src/sky/Settings.tsx` (a `profiles` panel, listed only when `window.kataki?.profiles` exists), `app/src/strings/en.json` (`set.n.profiles`, `pf.*`)

**Interfaces:**
- Consumes: Task 3's `window.kataki` methods.

- [ ] The panel: a callout saying what a profile is and what profiles share (models, keys); one row per profile (name, folder; "Open now" on the current one, else Switch; Rename; Forget, with a confirm that says the files stay); Add (a name, then the shell's folder dialog), with a toast offering to switch to it.
- [ ] `pnpm -C app typecheck` and `node app/checks/copy.mjs` pass.
- [ ] Look at it in the real app on a scratch `KATAKI_HOME` and userData: add a second profile, make a story in it, switch back and forth.
- [ ] Commit `feat(app): Settings › Profiles`.

### Task 5: Land it

- [ ] Add the P1 Progress line to the spec. `pnpm check`. Push as the bot, open the PR with the template filled in, merge when green, report.
