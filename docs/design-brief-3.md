# Kataki: design brief 3 (what changed, the landing page, the online app)

Three parts. Part 1 tells you what has changed since the third handoff. Parts 2 and 3 are the
two things to design: the landing page at `[DOMAIN]` and the online app at `app.[DOMAIN]`.

Your last handoff (*Kataki · App screens*, 118 boards) is built and stays the source of truth
for everything it covers. Don't redesign it. This brief adds to it, in the same design system,
the same Night/Day tweak, the same copy rules and the same handoff format.

Words in `[BRACKETS]` are the owner's to fill; leave them as visible placeholders.

---

## Part 1 · What changed

### Two products now, not one

| | **Kataki (desktop)** | **Kataki online** |
|---|---|---|
| Where | Windows app, free, open source (GitHub releases) | A website: `app.[DOMAIN]` |
| Models | Yours: a model server on your computer, or your own API key | Ours: included, nothing to set up |
| Who pays | Nobody pays Kataki. Your own API key may cost you | Pay as you go: top up a balance; each reply costs what the model costs plus a small margin |
| Account | None. Everything stays on your computer | Sign in by passkey or email link. No passwords |
| Data | A library file on your disk | Your own library, hosted |

**One engine, the same features.** A feature ships to both or to neither. They differ only in
where models run and who pays. So the online app is the desktop UI you already designed,
plus sign-in, a balance, and a few screens swapped (Part 3).

Both have **alpha, beta and stable**. Desktop gets them as release channels; online, beta is a
flag on the account. A feature can be on for beta users only, so a small "Beta" badge on a
feature is a real state.

### Characters have minds now, not just memory

We did a deep research pass on what makes a character read as human. The answer: not a
smarter model, but **state that carries across turns, and imperfections with a cause**. Every
competitor sells a memory list. Nobody shows an inner life. That's Kataki's ground now.

The principle: **code owns the mind; the model only voices it.** Moods, grudges, whether to
give in, whether to lie, what to forget: all decided by the app, stored, and visible. Because
it's stored, the user can always see *why* a character acted that way, and change it.

What characters do, roughly in the order it ships. Slices 1 and 2 are built (alpha).

| # | What you'll see | Built? |
|---|---|---|
| 1 | **"She's still upset."** Insult Mike: he's hurt now and low for hours after. He may *show* calm while he *feels* hurt, with a tell ("short answers") that leaks. | ✅ alpha |
| 2 | **"He holds a grudge, and won't cave."** Trust falls fast and comes back slowly. A hollow "sorry" doesn't fix it; a sincere one starts to. He pushes back instead of agreeing with everything you say. | ✅ alpha |
| 3 | **"She thinks before she speaks."** A private two-line thought before each reply ("*He's lying. Let him finish.*"), and what she wants right now. | next |
| 4 | **"He lies to protect a secret."** Cover stories kept straight, white lies, suspicion, getting caught, confessing. | planned |
| 5 | **"Meanwhile…"** Life between scenes. Come back after a week and they've had one: a "while you were away" card. | planned |
| 6 | **"She misremembers, and corrects herself."** "Thursday… no, Wednesday." Only hazy memories drift; pinned ones never do. | planned |
| 7 | **"He wants something."** Goals that he steers toward, and drops if you deflect. | planned |
| 8 | **"She changes, slowly."** Growth over many scenes, with evidence the user can accept, reject or lock. | planned |
| 9 | **"He texts like a person."** Bursts of messages, typing, a typo corrected in the next bubble. Every delay skippable. | planned |
| 10 | **"She sounds like herself."** Voice. | planned |

**Rules no setting can break** (design them in, don't design around them):

1. A character stays in the scene and keeps playing. Moods and grudges change *how* they answer, never *whether* the story goes on.
2. A stop word (default `red`) ends any stance at once.
3. A sincere out-of-character question ("are you an AI?") gets a truthful out-of-character answer.
4. Pinned memories are never distorted or forgotten. "The app lost it" is never passed off as forgetting.
5. Every delay can be skipped with one tap.
6. **Everything the mind decided is inspectable in Peek and Backstage, and the user can edit or reject it** (a grudge, a growth ring, a misremembering).

### New things to design in the existing app

These go into the areas you already have (continue the board codes there: P, Q, E, F, K).
They apply to desktop and online alike.

- **Mood, in Peek and on the stage.** The data:
  `feels` "very hurt, and a little anxious" (private: Peek only) · `shows` "calm" · `tell` "short answers" · `word` "low" · `why` "Cas called him useless".
  Design the gap between *feels* and *shows*: it's the most human thing on screen.
- **Bonds, in Peek and on the profile's Story tab.** Per person: soft bars for trust, closeness and respect (roughly −100 to 100, drifting back over time), a words line ("trusts much less · further · holds a grudge"), and a grudge card: what happened, the cause (“Cas said "I forgot"”), since when, and whether it's forgiven. Rule 6: the user can edit or dismiss a grudge here.
- **The thought.** Slice 3's two lines in Peek, and on a line in Backstage. Private by default.
- **Backstage mind graph.** New nodes: Mood, Feeling (toward a person), later Thought, Intent, Honest?. Same graph you designed (Q1), more node kinds.
- **Realism settings** (a new Settings group, K19+), each overridable per character on its profile:
  Pushback (soft · realistic · stubborn), Memory style (faithful · human · dreamlike), Relationships (gentle · realistic · harsh), Texting (off · light · natural · messy), Off-screen life (off · on), and Mind level (lite · standard · premium: how much thinking each reply gets, and so how much it costs online). Defaults are "Natural": the middle of each.
- **A character's mind, on make/edit** (F-series). Six sliders with a middle and a spread (dominance, warmth, candor, honesty, yielding, volatility); attachment style; how they handle feelings; values; hard lines; want, need, fear; and stance presets (bratty, submissive, dominant, blunt…) as the quick way in. Most users will only ever touch the presets.
- **"While you were away"** card on returning to a story (slice 5).
- **Cost, on both.** Online: what a story has cost, and an estimate before an expensive job. Desktop users with a paid API key get the same: "This story cost $0.12".

### Sample content

Use the sample world the app ships with (`app/src/sample`): **Liv Sandoval** ("Cheerleader. The queen's step-sister's daughter."), **Cas Brennan** (the user's persona, "Twelfth in line, and hates it."), **Mike Dorsey** ("Barista at Halcyon. Son of the queen's hairdresser."), **Theo Park**, **Nico Ferrer** ("Art student, your flatmate. Tells you the truth you asked for."), **Jae Moretti**, **Dani**. Places: Halcyon Coffee, Corvel Palace, the flat on Ardenne. Mike is the one who gets hurt; Nico is the blunt one; Jae is the one with a secret.

---

## Part 2 · The landing page (`[DOMAIN]`)

### Its one job

**Get an email address.** Kataki online isn't open yet; this page builds the waitlist. Nothing
else on it competes with the email field: no pricing table, no sign-in, no feature grid that
needs reading.

### Who it's for

People who already roleplay with AI (Character.AI, SillyTavern, companion apps) and have felt
the character forget them, agree with everything, or reset to a polite assistant. They should
recognise that in two seconds and see that this is different.

### What it says, top to bottom

1. **Hero.** One line, one sub-line, the email field and button, above the fold on a phone.
   Direction, not final copy:
   - "Characters with a mind of their own."
   - "They remember, they feel, they hold a grudge, and they don't just agree with you."
   - Field: "Your email" · Button: "Join the waitlist"
2. **Show it, don't list it.** One short scene that plays itself: Cas says something careless
   to Mike. Mike answers calmly, *but* a Peek-style card beside him shows `feels: hurt · shows:
   calm · tell: short answers`. A beat later, Cas apologises half-heartedly and the trust bar
   barely moves. This is the whole pitch in one moment: an inner life you can see. Reuse the
   Scene and Peek components; it should look like the real app, because it is.
3. **Three things no one else does**, one line each, each with a small live-looking fragment
   from the app: *They remember what they saw, and forget like people do* (memory receipts
   fading) · *They feel, and it lingers* (the mood card) · *You can see why* (a Backstage node).
4. **Two ways to play.** Two cards, side by side:
   - **Kataki** · Free and open source, on your computer, with your own models. → "Get it on GitHub" (this one is live now).
   - **Kataki online** · Nothing to install. Pay only for what you use. → "Join the waitlist" (scrolls to / focuses the field).
5. **Email again** at the bottom, for people who read to the end.
6. **Footer.** GitHub, privacy, terms (`[PRIVACY URL]`, `[TERMS URL]`), `[CONTACT]`.

### The email field, every state

Idle · typing · invalid ("That doesn't look like an email") · sending · **done** ("You're on
the list. Check your inbox to confirm.") · already on the list ("You're already on it. We'll
write when it opens.") · failed ("Couldn't add you just now. Try again?", keeps what was typed).
Double opt-in: design the confirmation email too, and the page it links to ("Confirmed. See
you soon.").

One line under the field, always visible: "One email when it opens. No spam, unsubscribe any
time." `[OWNER: add an age line here if needed]`.

### Constraints

- **Phone first.** Most visitors arrive from a link on a phone. Design 390×844 first, then 1440.
- **Fast.** No heavy video; the scene in section 2 is real text and CSS motion, still under reduced motion.
- **General-audience.** Illustrated characters, never photos of real people.
- **No claims we can't back.** No "the most human AI", no user counts, no prices yet.
- Night by default (it's where the Scene lives); Day works too.
- The social share image (1200×630) and favicon belong to this deliverable.

### Boards

`V1` landing, phone · `V2` landing, desktop · `V3` field states (all seven) · `V4` confirmation
email · `V5` confirmed page · `V6` share image. Night and Day on each.

---

## Part 3 · The online app (`app.[DOMAIN]`)

### What it is

The desktop app in a browser. **Every existing board carries over unchanged** unless listed
below. The web build already runs today (the same React app with a browser router), so this
is about what's *different* online, not a new app.

### New: signing in (`S`)

- `S1` Sign in: email field → "Send me a link", and "Use a passkey". No passwords, ever.
- `S2` "Check your email" (with resend after 30 s, and "wrong email?").
- `S3` Link expired or already used.
- `S4` First sign-in: create a passkey (skippable).
- `S5` Signed out / session expired (keeps the user's place and returns them to it).

### New: balance and billing (`T`)

Show money, not tokens or points: "$4.20". It's the honest unit for pay-as-you-go.

- `T1` **Balance, always in reach**: a quiet chip in the top bar or rail. Low (`[LOW THRESHOLD]`) turns it amber; zero turns it red. Never a nag.
- `T2` **Top up**: pick an amount (`[AMOUNTS]`) → the payment provider's hosted checkout (we don't draw that page) → back to `T3`.
- `T3` Back from checkout: paid · cancelled · still processing.
- `T4` **Out of credit in the Scene.** The reply is refused *before* anything is sent. The composer keeps the user's line. Inline: "You're out of credit" with Top up. The story is never lost or locked; reading, editing and Backstage still work.
- `T5` **Usage**: spend by day and by story, and what each reply cost (open a story → its cost). A plain ledger underneath: top-ups and spending, downloadable.
- `T6` **Before an expensive job** (a big time skip that runs everyone's "meanwhile", or premium mind level): "About $0.08. Go ahead?" with "don't ask under $[X]".
- `T7` **Spending cap**: a monthly limit the user sets; what happens when it's hit (like T4, with "raise the cap").
- `T8` Starting credit on a new account, if there is one: `[STARTER CREDIT]`.

### Changed: Settings online (`K`)

- **Models** (K4–K8) becomes a **catalogue**: our models per job, each with a plain quality line and a price per reply, instead of servers, keys and local detection. The default is picked; most users never open it.
- **Mind level** shows its cost: lite · standard · premium, each with "about $X per 100 replies".
- **Gone online**: servers on this computer, API keys, Start with Windows, closing the window, updates, backups on disk. **Replaced**: backups are ours (show "last backed up"), and "Export my library" downloads a `.kataki` file.
- **New: Account** (`U1`): email, passkeys (add, remove), sign out everywhere, the beta toggle if we offer it, delete my account (type-to-confirm, with "export first").
- **"Get the desktop app"**: a small, friendly link in Settings › About: same characters, your own models, free.

### Changed: first run (`B`)

Online skips "connect a model" entirely (B1–B4). It's: sign in → who you are (B6) → who first
(B5) → a scene. Show the starting balance once, calmly, at the end.

### New errors

Add to the catalogue in `errors.json` format (title, body, actions, surface): `NO_CREDIT`,
`SPEND_CAP_REACHED`, `TOPUP_FAILED`, `TOPUP_PENDING`, `SESSION_EXPIRED`, `SIGNIN_LINK_EXPIRED`,
`SERVICE_BUSY` (our models are overloaded; retry by itself), `ACCOUNT_DELETED`.

### Constraints

- **Phones are real now.** The desktop handoff proved 1024 wide; online must work at 390×844.
  Design phone versions of: Home, the Scene (one-to-one), Peek, sign-in (S1–S2), balance and
  top-up (T1–T4).
- **Staging** runs with test payments. A thin ribbon, "Staging · test payments", on every page
  there, so no one mistakes it for real.
- Everything else (copy rules, strings file, keyboard, accessibility, reduced motion, right to
  left) as in the handoff's README.

---

## Deliverable

The same shape as the third handoff: a Claude Design canvas with every board above (Night and
Day), and a handoff folder that adds to the existing one: new rows in `ROUTES.md`, `SCREENS.md`,
`OVERLAYS-AND-MENUS.md`, `DATA.md`, `manifest.json`, `errors.json` and `strings.boards.en.json`,
and a short `CHANGES.md` listing every board that is new or changed.

**Order of work:** the landing page first (V1–V6: it's what goes live first), then the online
app's S and T boards and phone Scene, then the mind additions (mood, bonds, thought, realism
settings, a character's mind), then the rest.

Questions worth exploring:

- How does *feels* vs *shows* read at a glance without turning the Scene into a dashboard?
- How does a balance stay visible without making every reply feel like it costs money?
- How much of the inner life does the landing page show before it becomes a feature list?
