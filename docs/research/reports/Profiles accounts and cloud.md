# Profiles, accounts and cloud storage for Kataki

Researched 2026-10-02 for `docs/specs/2026-10-02-profiles-and-accounts.md`. Four threads: the
sign-in stack, what a correct account system must do, profiles and badges in comparable
products, and library folders plus cloud storage. Items marked *(unverified)* could not be
confirmed from a first-party source on the day.

## 1. What comparable products do

| Product | Profile and persona | Account and data | What users complain about |
|---|---|---|---|
| Character.AI | Public profile (username, display name, avatar, bio) is separate from personas (several, one default, per-character override) | Deletion with a 30-day cool-off | "Lost" chats, export *(export unverified)* |
| JanitorAI | Free-form "About me" with custom CSS; a security fix broke designs in June 2026 | 2026 changelog: editable usernames, active-sessions list, badge visibility, 30-day restorable deletion | No built-in chat export; users rely on userscripts |
| Chub | Username, avatar, NSFW and NSFL toggles, blocked tags, personas | No self-serve deletion found | |
| SillyTavern | Multi-user: a handle per user, data at `DATA_ROOT/handle`, a login screen that lists users or hides them ("discreet login"), skipped when there is one passwordless user | Per-user backup zip | Passwords are documented as "not a security feature": the data is plain text on disk |
| NovelAI | No social profile | Stories encrypted client-side; a lost password loses the stories | |
| AI Dungeon | Three safety levels, an 18+ confirmation, a 4-digit PIN lock, muted content | | |
| Backyard AI | Desktop app deprecated 2025-06-25 | Bulk export was the migration path | Stranded desktop users |
| RisuAI | No profile | Backup to Google Drive, a file or your own server | Want a settings-only backup |
| Replika, Nomi, Kindroid | | Export by support email only | |
| Discord | Display name separate from username, pronouns, 190-character bio, banner, two-colour theme | | |
| Steam | Showcases (pinned or rarest achievements), global unlock percentage | | |

Two patterns hold everywhere. The account profile and the in-story persona are separate
objects. The loud complaints are about export, lost chats and deletion, not about customisation.

## 2. Badges that do not backfire

- **Badges steer behaviour.** On Stack Overflow, activity speeds up toward a badge threshold and
  drops after it (Anderson et al., WWW'13). Badge only what the product wants more of.
- **Ship the off switch on day one.** GitHub's achievements rewarded dubious behaviour (merging
  without review) and drew complaints until it added a global opt-out and per-badge hiding.
- **No streaks.** They work through loss aversion and produce anxiety. Count cumulative days
  active; never a breakable streak, never a guilt notification.
- **Rarity** (Steam's global percentage) needs server-side aggregates, so it is website-only.
- **Hidden achievements:** few, quirky, never a grind; revealable on demand.
- **Award from rules over data, not from unlock calls scattered in code.** Rules must be
  re-runnable over an existing library; backfill silently (no flood of toasts), idempotent on a
  unique key, with a `backdated` flag.
- **Cheat resistance.** Steam achievements are client-set and trivially unlocked. Desktop badges
  are personal and unverified. Anything shown publicly must be computed on the server from
  data the server holds. Never tie credits or money to a badge.
- AO3 has no badges on purpose; Royal Road tiers writing milestones (word counts I–V).

Starter list (cheap = computable from data the library already has):

| Group | Badge | Cost |
|---|---|---|
| First steps | First message · first character · first story · first place | cheap |
| Writing | 1k / 10k / 100k words written by you; 100 / 1k / 10k messages; one reply over 500 words | cheap |
| Building | 5 and 25 characters; a world of 5+ places; a character with every field filled; a story with a cast of 3+ | cheap |
| Long-running | A story active on 30 and 100 distinct days; a story past 1,000 messages; back to a story after 30+ days; a story older than a year | cheap |
| Minds | A character recalled something from 100+ messages ago; a relationship changed; you corrected a memory | new tracking |
| Variety | 3 personas played; 3 models used; a local and an online model both used | cheap |
| Collection | First card imported; 10 imports; first export or backup | mostly cheap |
| Hidden | A message between 3 and 5 am; 20 takes on one reply; 5 lines queued at once | mixed |

## 3. Several profiles on one computer

- **Firefox** (2025 rebuild): name, avatar and colour per profile; an optional "choose at
  startup" window, else the last used. No password, and users ask for one.
- **Chrome:** avatar grid at startup.
- **Steam Family View:** a PIN gates the interface; it does not protect the data.
- **Obsidian:** the vault picker draws complaints for a delete button next to open and too many
  clicks to switch.
- **Anki:** switching is buried in a menu.
- **What they get wrong:** implying a PIN is security when the data sits unencrypted on disk, no
  PIN recovery, destructive actions inside the picker, forcing a picker on one-profile installs.

## 4. A library in a folder the user picks

- **Cloud-synced folders and network shares corrupt SQLite.** Sync clients upload `library.db`
  and its `-wal` separately and mid-transaction; WAL does not work over a network filesystem
  (sqlite.org, "How To Corrupt An SQLite Database File", and wal.html). Zotero ("extremely
  likely to corrupt your database"), Anki and Calibre all warn against it.
- **Two instances on one folder.** Lightroom writes a lock file beside the catalog; a stale one
  after a crash needs deleting by hand. An OS-level lock held by the process has no stale state.
- **Copying a live database** needs `VACUUM INTO` or the backup API, not a file copy.
- **A missing folder** (a removable drive) must never be answered by silently creating an empty
  library at that path.
- **Moving:** close, `VACUUM INTO` the new folder, copy pictures, `PRAGMA integrity_check`,
  switch the pointer, then offer to delete the old copy.

## 5. Cloud storage for a local-first app

From simplest to hardest:

1. **A snapshot slot:** upload or download the whole library, one side wins (AnkiWeb's full
   sync, Steam Cloud). Reuses the `.kataki` archive Kataki already has.
2. **Snapshots with versions:** the same, keeping the last few. This is what makes "replace"
   forgivable.
3. **Per-item push and pull,** last writer wins, with tombstones. Needs stable ids, `updated_at`
   and deletion records across characters, stories and memories.
4. **Changeset replication** (SQLite session extension, Litestream, libSQL replicas, PowerSync).
   The session extension cannot carry FTS tables; the rest assume one writer or a central
   Postgres.
5. **CRDTs:** for concurrent co-editing, a poor fit for one person's append-mostly chat.

For one person on one or two machines, 1 and 2 together are right; 3 is the upgrade path; 4 and
5 are not worth their cost.

**Conflict.** Keep a `revision` on both sides and the `base_revision` the local copy came
from. If the server moved past the base: "The online library is newer (date, device, counts)",
with Download, Upload and replace, Cancel. Back up locally before either.

**End-to-end encryption.** NovelAI derives the key from the password; a reset loses the remote
stories. It would also stop the website from opening that library, which is the point of Kataki
online. Later, at most, as an opt-in "encrypted backup, desktop-only" slot.

**How others meter storage.** Bytes are the norm (Obsidian Sync 1 GB at $4–5/mo; Zotero 300 MB
free, 2 GB $20/yr; Joplin Cloud 2 GB €2.99/mo; AnkiWeb free with a 100 MB compressed cap).
Counts appear as plan shape (vaults, memory slots). Counts are easier to understand; bytes are
what costs money. At the limit the pattern is: block new uploads, never delete, always allow
download.

**What storage costs.** Cloudflare R2 $0.015/GB-month, Backblaze B2 about $0.007, Tigris (on
Fly.io) $0.02, each with free egress or nearly. A text-heavy library is an estimated 50–300 MB,
a heavy one 1–2 GB, with pictures dominating *(estimate; measure real libraries before fixing
numbers)*. Five kept versions of 1 GB cost under $0.10 a month.

## 6. The sign-in stack

Required: Google, Discord, GitHub, Apple, email-or-username with a password, magic links, TOTP
with backup codes, passkeys, a backup email, session list and revoke, deletion and export.

| Option | Gaps | Price | Notes |
|---|---|---|---|
| **Better Auth** (TypeScript library, own Postgres) | Backup email (a column and a verify flow) | $0 | Everything else is core or a first-party plugin. Sessions are rows in our Postgres; a JWT plugin serves JWKS. Security record: CVE-2025-61928 and six fixes in 1.6.11 (August 2026), mostly in optional plugins |
| **Ory Kratos** (self-hosted, Go) | Headless: every screen is ours to build; passwordless is a code, not a link *(unverified)* | $0 | Mature; recovery address and codes native |
| **Clerk** | None | Free to 50k users, but TOTP, backup codes and passkeys need Pro ($25/mo), then $0.02 per user | About $2,800/mo at 200k users |
| **Supabase Auth** | No username login, no backup email; passkeys beta | $25/mo with 100k MAU | |
| **WorkOS AuthKit** | No Discord | 1M MAU free | |
| **Auth0** | No MFA on the free plan | 25k free, then from $35/mo | |
| **Python libraries** (Authlib, pwdlib, pyotp, py_webauthn) | Every flow is ours to write | $0 | Largest security surface. fastapi-users is in maintenance mode, with no 2FA or passkeys |

**Recommendation: Better Auth, runner-up Ory Kratos.** Pay-as-you-go credits mean many users
with little revenue each, so per-user pricing hurts. Adult roleplay is a grey zone in every
hosted provider's policy, and a suspended auth vendor locks every user out at once. Better Auth
covers the whole list bar one column, and users, hashes and sessions stay plain rows in our own
Postgres. The cost is one small Node service and prompt patching.

Provider rules that bite:

- **Apple:** needs the Apple Developer Program ($99/yr), a Services ID with verified domains,
  and a client secret that is a JWT we sign and that expires within 6 months (generate it per
  request). The name arrives only on the first sign-in. Users may give a private relay address;
  the sending domain must be registered with Apple to reach it.
- **Discord:** ask for `identify email`, require `verified`, expect a null email.
- **GitHub:** ask for `user:email` and take the primary, verified entry from `/user/emails`;
  never the profile email.
- **Google:** key on `sub`. Showing our name and logo needs brand verification (domain in
  Search Console, a homepage and privacy policy on it); until published, 100 test users.

## 7. What a correct account system must do

Sources: OWASP ASVS 5.0, the OWASP cheat sheets, NIST SP 800-63B-4, and the pre-hijacking paper
(Sudhodanan and Paverd, Microsoft, 2022).

### Core (ships with accounts)

- **Passwords:** at least 64 characters allowed, any Unicode, no composition rules, no forced
  rotation, never truncated. Checked against breached passwords (HIBP range API) at sign-up,
  change and reset. Argon2id (19 MiB, t=2, p=1 or stronger), rehashed on sign-in when the
  parameters change. A change needs the current password.
- **Reset:** a random token stored hashed, single use, short-lived; no automatic sign-in; never
  a way round 2FA. The link is built from config, not the Host header.
- **Any factor change or reset** ends every other session and every outstanding reset or magic
  token.
- **No enumeration:** the same message and timing for sign-in, reset and magic link. Sign-up
  always says "check your email"; an existing owner gets a "you already have an account" mail.
- **Identities are keyed on (provider, subject), never on email.**
- **An unverified account gets no session and holds nothing,** and is replaced when someone
  else proves the address. This is the pre-hijacking defence.
- **Auto-link only when both sides are verified.** Otherwise: sign in to the existing account
  first, then link from settings. Discord is never auto-linked.
- **Magic links:** 10–15 minutes, single use, hashed at rest, a new one voids the old. The GET
  shows a page with a confirm button (mail scanners prefetch links and burn them). Bound to the
  requesting browser by a cookie; on another device, a code to type.
- **Sessions:** an opaque random token stored hashed; cookie `__Host-`, `Secure`, `HttpOnly`,
  `SameSite=Lax`. A new token at every sign-in, 2FA step and re-authentication. 30 days at most,
  with an idle timeout. Sign-out is server-side.
- **Email change:** re-authenticate, confirm at the new address, tell the old one with an undo
  link.
- **Notices by email** for a password, email or 2FA change and for a recovery.
- **Abuse:** throttle with backoff per account and per address, never a hard lockout (an
  attacker can trigger it). Cap reset and magic mails per address. An invisible challenge at
  sign-up. Starting credit only after the email is verified.
- **Age:** an 18+ attestation at sign-up, stored with its time. (Pointers only: California
  SB 243, the UK Online Safety Act. The legal side is the owner's.)
- **Handles:** `[a-z0-9_]`, 3–30 characters, unique, with a reserved list; no `@`, so "email or
  username" is never ambiguous.
- **Deletion and export:** re-authenticate; a 14–30 day grace with a cancel link; sessions end
  at once. Export is machine-readable. Payment records are kept as tax law requires, detached
  from content. Say what happens to unspent credit.

### Should (soon after)

- **TOTP:** secret encrypted at rest; enrolment completes only after a valid code; ±1 step; a
  used code is refused.
- **Backup codes:** 10, single use, stored hashed; a new set voids the old; a warning when few
  are left.
- **Social sign-in still asks for the second factor,** or the weakest linked provider is a way
  round it.
- **Sudo mode:** a fresh sign-in (about 10 minutes) for email, password, 2FA, linking, export,
  deletion, payment method.
- **Session list,** revoke one, sign out everywhere; an email for a new device.
- **Passkeys** as a primary sign-in; a user-verified passkey satisfies 2FA alone. Several
  allowed; never the only credential without a way back in.
- **Backup email:** verified. It gets security notices and can receive a recovery code. It
  cannot sign in, cannot receive magic links, and cannot reset 2FA alone.
- **2FA lost entirely:** a backup code, else recovery through the primary and backup email with
  a multi-day delay and notices to every address.

### Nice (later)

Risk-based challenges; rescreening passwords at sign-in; passkey upgrade prompts; a cooldown and
quarantine on handle renames.

### Where the sources disagree

- Email as an authenticator: NIST forbids it for out-of-band authentication; magic links are
  still industry standard. Treat a magic link as password-equivalent, never as a second factor.
- Session lifetime: OWASP's cheat sheet says hours, NIST allows 30 days at this level. For this
  product: 30 days with sudo mode.
- Password minimum: ASVS says 8 (15 recommended), NIST 15 when the password is the only factor.

### What ships broken in a first version

Auto-linking on any matching email; sessions that survive a password reset; a reset that signs
in past 2FA; a magic link consumed on GET; tokens stored in plaintext; `Alice` and `alice` as
two accounts; an email change with no notice to the old address; a hard lockout; unlimited
reset mails; TOTP replay inside the window; credit granted before verification; no way to
recover, so support does it by hand on request.

## Sources

- sqlite.org/howtocorrupt.html · sqlite.org/wal.html · zotero.org/support/kb/data_directory_in_cloud_storage_folder · docs.ankiweb.net/files.html · docs.ankiweb.net/syncing.html · manual.calibre-ebook.com/faq.html
- obsidian.md/sync · zotero.org/storage · joplinapp.org/plans · developers.cloudflare.com/r2/pricing · backblaze.com/cloud-storage/pricing · tigrisdata.com/pricing
- better-auth.com/docs · ory.com/docs/kratos · clerk.com/pricing · supabase.com/pricing · workos.com/pricing · auth0.com/pricing
- OWASP ASVS 5.0 (V6, V7) · OWASP cheat sheets (Authentication, Password Storage, Forgot Password, Session Management, MFA, Credential Stuffing) · NIST SP 800-63B-4 · microsoft.com/en-us/msrc/blog/2022/05/pre-hijacking-attacks
- docs.sillytavern.app/administration/multi-user · book.character.ai/character-guide/user-personas · janitorai.com/news/changelog · cs.cornell.edu/home/kleinber/www13-badges.pdf · github.blog/changelog/2022-10-07-visibility-settings-for-individual-achievements
