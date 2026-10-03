# Decisions to review

Calls the agents made so development could keep going. Each one can be changed. Read the top
section first; the rest is a record.

Legend: **[you]** you decided it · **[default]** an agent picked it, you have not said yet.

## Needs you (nothing is blocked; these are when you have time)

1. **Mail sender: Resend** [default]. Emails are printed until a key is set. To turn real email
   on: make a Resend account, verify a sending domain, create an API key, put
   `RESEND_API_KEY=` and `KATAKI_MAIL_FROM="Kataki <hello@your-domain>"` in the gateway's
   environment. Why Resend: one HTTP call, no SMTP, a free tier for a start. Any other provider
   is one small function in `gateway/src/mail.ts`.
2. **Cloud save limits** [default, built]: free up to 5 stories, 10 characters, 10 places and
   10 plots; past that $0.10 per GB a month, taken from the credit balance once a day; 250 MB
   at most per snapshot. With no credit, a library past the limit is not saved (nothing is
   deleted). Change the numbers in `gateway/src/cloud.ts` (`LIMITS`).
3. **Apple sign-in**: needs the Apple Developer Program ($99/year). Not built until you join.
4. **Google and Discord sign-in**: built; each needs its keys in `.env` (same steps as GitHub).
5. **Payments (top-ups)**: built against a test processor (no money moves). Amounts: $5,
   $10, $20, $50. It needs a real processor that accepts an app that can be explicit (several
   mainstream ones do not); once you pick one, it is a webhook and a checkout link.
6. **Going online**: the stack is packaged (`compose.online.yaml`) and runs in Docker. To put it
   on a server it needs a domain or subdomain and a host; your existing server would do for
   staging.

## Accounts (Kataki online)

| Date | Decision | Why |
|---|---|---|
| 2026-10-02 | Better Auth, run inside our own gateway [you] | free per user; no vendor can lock users out |
| 2026-10-02 | Passwords allowed, at least 12 characters, checked against leaked lists [default] | you asked for passwords; 12 is the middle of the security guidance |
| 2026-10-02 | Email must be confirmed before an account holds anything [default] | stops someone claiming an address that is not theirs |
| 2026-10-02 | "Sign in with GitHub/Google/Discord" never creates an account; "Create account with …" does [default] | the 18+ tick has to come from the person |
| 2026-10-02 | An existing account is joined automatically only by Google or GitHub, never Discord [default] | Discord's emails are less trustworthy |
| 2026-10-02 | Sessions last 30 days; sensitive changes need a sign-in from the last 10 minutes [default] | long enough to be easy, short enough to be safe |
| 2026-10-02 | Two-step sign-in asked after a password, a sign-in link and GitHub alike [default] | otherwise the weakest way in walks around it |
| 2026-10-02 | A passkey counts as both steps, only if the device checked it was you [default] | that is what makes it safe to skip the code |
| 2026-10-02 | Deleting an account: 14 days to change your mind, then gone [default] | common practice; undoes mistakes |
| 2026-10-02 | Unused credit is not refunded on deletion [you] | |
| 2026-10-02 | Payment records are kept after deletion, without name or email [default] | tax law; you may want a lawyer's view |
| 2026-10-02 | Usernames: 3–30 lowercase letters, digits, underscore; a reserved list; no "is it taken?" lookup [default] | stops look-alikes and listing who is here |
| 2026-10-02 | Backup email only hears about changes; it cannot sign in or reset [default] | a second address is a second way to be hacked |
| 2026-10-03 | Mail through Resend's HTTP API [default] | see "Needs you" 1 |

## Running the website

| Date | Decision | Why |
|---|---|---|
| 2026-10-03 | One compose file: Postgres, gateway, engine; only the gateway is published [default] | simplest thing that runs anywhere Docker does |
| 2026-10-03 | The engine shares the gateway's network so it still listens on loopback only [default] | the engine is not yet hardened to listen wider |
| 2026-10-03 | Out of credit in a story: the line is kept and Add credit opens the amounts; after paying you land in Settings › Account, not back in the story [default] | the simplest return; going back to the story is a later nicety |
| 2026-10-03 | The daily limit ($5 a day by default, resets 00:00 UTC) gets its own message, not the out-of-credit one [default] | adding credit does not lift it, so saying so would mislead |
| 2026-10-03 | The balance chip turns amber under $1 and red at $0 [default] | a quiet warning while there is still some left: time to notice, not a nag |
| 2026-10-03 | Spending shows 30 days, the last 14 with spend as bars, the top 5 stories, the last 5 credits [default] | enough to see where money goes without a whole page; every charge is in the account download |

## Stories

| Date | Decision | Why |
|---|---|---|
| 2026-10-03 | Three levels, Gentle / Mature / Explicit; Mature by default [default] | most roleplay sits there; Explicit is one choice away |
| 2026-10-03 | No level ever allows sexual content involving anyone under 18 [default] | a line the app holds whatever the setting or the card says |
| 2026-10-03 | Explicit on the desktop asks "I am 18 or older" once; online accounts said it at sign-up [default] | the desktop has no account to ask |
| 2026-10-03 | "Keep out of stories": up to 20 topics, told to the model on every reply [default] | a simple, strong way to steer clear of what someone does not want |

## Desktop

| Date | Decision | Why |
|---|---|---|
| 2026-10-02 | A profile is a name and a folder; switching restarts the app [default] | the engine opens one library at a time |
| 2026-10-02 | Synced folders (OneDrive, Dropbox…) get a warning, not a block [default] | they can corrupt the database, but it is your call |
| 2026-10-02 | A PIN is privacy on this computer, not encryption, and says so [default] | the files are not locked; pretending otherwise would mislead |
| 2026-10-02 | Moving a library copies it and leaves the old folder until you delete it [default] | nothing is lost if the copy goes wrong |

## Cloud save

| Date | Decision | Why |
|---|---|---|
| 2026-10-02 | Whole-library snapshots, not live sync [default] | simple and safe for one person on one or two computers |
| 2026-10-02 | The newest 5 snapshots are kept [default] | room to go back without paying for much storage |
| 2026-10-02 | If the cloud copy changed since this computer last saw it, ask before replacing [default] | never silently overwrite another computer's work |
| 2026-10-02 | Snapshots are kept on the gateway's disk for now [default] | object storage comes with going online |
| 2026-10-03 | Limits counted from what the library holds, charged by the bytes kept [default] | counts are easy to understand; bytes are what costs money |
| 2026-10-03 | Out of credit: saving past the limit stops; nothing is deleted, downloads always work [default] | never lose someone's library over money |

## Profiles and badges

| Date | Decision | Why |
|---|---|---|
| 2026-10-02 | The profile card lives inside the library, on the You page [default] | it travels with the library; no design board yet |
| 2026-10-02 | 16 starter badges; no streaks; badges are private and worth nothing [default] | you said you would define the real list |
