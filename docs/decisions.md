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
7. **Backups of the website** [not built]: people's libraries and the Postgres ledger need a
   backup once there is a host (item 6). Until then the Data page online says nothing about
   backups rather than promise them.
8. **Phone designs** [default, built]: the website works at 375 px with a stopgap layout (a tab
   bar at the bottom, nothing wider than the screen). When the designer draws the phone
   screens, those replace it.
9. **The badge list** [default, built]: 16 starter badges (`engine/src/kataki/achievements.py`).
   The real list, tiers and hidden ones are yours to define.

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
| 2026-10-03 | The mind levels are called Light, Standard and Deep in the app (lite, standard, premium in the engine) [default] | plainer words; "premium" sounds like a paid tier, and it is only more calls |
| 2026-10-03 | The monthly limit is off by default; choices $5 to $100; the month is the calendar month in UTC [default] | pay-as-you-go needs no limit to be safe, and a calendar month is what people expect |
| 2026-10-03 | Online, Data says nothing about backups until the service really backs libraries up [default] | showing a backup row before there are backups would mislead |
| 2026-10-03 | "Get the desktop app" links to the GitHub releases page [default] | the only place the app is published today |
| 2026-10-03 | The ribbon shows whenever the test processor is on, not only on a host called staging [default] | the thing to warn about is fake payments, wherever they run |
| 2026-10-03 | Online, Models shows each job's model and a price per 100 replies, and nothing to change [default] | the service picks the models; a choice of models per job comes when the catalogue has more than one |
| 2026-10-03 | Every job's price is for a reply-sized call (4,000 tokens in, 300 out) [default] | one honest yardstick; side jobs vary, so it says "about" |
| 2026-10-03 | An unsent line is kept in the browser's session storage (this tab, until it closes), not on the server [default] | it survives a reload or a new sign-in, and nothing unsent leaves the device |
| 2026-10-03 | Out of credit in a story: the line is kept and Add credit opens the amounts; after paying you land in Settings › Account, not back in the story [default] | the simplest return; going back to the story is a later nicety |
| 2026-10-03 | The daily limit ($5 a day by default, resets 00:00 UTC) gets its own message, not the out-of-credit one [default] | adding credit does not lift it, so saying so would mislead |
| 2026-10-03 | The balance chip turns amber under $1 and red at $0 [default] | a quiet warning while there is still some left: time to notice, not a nag |
| 2026-10-03 | Spending shows 30 days, the last 14 with spend as bars, the top 5 stories, the last 5 credits [default] | enough to see where money goes without a whole page; every charge is in the account download |
| 2026-10-03 | Phones get a working layout now, before the phone designs exist [default] | the website must work on a phone; the designer's version replaces this when it comes |
| 2026-10-03 | On a phone the rail is a bottom tab bar: Home, Stories, Characters, World, You, Settings; New character, Feedback and Theme move out of it [default] | six fit a 375 px screen; the rest are a tap away in their pages and Settings |
| 2026-10-03 | Out of credit in a story: the line is kept and Add credit opens the amounts; after paying you land in Settings › Account, not back in the story [default] | the simplest return; going back to the story is a later nicety |
| 2026-10-03 | The daily limit ($5 a day by default, resets 00:00 UTC) gets its own message, not the out-of-credit one [default] | adding credit does not lift it, so saying so would mislead |

## Stories

| Date | Decision | Why |
|---|---|---|
| 2026-10-03 | Three levels, Gentle / Mature / Explicit; Mature by default [default] | most roleplay sits there; Explicit is one choice away |
| 2026-10-03 | No level ever allows sexual content involving anyone under 18 [default] | a line the app holds whatever the setting or the card says |
| 2026-10-03 | Explicit on the desktop asks "I am 18 or older" once; online accounts said it at sign-up [default] | the desktop has no account to ask |
| 2026-10-03 | "Keep out of stories": up to 20 topics, told to the model on every reply [default] | a simple, strong way to steer clear of what someone does not want |
| 2026-10-03 | Hidden tags hide characters from lists only: never a persona, and a story that has one still opens [default] | hiding is about what you browse; taking away a story or who you play would lose work |
| 2026-10-03 | A story can set its own level; Explicit there needs the same 18-or-older answer as in Settings [default] | one story gentle and another explicit is how people actually play; the age line stays one rule |

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
