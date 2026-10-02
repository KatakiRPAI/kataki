# Kataki online: the gateway

The service in front of `kataki serve --hosted`: who you are, what you may spend, and nothing
else. It is slice A0 of `docs/specs/2026-10-02-profiles-and-accounts.md` and the "own spec" that
`docs/specs/2026-09-29-minds.md` §4 and infrastructure Phase 6 point to. The engine's side of the
contract is minds §8.4 and does not change.

The owner chose Better Auth on 2026-10-02, so the gateway is a small TypeScript service.

## Progress

- [x] This spec (2026-10-02).
- [x] G1 · The gateway (2026-10-02): `gateway/` signs up and signs in with email and password
      (verified email first, 12 characters, 18 or older), keeps the session, proxies signed
      requests to the engine, answers `/allow` and `/usage` from the ledger, gives the starting
      credit once, and serves the web build. The app shows sign-in when signed out, skips the
      model step of first run, and has Settings › Account (name, email, balance, sign out).
      Checked on one machine with the fake model: sign up, the mailed link, a turn billed 121
      micro-dollars, sign out, a wrong password, sign in back to the same page. Owed: the
      "you already have an account" mail to a known address (G2); `gateway` as a required
      check in the ruleset (**[owner]**: `setup-repo.sh`); first run still says "Step 2 of 2".
- [x] G2 · Getting back in (2026-10-02): a forgotten password (a 15-minute link, a new
      password, every device signed out, a notice by mail); a sign-in link (10 minutes, once,
      only for an account, used by a button on our own page so a mail scanner burns nothing);
      the "you already have an account" mail; slower limits on sign-in, sign-up and the mail
      routes. Checked in a browser on one machine. Not done: the sign-up challenge
      (**[owner]**: Turnstile keys); binding a sign-in link to the browser that asked, with a
      code for another device; a notice when the email changes (G5, with the change itself).
- [ ] G3 · Google, GitHub, Discord, Apple. Built (2026-10-02): a provider is offered when
      both its keys are in the environment (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`; the
      same for `GOOGLE_` and `DISCORD_`), `pnpm -C gateway dev` reads them from the repo's
      `.env`; "Sign in with" never creates an account, "Create account with" does and carries
      18-or-older through the redirect; linking joins an existing account only for Google and
      GitHub. Callback: `{origin}/api/auth/callback/{provider}`. A stand-in provider in the
      tests runs the whole round trip. The owner made an account through real GitHub on
      2026-10-02 (a dev OAuth app, localhost). Signing in with no account opens Create account
      with a note. Not done: Google and Discord against the real services (**[owner]**: their
      keys); Apple; the production OAuth apps on the real domain.
- [x] G4 · TOTP and backup codes, sudo mode, passkeys. Built (2026-10-02): two-step sign-in
      with an authenticator app (issuer `Kataki`), ten backup codes stored encrypted, "don't
      ask on this device for 30 days". It is asked after a password, after a sign-in link and
      after another service (the library's own hook, pointed at those routes too; tests walk
      all three). Settings › Account turns it on (QR and key, a code typed back, the backup
      codes shown once), makes new codes and turns it off, each with the password. Checked in
      a browser on one machine. Passkeys (`@better-auth/passkey`, pinned): add one in
      Settings › Account, sign in with it from the sign-in screen; the device must verify the
      person each time, so a passkey stands for both steps. The app uses the browser's own
      WebAuthn JSON helpers, no library. The owner added a passkey with a real device and turned
      two-step sign-in on from a GitHub-made account on 2026-10-02 (localhost). Not confirmed
      with a real device: signing in with the passkey afterwards. Not done: a fresh
      sign-in before sensitive changes beyond these. An account made through another service
      has no password: it changes two-step sign-in from a sign-in of the last ten minutes
      instead. Adding a passkey needs the same; the app says so and offers to sign out (found
      by the owner's first real try, 2026-10-02).
- [x] G5 · Settings › Account: emails, methods, sessions, export, deletion. Built
      (2026-10-02): change email (approved from the old address, then confirmed from the new
      one), change password (the old one needed, every other place signed out, a notice by
      mail), link and unlink another service, the list of places signed in with sign out one
      and sign out everywhere else. Leaving: a sign-in of the last ten minutes, signed out
      everywhere at once, 14 days to sign in and stay, then the engine forgets the library
      (`POST /_gateway/forget`, refused while usage is unbilled, never proxied for a browser)
      and the account is removed; the ledger's rows stay. `GET /api/account/export` gives what
      the gateway holds (never a password hash). The backup email: a second address,
      confirmed by a mailed link, that gets a copy of every notice (password, email, two-step
      sign-in off, leaving) and can do nothing else. Checked in a browser on one machine. Not
      done: recovering an account through the backup email (it needs a delay and notices to
      every address). Decided by the owner (2026-10-02): unspent credit is not refunded when
      an account is deleted. Was **[owner]**: what happens to unspent credit when an account is
      deleted (the screen says the balance goes with it).
- [ ] G6 · Handles and the online profile. Built (2026-10-02): a username (3 to 30 lowercase
      letters, digits or underscores, one per account whatever the capitals, a reserved list,
      no way to ask whether one is taken), set in Settings › Account, and "email or username"
      on the sign-in screen. Not done: a cooldown on renaming and holding the old name; the
      shared online profile (profiles spec, Later).
- [x] C1 · Cloud save for the desktop (2026-10-02; §8): a computer is linked to an account by a
      code approved on the website; its token opens the cloud routes and nothing else, and can
      be removed from Settings › Account. The desktop's Settings › Data sends the library up
      and brings it down. Snapshots have revisions and the newest five are kept; an upload not
      built on the newest is refused until the person chooses. Bringing one down swaps it in at
      the next start, with what was there backed up first. Checked end to end in the real
      desktop app against a local gateway. Not clicked: the shell opening the system browser
      (the test approved the code in a browser directly). Not done: C2 (the free limit and the
      charge for storage: **[owner]** the numbers); object storage instead of the gateway's
      disk (G8); the desktop's address for Kataki online is `KATAKI_ONLINE` until there is a
      domain; uploads are read into memory.
- [x] C2 · Cloud limits (2026-10-03): free up to 5 stories, 10 characters, 10 places and 10
      plots (the snapshot's own counts); a library past any of them is kept for $0.10 per GB
      a month, charged once a day from the balance (`charge` table, migration 003; balance is
      credit − usage − charges). With no credit left, an upload past the limit is refused
      (402) and says why; inside the limit it is always free; nothing is deleted and downloads
      always work. The numbers are defaults in `docs/decisions.md`.
- [ ] G7 · Top-ups (the owner's payment processor, test mode).
- [ ] G8 · The image, staging and production (infrastructure Phase 6).

G1–G6 are A1–A6 of the profiles spec.

## 1. The shape

```
browser ──► gateway (public)                         engine (loopback)
            ├ /api/auth/*      Better Auth            kataki serve --hosted
            ├ /app/*           the web build            --root <libraries>
            ├ /allow, /usage   ◄── the engine asks ──   --gateway http://gateway
            └ everything else  ── signed request ──►   one library per user
                 │
              Postgres: user, session, account, verification (Better Auth), credit, usage
```

- **One process, `gateway/`:** Node 24, TypeScript run as it is (no build step), `node:http`,
  `better-auth` pinned to an exact version, `pg`. No web framework.
- **The session is a cookie** on the gateway's own origin; the app and its API are the same
  origin, so nothing is cross-site. The engine never sees the cookie.
- **A user's id is their library id:** ids are generated as lowercase UUIDs, which fit §8.4's
  `[a-z0-9_-]{1,64}`. The gateway refuses to proxy any id that does not.
- **The proxy** adds `X-Kataki-User`, `X-Kataki-Channel`, `X-Kataki-Time`, `X-Kataki-Sig` (§8.4),
  drops any the browser sent and the `Cookie` and `Authorization` headers, and streams both
  ways (uploads in, server-sent events out). A request that changes something must come from
  the gateway's own origin (`Origin` checked).
- **No session:** `401 {"code": "SIGNED_OUT"}`; the app shows sign-in and comes back to where
  it was.

## 2. Accounts (Better Auth)

What is set, and why (research report §7):

| Setting | Value | Why |
|---|---|---|
| `emailAndPassword.requireEmailVerification` | on | an unverified account gets no session and holds nothing; sign-up with a known email answers the same as a new one |
| `minPasswordLength` | 12 | profiles spec decision 4 |
| `haveIBeenPwned` | on | breached passwords are refused at sign-up, change and reset |
| `revokeSessionsOnPasswordReset` | on | off by default in the library |
| password hash | the library's scrypt | OWASP lists it; Argon2id would add a native dependency for no gain here |
| `session.expiresIn` | 30 days, `updateAge` 1 day, `freshAge` 10 minutes | long sessions with a fresh sign-in for sensitive changes |
| cookie cache | off | a revoked session stops at once |
| `rateLimit` | on, in the database | several gateway processes share it |
| `advanced.database.generateId` | lowercase UUID | the library id |
| `account.accountLinking` | on, `trustedProviders` Google, GitHub, Apple; never Discord; `allowDifferentEmails` off | linking only when both sides are verified |

Known gaps in the library, to close in the slice named:

- **Magic-link verification is a GET that uses the token up,** so a mail scanner can burn it.
  The mail links to the app's own page, whose button makes the request (G2).
- **Two-factor only guards password sign-in** in the library. Closed in G4 for sign-in links
  and other services (`secondStep` in `gateway/src/auth.ts`). Passkeys, when they come, count
  as both factors when the user is verified.
- **No backup email** in the library. Ours is `account.ts` (G5).
- **Advisories:** 37 published, most in plugins this service does not load (SSO, SCIM, OAuth
  provider, Stripe, OAuth proxy). The version is pinned exactly; Dependabot raises it.

Mail goes through one function, `send(to, subject, text)` (`gateway/src/mail.ts`). With no
`RESEND_API_KEY` it prints the mail (tests keep it in memory). With one, it posts to Resend's
HTTP API from `KATAKI_MAIL_FROM`; a failed send is logged by status only. The provider is a
default in `docs/decisions.md`; the owner makes the account and the key.

## 3. The ledger

Money is integer micro-dollars, computed from a row's tokens and the price table exactly as
`usage.micros` does (minds §8.4), never from `cost`. `gateway/src/money.ts` and the engine are
held to the same answers by one file of vectors, `engine/tests/money_vectors.json`, read by a
test on each side.

- `credit(id, user_id, micros, reason, ref UNIQUE, at)`: append-only. Reasons: `starter`,
  `topup`, `refund`, `adjust`.
- `usage(usage_id PRIMARY KEY, user_id, micros, role, model, prompt_tokens, cached_tokens,
  completion_tokens, estimated, used_at, at)`: append-only, one row per model call.
- Balance = sum of credit − sum of usage. It may go below zero by one call (the gate asks with
  an estimate); the next call is refused.
- `GET /allow?user=&estimate=` → `{"ok": balance ≥ estimate}`. `POST /usage` → 200; 409 when the
  `usage_id` is already there; 422 when a field is missing or the model has no price. Both need
  `Authorization: Bearer {KATAKI_GATEWAY_KEY}`.
- Prices come from the same catalogue file the engine is given (`--catalogue`), read with
  `node:sqlite`, so the two can never disagree.
- Starting credit: `KATAKI_STARTER_CREDIT` dollars (default 0), granted once per account, after
  the email is verified (`ref = starter:<user>`).
- `GET /api/me` → `{user, balance}` for the app.

Top-ups are G7. Until then the only credit is the starting credit, which is what staging needs.

## 4. Data and migrations

- Better Auth's tables are created by its own migration at startup (`getMigrations`).
- The gateway's tables are numbered SQL files in `gateway/migrations/`, applied in order and
  recorded in `schema_version`; forward-only, expand → migrate → contract (AGENTS.md).
- Tests and local development run on PGlite (Postgres compiled to WASM, in process, reached
  over its socket server by the same `pg` client), so nothing needs a database daemon. CI can
  move to a Postgres service container when the deploy slice adds one.

## 5. The app

- The web build asks `GET /api/auth/get-session` once at start. No such route (the desktop, a
  self-hosted Kataki): nothing changes. Signed out: the sign-in screen. Signed in: the app.
- Sign-in calls the auth routes with `fetch`; the desktop bundle takes no new dependency.
- Screens follow `docs/design-brief-3.md` S1–S5 as amended by the profiles spec (passwords and
  social buttons are in). Until boards arrive they are built from existing components.

## 6. Running it on one machine

Four terminals, from the repo root (bash; the dev secrets are `gateway/src/dev.ts`'s):

```
pnpm -C app build:web
cd engine && uv run python evals/dev_catalogue.py ../.dev/catalogue.db
cd engine && uv run python evals/demo.py serve-model --port 8099          # the fake model
cd engine && KATAKI_KEY_FAKE=x KATAKI_GATEWAY_SECRET=dev-only-gateway-signing-secret-32b \
  KATAKI_GATEWAY_KEY=dev-only-gateway-key uv run kataki serve --hosted --root ../.dev/online \
  --catalogue ../.dev/catalogue.db --gateway http://127.0.0.1:8787 --port 8788
KATAKI_CATALOGUE=.dev/catalogue.db pnpm -C gateway dev                    # PGlite + the gateway
```

Then open `http://localhost:8787/`. The confirmation mail is printed by the gateway. `dev`
gives each new account $1 and turns the breached-password check off; `start` reads everything
from the environment and has no defaults.

## 8. Cloud save for the desktop

Profiles spec C1. The desktop keeps its library on its owner's account as whole snapshots, the
library's own `.kataki`, never a live sync (research §5).

- **Linking** (`gateway/src/cloud.ts`, `engine/src/kataki/cloud.py`): the engine asks
  `POST /api/device/start` and gets a code, a secret and an address; the shell opens the address
  (only ever Kataki online's own origin); the signed-in person sees the computer's name and the
  code and approves (`POST /api/device/approve`); the engine's `POST /api/device/poll` is handed
  a token once. The token is kept in the OS keychain, stored hashed on the gateway, and listed
  and removable under Settings › Account.
- **Routes for a linked computer** (`Authorization: Bearer kd_…`): `GET /api/cloud` (the
  account's name, the newest snapshot, the limits), `PUT /api/cloud?base=&force=&holds=` (the
  body is the `.kataki`), `GET /api/cloud/download`, `DELETE /api/cloud/device`.
- **Revisions:** an upload says which snapshot the library was last in step with (`base`, kept
  in `cloud.json` beside the library, not in it). Anything else is `409` with what is there:
  the person brings it down, or uploads again with `force`. The newest five are kept.
- **Down:** the snapshot is checked to be a library, written beside the backups, and swapped in
  at the next start by the backup-restore path, which keeps what was there.
- **Limits:** a byte ceiling per snapshot (`KATAKI_CLOUD_MAX_BYTES`, 250 MB by default), and the
  free limit by counts (the snapshot's `holds`) with the storage charge past it (C2 above).
- **An account that is deleted** takes its snapshots and linked computers with it.

## 7. Rules

- The engine binds loopback; only the gateway is reachable.
- Secrets come from the environment: `BETTER_AUTH_SECRET`, `DATABASE_URL`,
  `KATAKI_GATEWAY_SECRET`, `KATAKI_GATEWAY_KEY`, provider client secrets. Never in the repo.
- Nothing here calls a paid API in tests.
- Production, live payment keys and real accounts are the owner's.
