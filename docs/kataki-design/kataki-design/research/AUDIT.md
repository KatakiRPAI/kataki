# Element audit · the Sky

Every screen, every region, every recurring element in the nine Sky screens, taken one at a time. For each: **what it is now**, **why it was chosen**, **what else it could be**, and a **verdict** — `keep`, `change`, `replace`, `cut`, or `add`.

Written 26 September 2026 against canvas version 12 (`Sky-Home`, `Sky-Profile-Mike`, `Sky-AddCharacter`, `Sky-Chats`, `Sky-Library`, `Sky-You`, `Sky-Activity`, `Sky-FirstRun`, `Sky-Models`, plus four dark variants). Reads on top of `UX-STUDY.md` (friction IDs `F1`–`F22`) and `DESIGN-RESEARCH.md` (slop tells `S1`–`S12`).

Verdict counts: **31 keep · 38 change · 11 replace · 7 cut · 19 add.**

---

## 0. Cross-cutting decisions

These apply to every screen and are the highest-leverage items in the document. Nothing below them matters as much.

### 0.1 The sky gradient and the clouds

**Now.** Every Sky screen sits on `linear-gradient(165deg, …)` from pale blue to lavender, with three PNG cloud layers at 30–55% opacity drifting across the top. Dark mode swaps in a night gradient, 150 SVG stars, and a moonlight radial.

**Why.** The metaphor: the Sky is above the clouds, the Scene is down in the world. It makes the dive meaningful.

**Alternatives.** (a) A flat warm paper ground, clouds only at the dive. (b) A photographic sky. (c) Per-time-of-day gradient that tracks the user's real clock. (d) Per-book tinting, so *Close to the Crown* has its own weather.

**Verdict — change.** The metaphor earns its keep but the execution is the app's biggest slop exposure: a full-bleed blue-lavender gradient under everything is one grader away from `S1`. Three fixes: pull the hue off the violet axis toward a warm, slightly desaturated daylight blue; drop the gradient's contrast so it reads as *paper with air in it* rather than a hero background; and make the clouds a **thin band at the top of the viewport**, not a full-surface wash — so the metaphor lands in the first 160px and the content below sits on a calm ground. Keep (c) as a quiet touch: three states (morning / day / evening) tied to the user's clock, no more. Reject (d) — per-book tinting fights the character art.

### 0.2 Frosted glass everywhere

**Now.** Nearly every container is `background: rgba(255,255,255,.07); border: 1px solid rgba(…,.18); backdrop-filter: blur(16px)`.

**Why.** It let the sky show through, so everything felt like it was floating up there.

**Alternatives.** (a) Solid cards on the gradient. (b) Glass only for floating/overlay layers. (c) A surface ladder — stepped near-flat tones for elevation, the Linear/Raycast method.

**Verdict — replace, and this is the single most important change in the audit.** Apple's own Liquid Glass retreat in 2025 is the warning label, and `S2` names decorative glass as a top AI tell. Glass becomes a **material with one job: things that float over something**. That means the persona menu, the Link dialog, the command palette, the Scene's composer over painted art. Everything that is *the page* — character cards, list rows, profile sections, settings panels — moves to an opaque surface ladder: base, raised, overlay, each one step, no blur, no glow. The immediate wins: text contrast becomes calculable instead of dependent on what's behind it, dark mode stops needing a `polish()` pass, and the app stops looking like every AI product launched this year.

### 0.3 Shadows

**Now.** `0 14px 34px rgba(62,92,170,.14)` on almost everything, a coloured soft glow.

**Why.** Floating, above the clouds.

**Verdict — change.** `S3` names glow-under-every-card. Two shadows only: a 1px hairline border for surfaces (elevation via the ladder), and one real drop shadow reserved for genuinely floating layers (menus, dialogs, drag). Drop the blue tint — neutral, low alpha.

### 0.4 Border radius

**Now.** Roughly six radii in play — 10, 14, 16, 18, 22, and full pills — applied by eye rather than by rule.

**Verdict — change.** A four-step scale, each mapped to a component class: `4` inputs and chips, `10` cards and rows, `16` panels and dialogs, `full` reserved for **two** roles only — the primary action and status pills. Uniform radius is `S6`; so is radius chosen per-instance. Pills-on-everything is on the worn-out list.

### 0.5 Colour

**Now.** One accent (`#2f63f0` light / `#82a8ff` dark), semantic ok/warn/danger, and the "candy" filter chips, which carry hue per category.

**Verdict — keep the discipline, change the values.** The Raycast rule applies exactly: **saturated colour lives in the art, never in the frame.** So: one accent, used for the primary action and focus only. The candy filters lose their per-category hue and become neutral chips with a selected state — because hue-coded categories are `F21` (colour as the only channel) and visual noise next to portraits. Semantic colours stay but get a non-colour partner: icon shape for ok/warn, and never a bare coloured dot.

The accent hue itself should move off `#2f63f0`. It sits squarely in the indigo band that `S1` flags. A warmer, slightly greener blue, or a considered non-blue drawn from the painted references, is worth testing in the style directions — this is one of the things the four directions exist to answer.

### 0.6 Type

**Now.** Chewy for display, Figtree for UI, Newsreader for story prose, JetBrains Mono for numbers.

**Verdict — change one, keep three.** The three-voice system is right and is how the app avoids `S5`. But **Chewy is wrong**: it is a novelty comic face, it reads as "cute app for kids", it has no weights, and it does not render in Arabic or most non-Latin scripts at all — which breaks the i18n requirement on the very first screen. Replace with a display face that has real weight range, tight tracking capability, and broad script coverage. Newsreader for prose is excellent and stays — it is the thing that makes the Scene feel like a book. Figtree is fine but unremarkable; the style directions should each propose their own UI face, because that choice more than any other sets the app's temperature.

Add a **type scale with actual contrast**: the current screens run 12/13/14/16/18/22/28 with everything at 400–700. Editorial contrast — a 34px display against 13px meta — is what separates a designed page from a generated one.

### 0.7 Grid and rhythm

**Now.** 1440 wide, a 72px rail, ~24px gutters, cards on a 3- or 4-up grid of equal size.

**Verdict — change.** Equal-weight repeating cards are `S4`. The content is not equal: one story is live, one character was played two hours ago, one is half-finished. The grid should be **asymmetric by importance** — the continue block full width, the played-recently character larger than the rest — and the spacing should have rhythm (bigger gaps between sections than within them) rather than an even 24 everywhere.

Also: **1440 is not a spec, it is a screenshot.** Every layout needs stated behaviour at 1280 (rail collapses to icons), 1440 (as drawn), and 1920 (content max-width caps; the sky does not stretch the cards). Add a stated minimum of 1024 for a small laptop.

### 0.8 Icons

**Now.** 66 custom icons, 24×24, 1.8 stroke.

**Verdict — keep, extend.** A coherent custom set is a genuine craft signal and the opposite of emoji-as-icons. Three additions needed: no icon may be the only label on a destination (pair with text in the rail); add the missing states (error, offline, empty); and confirm every icon mirrors correctly under RTL or is marked as non-mirroring (arrows mirror, clocks do not).

### 0.9 Imagery

**Now.** Painted portraits with per-character `object-position` focal points, painted places with a dawn/day/dusk/night strip.

**Verdict — keep, and lean harder.** This is the app's best asset and the thing no competitor has. Two changes: treat character cards as **key art**, composed, not head-in-a-circle repeated twenty times — the streaming-poster problem, and the "floating heads" cliché is a real one. And every portrait needs a mood-bearing alt text (`F21`), because the art is carrying content.

### 0.10 Motion

**Now.** Bouncy easing, the dive, hover lifts on cards.

**Verdict — change.** Hover-bounce on everything is `S11`. Rule: **motion communicates a state change or it doesn't ship.** Keep the dive (a real transition between two worlds), the memory-bar fill, the streaming caret, the crossfade on a place change. Cut decorative card lift — replace with a border/surface change. Every one of these needs a `prefers-reduced-motion` form.

### 0.11 The four missing systems

`add`, all four, before anything else is drawn:

- **Empty states** for every list: no characters, no stories, no places, no search results, no activity. Each with its own small painted vignette and one action. `F18`, `S10`.
- **Error states**, starting with the one that will actually happen: *the model server went away mid-story*. Then: model too slow, out of memory, disk full, corrupt story file. A local-first app fails locally; the design must own that.
- **Loading states**: the app's cold start, a character's portrait streaming in, a long story opening. Skeletons that match the real layout, not spinners.
- **Feedback / bug / suggestion**, per `UX-STUDY.md` §6.

---

## 1. `Sky-Home`

**Now (1440×1190, scrolls).** Greeting + avatar with switch badge · search · activity bell (4) · "Add a character" · Continue card · Activity preview · Characters section with candy filters and 5 cards + Add card · Moments (2 stills).

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| "Good evening, Liv" | Time-of-day greeting using the persona's name | Story-state line ("Mike is still waiting at the palace"); or no greeting | **change.** The greeting is warm but says nothing. Keep the persona name — it reinforces who you're playing — but demote it to a small line above the continue block rather than a 28px page header. The page header should be the story. |
| Avatar + switch badge | Persona switcher lives on the avatar | Rail footer; command palette; a header dropdown | **keep**, and also expose it in the palette and the rail footer (`F15`). The badge is discoverable only by hovering; add a visible caret. |
| Search field | Full-width input, top of page | Palette-only; a `/` shortcut; a real results page | **change.** Keep the field, but it must lead somewhere — a real search-results surface across characters, stories, places, plots and lines (`F19`). Bind `/` and fold it into `Ctrl+K`. |
| Activity bell (4) | Badge count of memory events | Remove; fold into the continue block | **replace.** A notification bell in a single-player local app is borrowed furniture — there is no one else acting. What it actually means is "your story changed", which belongs in the continue block as prose (`F8`). |
| "Add a character" pill | Top-right primary action | Secondary; inside the characters section | **change.** It is not the primary action of the home screen for anyone except a day-one user. Demote to the characters section header; the primary action on Home is *continue*. |
| **Continue card** | One card in a stack, ~340 tall | The page's hero | **change — the most important layout change in the Sky.** Full-width block at the top: the last still large, the last line in Newsreader at reading size, who is present, what changed while you were away in feelings language, and one large "Dive back in". Priya's five-second contract (`F4`). |
| "3 new memory events" | Event count | "Mike has been thinking about the gala." | **replace.** Feelings, not telemetry. The brief said this twice. |
| Activity preview card | Small list of recent memory events | Cut; merged into continue | **cut** (`F8`). |
| Candy filter chips | All / Favourites / In a story / New / Groups, hue-coded | Neutral chips; a sort instead; a segmented control | **change.** Neutral surface, selected state by fill + weight, not hue (`0.5`). Five filters for five characters is more chrome than content — show filters only past ~8 characters. |
| Character cards | Equal 4-up grid, circular portrait, name, "Played 2 hours ago" | Asymmetric key-art cards; a list; a shelf | **change.** Asymmetric: the character you played last is a large card with the portrait composed as key art; the rest are smaller. Kill the repeating-unit look (`S4`). Keep "Played 2 hours ago" — the real-clock default is right. |
| Dani's 60% ring | Completeness ring on an unfinished character | A quiet "draft" tag; nothing | **replace.** A progress ring nags (`F10`). A small "Draft" chip and, on the card, one specific missing thing ("no secret yet") is more useful and less judgemental. |
| Add card in the grid | Dashed tile at the end | Keep | **keep.** Correct pattern, low cost. |
| Moments strip | 2 composed stills | Explain it; cut it | **change.** Beautiful, unexplained (`F22`). Needs a one-line header that says what a Moment is and how one is made, or it reads as decoration. |
| Page scroll to 1190 | Home scrolls | Fit to viewport | **change.** With the continue block as hero, Home should fit 900 and *invite* the scroll rather than require it. |
| Empty home | Not designed | — | **add.** The day-one home, with a shipped cast, is the single most important screen in the product (`F3`). |

---

## 2. `Sky-Profile-Mike`

**Now (1440×1500).** Portrait + name plate + "Played 2 hours ago" + tags · last-played tile · four actions · 3 stat tiles · "Right now" living card with story selector and memory bar · About · How he talks · How he says hi · The Secret · Relationships · Stories together · Places · Moments.

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| Big portrait + name plate | Hero image with overlaid plate | Split hero (art left, facts right); full-bleed with scrim | **keep the ambition, change the crop.** This is the best screen in the Sky. Give the plate a real scrim (not a translucent card) so the name is legible over any art, and set a max hero height so a tall portrait doesn't push the actions below the fold. |
| Four action buttons | Message / Start a new story / Group scene / Edit profile, equal weight | One primary + a menu | **change.** "Message Mike" is the action; the other three are not peers. One primary, one secondary ("New story"), and the rest in a `⋯`. Four equal buttons is the undifferentiated-pill problem. |
| Three stat tiles | Stories · Memories · Days known | Cut; fold into prose | **cut** (`S12`). A three-stat-tile row is the dashboard reflex and it tells the user nothing they act on. "Memories: 41" is exactly the memory-spam the brief asked to reduce. Replace with one sentence: "Four stories together since May." |
| "Right now" living card | Current state + story selector + memory bar | Keep | **keep** — this is the product. It is the only place a competitor has nothing comparable. Give it more room and move it directly under the actions. |
| Memory bar | A bar showing memory sharpness | Keep, relabel | **change.** Keep the mechanic, lose the word "memory" as the label — "What he still holds onto" does the same job in feelings language. Add a non-colour channel (`F21`). |
| About / Also known as | Prose block | Keep | **keep.** |
| How he talks / says hi | Sample lines as chat bubbles | Keep | **keep.** Genuinely charming and instantly readable. |
| The Secret | Dark card, high contrast | Keep | **keep.** The one place a dark card is justified inside a light page — it is a *different kind* of information. Verify contrast in both themes. |
| Relationships / Stories / Places / Moments | Four stacked sections, same weight | Tabs; an accordion; reorder by use | **change.** Eleven undifferentiated sections is `F11`. Group into two tabs under the living card: **Story** (relationships, stories together, places, moments) and **Profile** (about, voice, secret). Keeps the page under one screen of scroll. |
| Four time displays | "Played 2h ago" + tile + story rows + hover | One | **change** (`F12`). One real-clock statement in the header, story-relative dates inside story rows, hover for the exact. Drop the standalone tile. |
| Edit affordance | "Edit profile" button | Inline edit on hover | **add** inline editing for single fields; keep the full editor for structural changes. |

---

## 3. `Sky-AddCharacter`

**Now.** A 6-step wizard (step 3: "Their secret") with a stepper, a big textarea, "Stuck? Start from" chips, Back/Skip/Next, and a live preview card with a 60% ring.

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| Six-step wizard | Guided, one question per screen | One page, progressive; a conversational builder; import a card | **replace** (`F9`). Six screens to make a character is six chances to quit; Character.AI does it on one page with two required fields. New shape: **one page, two required fields (name, greeting), everything else optional and collapsed**, with the live preview beside it. Keep the guided path as an explicit "Walk me through it" option for people who want it. |
| "Stuck? Start from" chips | Prompt starters | Keep | **keep.** Excellent — the cheapest quality lever in the flow. Extend to every field. |
| Live preview card | Fills in as you type | Keep | **keep.** Best part of the screen. |
| 60% ring | Completeness | Draft chip | **replace**, as on Home. |
| Skip | Per-step skip | Implicit (fields optional) | **cut** — unnecessary once fields are optional. |
| Import | Not present | — | **add.** Import a character card (the PNG-embedded format SillyTavern and Chub use) and import from a folder. Ko will expect it; it is also how a user brings their existing library. |
| Portrait | Not in the flow | — | **add.** A character with no face is the weakest thing in the Sky. Offer: choose from a bundled set, upload, or leave blank with a good placeholder. |

---

## 4. `Sky-Chats`

**Now.** Thread list (New chat, New group, filter chips, pinned thread with stacked avatars, 3 others) + a preview pane (last-moment still, Dive in orb, In this story, New since you left).

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| Existence of the destination | Chats separate from Characters | Merge into one "Stories" surface; make Characters a view of it | **change** (`F6`). For most users a chat *is* a character. Proposal for the style directions to test: one destination — **Stories** — with two views (by story, by character) and one shared search. The rail drops from six to five. |
| Thread rows | Avatar stack, title, "2h ago", "as Liv · three weeks later", memory badge | Keep | **keep**, drop the memory badge (`3`) — memory spam again. Replace with a feelings line if anything. |
| Two-line time | Real time + story time | Keep | **keep.** This is the two-clock model working correctly. |
| Preview pane | Repeats the selected row, adds a still | Full preview with the last few lines; cut the pane | **change** (`F13`). If the pane exists it must add something: the last three lines in Newsreader, who is present, what changed. Otherwise the row is enough and the space belongs to the list. |
| "Dive in" orb | Circular primary action | Keep | **keep.** The orb is a genuine signature element — one of the few things in the Sky that could not have been generated. |
| Filter chips | Same candy chips | Neutral | **change**, as on Home. |
| Group scene | "New group scene" as a peer of "New chat" | Keep | **keep.** |
| Empty / archived | Not designed | — | **add** an empty state and an archive; a two-year user will have 200 stories. |

---

## 5. `Sky-Library` (Places & Plots)

**Now.** Filter panel (Everything, a BOOKS tree, "Not in a book", character chips) · tabs All/Places/Plots · sort · cards grouped by book (places with a dawn/day/dusk/night strip, plots as quote cards) · a Link dialog.

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| Places and plots together | One destination, one tab set | Two destinations; one "World" destination with sections | **keep the merge, change the framing.** They belong together — both are story scaffolding — but "Places & Plots" is a list of two nouns, not a concept. Name the destination **World**, with Places and Plots as its sections. Shorter rail label, clearer idea, and it has room to grow (items, factions, lore). |
| Four filtering mechanisms | Tree + chips + tabs + sort | One filter bar; a tree only | **change** (`F14`). The book tree is the primary organiser and should stay in the sidebar. Character chips and the type tabs collapse into a single filter row above the grid. Sort stays. Three mechanisms, clearly ranked. |
| Book tree | Books → stories, indented | Keep | **keep.** This is the structure Noor needs and no competitor has it. |
| Place cards + time strip | Painted place with dawn/day/dusk/night | Keep | **keep.** The time strip is one of the best small ideas in the design. |
| Plot cards | Quote-led card | Keep | **keep** — the pull-quote treatment is right and gives the grid two card types, which breaks up `S4`. |
| Link dialog | Modal: Book, Stories, Characters who know it | Inline; a side panel | **keep** the modal; it is a focused, bounded task. Glass is justified here (it floats). |
| Faces on cards | Avatars of who knows the place | Keep | **keep**, with alt text. |
| Empty world | Not designed | — | **add.** A new user's World is empty, and this is the screen that most needs to teach what it's for. |

---

## 6. `Sky-You`

**Now.** Persona switcher menu (Liv ✓, Cas, Director, New persona) · Your profile with a "Played by you" badge · Who knows Liv (per character, per story) · Liv's chats.

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| Persona switcher as a menu inside a destination | Menu on this page | Global: avatar, rail footer, command palette | **change** (`F15`). Switching who you are is global. The menu lives on the avatar everywhere; this destination *manages* personas rather than switching them. |
| "Director · play no one" | A persona that is not a person | Keep | **keep.** Genuinely good idea, clearly labelled. |
| "Who knows Liv" | Per character, per story | Keep | **keep.** The clearest expression of the memory engine anywhere in the Sky, and it is on the least-visited screen. Surface a compact version on the character profile too. |
| "Played by you" badge | Distinguishes persona from character | Keep | **keep.** |
| Settings entry | Reached from here | A separate rail footer item | **change.** Settings is not "You". Split: **You** = personas and what characters know about them; **Settings** = app, models, appearance, language, data, about, feedback. |
| Data / export / delete | Not present | — | **add.** Local-first means the user owns the files: export a story, export everything, show where the data lives on disk, delete with a real confirmation. This is both a trust feature and, for Ko, a dealbreaker. |

---

## 7. `Sky-Activity`

**Now.** Memory events grouped by day and story, kind filters, one expanded item with a quoted line and "Open the line", side cards "Still being read" and a "How receipts fade" legend.

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| The destination itself | Top-level rail item | Fold into the continue block; make it a per-story view; keep for power users | **replace** (`F8`). As a top-level destination it promotes memory bookkeeping to the same rank as Characters — the exact thing the brief pushed back on twice. What survives: a **per-story "What changed"** section inside the continue block, and a full log reachable from a story's own menu and from Backstage. The rail item goes. |
| "Open the line" | Jumps to the message in context | Keep | **keep.** Excellent, and the reason the log should still exist somewhere. |
| "How receipts fade" legend | Explains memory decay | Keep, relocate | **keep** but move it to where decay is *shown* (the living card), not to a legend on a log page. A legend is a sign that the thing it explains isn't self-evident. |
| Kind filters | Filter by event type | Keep in the full log | **keep** in the demoted log. |
| "Still being read" | Background processing indicator | Keep | **keep** — honest about async work, which matters for a local app on slow hardware. |

---

## 8. `Sky-FirstRun`

**Now.** "They'll remember this." over clouds · three steps: Connect a model (active — found llama.cpp, Use this, Look again, or add an online API), Make yourself, Add your first friend · a privacy line · Continue.

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| "They'll remember this." | The promise, as the headline | Keep | **keep.** Four words that say what the product is. Do not touch it. |
| Step 1 = connect a model | Engine first | Three doors: try now / my server / my key | **replace** (`F1`, `F2`). The hardest step is first and it is the step most users cannot do. Restructure: a zero-configuration door with real visual weight, the auto-detected local server second (one click for Ko), an API key third. The words "llama.cpp", "API" and "engine" appear only inside doors two and three. |
| Auto-detection | Looks for a local server | Keep | **keep** — this is a genuinely delightful moment for the one user who has a server running, and it costs the others nothing. |
| Step 2 = make yourself | Persona before characters | Optional; after the first chat | **change.** Make it skippable with a good default ("You"). Sam does not know they need a persona until they have seen one matter. |
| Step 3 = add your first friend | Authoring as onboarding | Ship a cast | **replace** (`F3`). Step 3 becomes *choose someone to start with*, from four or five finished characters. Authoring is offered, not required. |
| Privacy line | A footnote | The second-loudest thing on the screen | **change.** "Nothing leaves this computer unless you connect an online model" is the differentiation. It belongs next to the model choice at real size, not as a footnote. |
| Three-step stepper | Linear progress | Keep | **keep**, but each step must be completable in one action. |
| What comes after | Not designed | — | **add.** The first thirty seconds *after* setup decide retention: land on Home with a cast and one obvious first move, not on an empty grid. |
| Import | Not present | — | **add** to first run: "Coming from somewhere else?" — import character cards. Cheap, and it is exactly the escapee's first question. |

---

## 9. `Sky-Models`

**Now.** Settings subnav · Models with "engine ok" · Servers and APIs (llama.cpp connected with qwen3.5-9b; OpenRouter with key stored; Test, Remove) · "Look for model servers" · "Add an API" · Jobs: Characters expanded with every field, Narrator / Memory reader / Reasoning / Recall by meaning collapsed.

| Element | Decision now | Alternative | Verdict |
|---|---|---|---|
| Per-job model assignment | Four+ jobs, each assignable | Keep | **keep.** This is a real differentiator — nothing in the competitor set assigns different models to narration, memory and reasoning. It deserves to be *shown off*, not hidden in settings. |
| Everything visible at once | Servers, APIs and all jobs on one page | Tiered | **change** (`F16`). This is the SillyTavern failure mode in miniature. Three tiers: a single status line ("Running on qwen3.5-9b · everything working") at the top; one collapsed row per job with its current model; every numeric parameter behind an explicit Advanced disclosure inside each job. |
| "engine ok" | Status string | A real status block | **change.** The most important thing on the page is *is it working right now* — with a plain-language failure and a fix when it isn't. |
| Test / Remove | Per-connection actions | Keep | **keep.** Test is essential; it is the only way a non-technical user can self-diagnose. |
| "Look for model servers on this computer" | Rescan | Keep | **keep.** |
| Key storage | "key stored" | Say where and how | **change.** For a local-first app, "stored in your OS keychain, never sent anywhere but the provider" is a trust statement worth the line. |
| Model picker | Presumably a dropdown of names | Show size, speed, and fit for the job | **add.** A user choosing between two GGUFs by filename is choosing blind. Show what it costs to run and what it's good at. |
| Failure states | Not designed | — | **add.** Server unreachable, model too large for RAM, generation timed out, out of disk. Each with one plain sentence and one action. This is where a local app lives or dies. |

---

## 10. Dark mode

**Now.** Four dark variants, produced by a token flip plus a `polish()` pass that rewrites shadows and accents.

**Verdict — change the method, keep the result.** That a post-pass is needed at all proves the light theme encodes decisions the tokens don't capture — mostly because glass makes every surface's real colour depend on what is behind it. Once §0.2 lands (opaque surface ladder), dark mode becomes a genuine token flip with no post-pass.

Two further notes: dark should be **built as its own palette, not an inversion** — warm-tinted near-black, not pure black, the way Linear does it. And all four dark screens need a contrast check against WCAG AA at the end of the design pass, especially the muted text (`#a9bce0` on `#1c2450` is close to the line).

---

## 11. Summary — what the four style directions must each answer

The audit produces eleven open questions. Each style direction has to take a position on all of them, which is what makes the four genuinely different rather than four skins.

1. What replaces full-bleed glass as the app's material?
2. What is the accent hue, and is it blue at all?
3. What carries the "above the clouds" metaphor once the gradient is calmed?
4. What is the display face, and what is the UI face?
5. How is importance expressed in the character grid — size, crop, chrome, or position?
6. Is the rail five items or four, and are Characters and Chats one surface?
7. What does the continue block look like as the hero of Home?
8. What does an empty Kataki look like on day one?
9. How does the app show a character's state without a memory bar and a stat tile?
10. What does a failure look like — and does it feel like the same app?
11. What is the one element a competitor could not have made?
