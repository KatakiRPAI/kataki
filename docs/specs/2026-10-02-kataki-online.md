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
- [ ] G2 · Magic links, password reset, change notices, throttling, the sign-up challenge.
- [ ] G3 · Google, GitHub, Discord, Apple.
- [ ] G4 · TOTP and backup codes, sudo mode, passkeys.
- [ ] G5 · Settings › Account: emails, methods, sessions, export, deletion.
- [ ] G6 · Handles and the online profile.
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
- **Two-factor only guards password sign-in.** A magic link, a social sign-in or a passkey is
  not challenged. G4 adds the challenge on session creation for accounts with 2FA on (a
  user-verified passkey counts as both factors).
- **No backup email.** One column and a verify flow of our own (G5).
- **Advisories:** 37 published, most in plugins this service does not load (SSO, SCIM, OAuth
  provider, Stripe, OAuth proxy). The version is pinned exactly; Dependabot raises it.

Mail goes through one function, `send(to, subject, text)`. In development it prints the mail
and keeps it in memory for tests. In production it calls the owner's provider over HTTPS
(**[owner]**: which one; a paid API, so the paid-API rule applies).

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

## 7. Rules

- The engine binds loopback; only the gateway is reachable.
- Secrets come from the environment: `BETTER_AUTH_SECRET`, `DATABASE_URL`,
  `KATAKI_GATEWAY_SECRET`, `KATAKI_GATEWAY_KEY`, provider client secrets. Never in the repo.
- Nothing here calls a paid API in tests.
- Production, live payment keys and real accounts are the owner's.
