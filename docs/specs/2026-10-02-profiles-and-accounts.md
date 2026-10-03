# Profiles, accounts and cloud

The owner, 2026-10-02: profiles and users on both products. On the desktop a profile can be a
folder that holds everything; a desktop user can also bring a library from the cloud, free up
to a number of characters, places, plots and stories. Online there are real accounts: Google,
Discord, GitHub, Apple, and email or username with a password; two-factor, backup codes, a
backup email, magic links, account management, deletion. Everyone gets full settings and a
profile they can customise, with badges from achievements defined later.

Research: `docs/research/reports/Profiles accounts and cloud.md`.

**This spec overrides** three older lines, at the owner's word:

- `docs/design-brief-3.md` S1 and infrastructure Phase 6: "No passwords, ever". Passwords are in.
- The handoff README's "account systems, sync … are out of scope". They are in scope here.
- `da.privacyBody`'s "No account, no sync": still true by default; it gains "unless you sign in"
  when the cloud slices land.

## Progress

- [x] Research and this spec (2026-10-02).
- [x] P1 · Desktop profiles (2026-10-02): the shell keeps `profiles.json` and opens the last
      profile's folder; Settings › Profiles adds, switches, renames and forgets; the engine holds
      `library.lock` and a second engine on the folder exits 4 (`LIBRARY_IN_USE`). Checked in the
      real app on a scratch home: two profiles, switch there and back, the lock refusing a second
      engine. Not clicked through: the native dialogs (the folder picker, a missing folder, a
      library that will not open). A profile whose folder once held a library and no longer
      does is asked about like a missing folder (`opened` in `profiles.json`). Owed: the
      dialogs' text is English in `main.ts`, outside `strings/`.
- [x] P2 · The profile card (2026-10-02): the `profile` setting (name, pronouns, bio, picture,
      colour) and `GET /profile/stats`, shown at the top of You with an edit dialog; saving it
      renames the desktop profile to match. Not done: a banner; a `/profile` page or Settings
      panel of its own (it lives on You until there are boards). An import online keeps the
      service's keys (`archive.SERVICE_SETTINGS`: `prices`) and brings the person's settings,
      card included (2026-10-03; it dropped them before).
- [x] P3 · Badges (2026-10-02): schema v19 `achievements`; `achievements.py` holds the rules
      (a number from `profile.stats` and a target) and `POST /achievements/check` awards them.
      What a library already held at the first look is backdated and never announced. The card
      shows earned badges, a list of all with progress, Hide per badge, and an off switch in
      the edit dialog; a toast says a badge was earned when you are back in the Sky, never in
      a scene. The 16 rules are a starter set: **[owner]** defines the real list. Not done:
      tiers, hidden badges, a pinned showcase.
- [x] P4 · Move, startup, PIN (2026-10-02): Settings › Profiles moves the open library to an
      empty folder (copied and compared at the restart, with nothing open; the old folder is
      left until the person deletes it), can ask which profile each time Kataki starts, and
      sets a PIN on a profile (4 to 12 digits, kept as a salted scrypt hash; a wrong guess costs
      a second). The picker is the shell's own small window (`picker.html`), shown before any
      library opens. A PIN is privacy on this computer, not encryption, and the screens say so.
      Not done: the discreet list (type the name instead of choosing it); the picker's and the
      dialogs' text is English in the shell, outside `strings/`.
- [ ] P5 · Settings, completed. Content (2026-10-03): Settings › General › Stories sets how far
      stories go (Gentle, Mature by default, Explicit) and topics to keep out; every reply's
      rules carry them (`context.content`), with a line about minors that no level removes.
      Explicit on the desktop asks for 18 or older once; online accounts already said so.
      A per-story level (2026-10-03): the story's settings sheet sets "How far this story goes"
      (As in Settings, Gentle, Mature, Explicit; `overrides.content`), which wins over the
      library's; Explicit is offered only where 18 or older is already said. The sheet no longer
      offers a per-story model online. Not done: hiding characters by tag; a settings-only export.
- [x] A0 · The gateway's spec: `docs/specs/2026-10-02-kataki-online.md` (2026-10-02). The owner
      chose Better Auth. A1–A6 are its G1–G6, and their progress is kept there.
- [ ] A1–A6 · Accounts: A1 (G1) done; see the gateway spec.
- [ ] C1–C2 · Cloud for the desktop: C1 done (2026-10-02), see the gateway spec §8; C2 (the free
      limit and the storage charge) waits for the owner's numbers.

## 1. What the owner is after

1. **A person owns the library, not an install.** Today there is one library at a fixed path
   and nobody's name on it.
2. **On the desktop, a profile is a folder.** Point Kataki at a folder and everything in it is
   there: characters, places, plots, stories, settings. Keep several; switch between them; put
   one on another drive.
3. **The desktop can reach the cloud.** Sign in to a Kataki account from the desktop app and
   send the library up or bring it down. Free to a limit, paid storage past it.
4. **Online, an account is a real account,** with the sign-in methods people expect and the
   safety a balance and private writing deserve.
5. **A profile is yours to dress:** a name, a picture, a few words, a colour, badges you earned.
6. **Settings cover all of it.**

## 2. The model

```
desktop                                   online
───────                                   ──────
profiles.json (the shell's userData)      account (the gateway's Postgres)
  └ profile → folder                        ├ sign-in methods, sessions, 2FA
       └ library.db, blobs/, backups/       ├ balance, ledger
            └ settings['profile']           ├ handle
            └ achievements                  └ library id → <root>/<id>/library.db
                                                 └ settings['profile'], achievements
        cloud slot (C1): a desktop profile signed in to an account
        uploads or downloads the whole library as a .kataki snapshot
```

- **Library:** unchanged. One folder: `library.db`, `blobs/`, `backups/`.
- **Profile:** who you are, kept *inside* the library (the `profile` setting), so it travels
  with an export, a move and a cloud snapshot, and is the same object on both products. A
  profile is not a persona: personas are who you play in a story; the profile is you.
- **Desktop profile list:** `profiles.json` in the shell's userData: `{last, profiles: [{id,
  name, folder}]}`. It only says where the folders are; the name is a copy for the list.
- **Account** (online only): lives in the gateway's Postgres. One account, one library. The
  engine never sees a password or a session: it keeps seeing `X-Kataki-User` (minds spec §8.4).
- **What profiles on one computer share:** downloaded models (`KATAKI_HOME/models`) and API keys
  (the OS keychain, by provider name). Profiles are separate libraries for one person or a
  trusting household. They are not a wall between people: the files are readable on disk.

## 3. What to build

### Core

| Area | What |
|---|---|
| Desktop profiles | Several profiles, each a folder. Add (a new folder, or one that already holds a library), switch, rename, forget (never deletes files). Opens the last used |
| Folder safety | A lock so two engines never open one library. A warning for OneDrive, Dropbox, iCloud, Google Drive and network paths. A missing folder asks (Retry, Locate, another profile) and never creates an empty library there |
| Profile card | Display name, picture, bio, pronouns, accent colour. Private. Stats: stories, characters, words written, days active |
| Badges | Rules over library data, re-runnable; a silent backfill; a global off switch; hide any badge |
| Account sign-in | Email or username with a password; magic link; Google, GitHub, Discord, Apple. Email verification before anything is held |
| Account safety | Everything in the research report §7 Core: breached-password check, Argon2id, no enumeration, linking only when both sides are verified, confirm-button magic links, hashed session tokens, change notices, throttling, an 18+ attestation |
| Account management | Change email (confirm new, notify old, undo), change password, linked sign-in methods, sign out, delete the account (grace period, export first), export everything |
| Cloud slot | Sign in from the desktop; upload or download the whole library; a revision check; a local backup before either side is replaced |

### Nice to have

| Area | What |
|---|---|
| Profile | Banner, a pinned showcase of badges, a handle |
| Badges | Tiers, a few hidden ones |
| Desktop | Choose a profile at startup; hide the list ("discreet"); a PIN, labelled as privacy and not encryption |
| Account | TOTP with backup codes; passkeys; a backup email; the session and device list; sign out everywhere; sudo mode for sensitive changes; a new-device email |
| Cloud | The last 3–5 snapshots kept; automatic upload on a schedule |
| Settings | Content preferences (how mature, blocked tags) |

### Quality of life

- Move a library to another folder from Settings (copy, verify, switch, offer to delete the old).
- Switch profile from the top bar, not only from Settings.
- One toast for several badges earned at once.
- A settings-only export.
- "This library is open on {computer}" when the lock is held.
- The cloud's limit shown as counts, with what is used.

### Later

- A shareable public profile, with badges the server computed and rarity percentages.
- Per-item cloud sync (a story, a character) instead of whole snapshots. Needs stable ids,
  `updated_at` and tombstones on every row.
- An end-to-end encrypted backup slot, desktop-only.
- Risk-based sign-in challenges.

### Not building

- Custom CSS on profiles (JanitorAI's broke under a security fix).
- Streaks, or any reminder that plays on guilt.
- Badges that grant credit or anything worth money.
- A password on a desktop profile that claims to protect files it does not encrypt.
- Team or shared accounts.

## 4. Decisions

Defaults chosen so the work can move. The owner can change any of them; the ones marked
**[owner]** need the owner before the slice that uses them.

1. **One word, "profile".** On the desktop a profile is a name and a folder; its card lives in
   that folder's library. Online a profile belongs to an account. Not "user", not "vault".
2. **The profile list belongs to the shell,** in `profiles.json`. The engine keeps opening
   exactly one library per process. Switching restarts the app on the other folder, as a
   restored backup already does.
3. **Sign-in stack: Better Auth,** in the gateway, on the gateway's Postgres (research §6). It
   costs nothing per user, no vendor can lock users out, and it covers the list bar the backup
   email. Runner-up: Ory Kratos. A hosted provider (Clerk) only if the owner would rather pay
   than run it. This makes the gateway a small TypeScript service; A0 settles that with the
   ledger. **[owner]**
4. **Passwords are allowed,** 12 characters at least, checked against breached lists, with 2FA
   offered right after sign-up. Magic link and passkey stay the suggested ways in.
5. **Cloud is a snapshot slot with versions,** not live sync (research §5). It reuses the
   `.kataki` archive and the per-account library the hosted engine already has.
6. **The free limit is shown as counts** (`[FREE CHARACTERS]`, `[FREE PLACES]`, `[FREE PLOTS]`,
   `[FREE STORIES]`) with a byte ceiling behind it as the abuse guard. Past it, storage is
   charged to the credit balance per GB-month; no subscription. Over the limit or out of
   credit: uploads stop, downloads always work, nothing is deleted for 30 days. **[owner]**:
   the numbers.
7. **Desktop badges are personal.** Anything shown to someone else is computed online from a
   library the server holds; a library uploaded from a desktop earns its badges as `backdated`.
8. **No end-to-end encryption now.** It would stop the website from opening the library.

**The owner's to do** (agents cannot): the Apple Developer Program; OAuth apps at Google,
GitHub, Discord and Apple; a domain and a mail sender; the challenge keys for sign-up; the free
limits and the storage price; boards for the new screens (profile list, profile card, badges,
sign-in with passwords and social buttons, Settings › Account, cloud). Until boards arrive the
screens are built from existing design-system components and say so in their PRs.

## 5. Slices

Show-first: each ends on screen, in a PR. Desktop slices first; they need nothing from the owner.

### P1 · Desktop profiles

- `app/electron/profiles.ts`: read and write `profiles.json`; add, rename, forget, pick; what
  kind of folder a path is (`library` · `empty` · `other`) and whether it is cloud-synced.
  Checked by `app/electron/profiles.check.ts`.
- `app/electron/main.ts`: start the engine on the chosen profile's folder. `KATAKI_DB` and
  `--smoke` bypass profiles. A missing folder or an engine that will not open the library asks
  with a native dialog (Retry, Locate, another profile, Quit).
- Engine: `library.lock` beside `library.db`, held by an OS lock for the life of `serve`. A
  second engine on the folder exits 4 with `LIBRARY_IN_USE`. Not in hosted mode.
- Settings › Profiles (desktop only): the list, which one is open, Add, Switch, Rename, Forget.
- Done when two profiles hold different stories and switching shows each.

### P2 · The profile card

- `settings['profile']`: `{name, pronouns, bio, portrait, focus, zoom, alt, accent, banner}`.
- `GET /profile/stats`: stories, characters, places, words written, days active, since.
- `/profile` page and Settings › Profile; the picture reuses Crop. The desktop list takes its
  name from the card.

### P3 · Badges

- Migration: `achievements(key PRIMARY KEY, earned_at, backdated)`.
- `achievements.py`: a table of rules (`key`, group, tiers, a query over the library), evaluated
  on `GET /achievements`; newly met rules are stored and returned once as `new`. The first run
  on an existing library stores everything as `backdated` and returns nothing new.
- The starter set: the "cheap" rows of research §2.
- The card shows badges; `profile.badges = {off, hidden[], showcase[]}`.

### P4 · Move, startup, privacy

- Move a library (`VACUUM INTO`, copy pictures, `integrity_check`, switch, offer to delete).
- Choose at startup; discreet list; PIN (privacy, not encryption; forgetting it means opening
  the folder as a new profile, which the copy says).

### P5 · Settings, completed

- Content preferences; a settings-only export; anything P1–P4 left without a control.

### A0 · The gateway spec

- `docs/specs/…-kataki-online.md`: the gateway (sign-in, sessions, signing requests to the
  engine, `/allow`, `/usage`, the ledger, top-ups), its language, `docker compose` for dev, and
  the deploy. Decision 3 is settled there.

### A1–A6 · Accounts

- A1 · Email or username with a password; verification; sessions; sign-in and sign-up screens
  in the web build; the 18+ attestation.
- A2 · Magic links; password reset; change notices; throttling.
- A3 · Google, GitHub, Discord, Apple, with the linking rules.
- A4 · TOTP and backup codes; sudo mode; passkeys.
- A5 · Settings › Account: emails (with the backup email), methods, sessions, export, deletion
  with its grace period.
- A6 · Handles; the online profile; server-computed badges.

### C1–C2 · Cloud for the desktop

- C1 · Sign in from the desktop (the system browser, back on a loopback address); upload and
  download; revisions; kept versions; the conflict dialog.
- C2 · The free limit, the storage meter, the charge to the balance.

## 6. Rules that hold throughout

- The engine never handles a password, a session or a provider token. Online it trusts only the
  gateway's signed headers.
- The page never names a path. The shell shows the folder dialog and keeps the answer.
- Forgetting a profile never deletes a file. Deleting a library is its own, typed-to-confirm act.
- A library is never created at a path the user did not just choose.
- Schema changes follow AGENTS.md: forward-only, each with a test from the previous version.
