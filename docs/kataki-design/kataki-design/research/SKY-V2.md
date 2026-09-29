# The Sky · dark, rebuilt

The direction. The five style studies stay as reference; this is the one to build.

It is the dark Sky you already had — night above the clouds, stars, moonlight, the orb, the painted art — with every finding from `AUDIT.md` and `UX-STUDY.md` applied.

**29 screens** (`screens/html/Sky2-*.html`): every destination, every settings panel, every menu, the states that have never existed, and four proof boards — Day theme, 1024 wide, Arabic right to left, and Accessibility, measured. The Scene has been moved onto the same surfaces.

> **v2.1 — the 10/10 pass** is at the end of this file. Where it contradicts something above, v2.1 wins.

---

## The whole inventory

| | Screen | What it settles |
|---|---|---|
| **Core** | Home | Continue as the hero. "While you were away" instead of an Activity page. Asymmetric character grid. |
| | Mike's profile | Portrait, one primary action, tabs, the living card, moments, export. |
| | Stories | Chats and Characters merged. By story / By character. Two-line times. Full story preview. |
| | World | Places and plots under a books tree. Time strips, plot quotes, the Link dialog. |
| | Characters | Grid and list, filters with counts, a hover card with its quick actions, groups. |
| | You | Personas, the Director, and "Who knows Liv" per character per story with a forget control. |
| **Making** | New character | One page. Two required fields, six optional sections collapsed, live preview, import. |
| | New story | Who, you, where, what — three of four optional — with a live scene summary. |
| **First run** | Step 1 | Three doors; the first needs no configuration. Privacy at full size. |
| | Step 2 | Pick one of the six shipped characters. Persona optional. |
| **Finding** | Command palette | `Ctrl K` over anything: jump to, lines, and do. |
| | Search results | One surface across lines, stories, characters, places, plots and memories. |
| | Every menu | Seven menus on one board: persona, story ⋯, character ⋯, sort, filter, time hover, theme. |
| **States** | Empty · day one | The six shipped characters *are* the empty state. |
| | Model server went away | What happened, what still works, four causes, one fix each. |
| | Feedback and bug report | Three kinds, one dialog, every attachment listed and removable. |
| | Opening | Cold start with real steps, not a spinner. |
| **Settings** | General | Startup, autosave, edit history, updates, telemetry (off, and unbuildable). Story defaults. |
| | Appearance | Night / Day / system, text size to 150%, reduce motion, stars, story face, high contrast — and what is deliberately *not* adjustable. |
| | Language | Six languages, RTL marked, automatic mirroring, the 12/24-hour rule, and how to add one. |
| | Models | One status line, three connections, five jobs collapsed, everything numeric behind Advanced. |
| | Memory and thinking | How fast memories fade, whether they can be wrong, whether they can doubt you, how far back they look. |
| | Data and privacy | Where every file is on disk, export, backups, import, delete. |
| | Shortcuts | Nineteen, grouped, all remappable. Nothing needs a mouse. |
| | About | Version, the three feedback routes, and the changelog. |

---

## The refinement pass

Five things changed across every screen after the first five were drawn:

1. **The sky got quieter** *(reversed in v2.1: the sky now shows, and passes the audit)*. Stars are down from ~190 to 120 and confined to the top 460px; below that a gradient scrim darkens the ground so text sits on something calm instead of competing with the sky. The sky is now strongest exactly where there is no content.
2. **Numbers are tabular.** Every time, count, size and version uses lining tabular figures, so columns of times stop jittering.
3. **A real focus ring.** `0 0 0 2px ground, 0 0 0 4px accent` — visible on the night ground, shown on the composer field in New character.
4. **Tighter display tracking** (−0.015em) so Baloo 2 holds together at 32px and above.
5. **Two new shared parts** that made the other twenty screens cheap and consistent: a settings row (title / description / control, right-aligned, with a hairline) and a floating menu (glass, because it floats), which is what every menu on the Every-menu board is built from.

---

## What stayed

The sky itself, as a real sky: a gradient, stars, moonlight from the top right, moonlit cloud along the top. The painted portraits and places. The two clocks (real time outside a story, story-relative inside, exact on hover). The warmth.

## What changed, and why

| Was | Now | Why |
|---|---|---|
| Frosted glass on every surface | **Opaque four-step ladder**: sky → `#131b3a` panel → `#1a2348` raised → `#212b57` overlay. Glass survives in exactly one place: the floating Link dialog. | Text contrast became calculable instead of depending on the art behind it, and the dark theme stopped needing a post-pass to fix. Decorative glass is also the #2 item on the slop checklist. |
| `0 14px 34px rgba(62,92,170,.14)` glow under everything | A 1px hairline for surfaces; **one real shadow** reserved for things that float (hero panel, stills, dialog) | Glow-under-every-card is a named AI tell. Elevation now comes from the ladder. |
| Six radii applied by eye | **6 / 10 / 16**, plus a pill for two roles only: the primary action and status chips | A radius scale that means something. |
| Violet-leaning gradient `#0d1330 → #241f52` | A blue night that stays blue: `#080d24 → #0d1533 → #121c42 → #16224c` | Off the indigo-violet axis the research flags, without stopping being a night sky. |
| One pale blue accent doing every job | **Two**: a deeper blue `#5b86ff` for actions and focus, and a lamplight amber `#e7b06a` for state — what a character feels, what they're holding onto, the secret, the pinned thread | A single pale-blue chrome reads as generic. Amber also ties the Sky to the Scene's lamplit places. |
| Candy filter chips, hue-coded | Neutral chips with counts; selected = filled, not coloured | Hue as the only channel fails colour-blind users and fights the portraits. Counts are more useful than colour. |
| **Chewy** for display | **Baloo 2**, paired with **Baloo Bhaijaan 2** for Arabic | Chewy has one weight and no non-Latin coverage. *Correction:* Baloo 2 itself covers Latin and Devanagari, **not Arabic**; its sibling Baloo Bhaijaan 2 is the Arabic cut, drawn to match. Both are vendored in `assets/fonts/`. |
| Rail: Home · Characters · Chats · Places & Plots · Activity · You | Rail: **Home · Stories · Characters · World · You**, with "New character" under a rule, and Settings / Feedback / Light in the footer | Activity is gone as a destination. "Places & Plots" became **World**. "Chats" became **Stories** with a By story / By character toggle. |
| An Activity bell with a badge | Nothing | There is no one else acting in a single-player local app. |
| Continue as one card among several | **The hero.** Full width, the still at 448×332, the last line in Newsreader, the state line, and one primary button | Priya's five-second contract: know where you were, be back in one click. |
| "3 new memory events" | **"While you were away"** — three sentences in feelings language, under the hero | Feelings, not telemetry. This is what replaced the Activity page. |
| Equal 4-up character grid | **Asymmetric**: the character you played last at 324 wide, four at 164, then Add | Importance expressed by size, not by a uniform repeating unit. |
| Dani's 60% completeness ring | A **"Draft"** chip, plus a real no-portrait state (initial + "no portrait yet") | A ring nags. A chip states a fact. |
| Three stat tiles on the profile | One sentence: *"Four stories together since May. He has met Theo, and did not like it."* | The dashboard reflex, removed. |
| Eleven flat profile sections | Two tabs (**Story** / Profile) and a two-column layout with the living card pinned right | The page now fits without eleven equal-weight stops. |
| Memory bar labelled "Memory" | **"What he still holds onto"**, three lines, each with a word (*going hazy · held tight · doubted*) as well as a bar | Non-colour channel for state, and language a person would use. |
| No search destination | `Ctrl K` field across characters, stories, places, plots and lines | The field existed and led nowhere. |
| Places & Plots: a tree **and** chips **and** tabs **and** a sort | **World**: books tree in the sidebar (primary), one filter row, one sort | Three ranked mechanisms instead of four competing ones. |
| No feedback anywhere | **Feedback** in the rail footer, on every screen, with a dot for the changelog | Named non-negotiable in the brief. |
| First run: "connect a model" as a hard step 1 | **Three doors**: Start now (bundled model, no configuration) · Use a model server (auto-detected) · Use an online model. Privacy promise at full size. Six characters shipped. Import cards offered. | The single highest-severity friction in the study — the biggest group of users cannot complete the old step one. |

## Still to draw (v2 — items 1, 4 and 5 are done in v2.1)

1. **The light theme** — its own palette built from these surfaces, not a flip.
2. **Empty World, empty Stories, no search results** — the three remaining empty states.
3. **Edit character** and **group scene setup** (both are variations of pages that now exist).
4. **Tokens and the component library** regenerated from this, replacing `tokens.json` and `components.css`.
5. **The Scene**, brought onto these surfaces — it is still on the old glass, and it still uses the orb.

## The no-LLM-copy pass

The first version of these screens had sentences that only a model could write — *"Four stories together since May. He has met Theo, and did not like it."*, *"Mike is turning that over."*, *"Theo still has not come back from the storeroom."* They read well and cannot ship: each needs a summarisation call over the whole relationship, on every render, with no cache key and no offline behaviour.

All of it is gone. Every string in the Sky is now one of four things — static copy, authored content, a computed value, or a row a model wrote **once at turn time** and the UI only reads. The rule, the enums, the templates and a string-by-string inventory are in **`COPY-RULES.md`**.

What changed on the screens:

| Was (needed a model) | Now (a query, an enum, or a stored row) |
|---|---|
| "Four stories together since May. He has met Theo, and did not like it." | `4 stories · 412 lines · together since 24 May · 2 places` |
| "Mike is turning that over. He is not sure you said what he remembers." | A `Doubtful` pill + `41 memories · 2 changed since you left` |
| "Mike has been turning over what you said at the gala." | An event row: **Memory faded** — "She didn't want to be on the gala list." — `sharp → hazy` |
| "He is glad you came and certain you said something you did not say." | Three stored scores: warmth 72, trust 54, doubt 46 |
| "knows your mother is the queen's step-sister" | `12 memories from this story` + a `1 doubted` pill |
| "Mike remembers your last four stories. Theo has never met you here before." | `Mike — 63 memories · 4 stories · knows this place` |

The test: **a screen must render with the model server stopped.** `Sky2-Error.html` is the proof that the app is designed for it.

---

## Removed since the first pass

**The orb.** The glossy blue sphere beside "Dive back in" is gone from Home and Stories. It was a signature that had to be explained, and next to a painted still it was the second most decorative thing on the page competing with the first. The dive is now carried by the button and the still it sits beside. (The Scene screens still show it; it comes out of those in the same pass.)

---

## v2.1 — the 10/10 pass

The 7.5 review named what was wrong. Each item below was fixed and then **measured**, not eyeballed.

### How it was measured

A headless browser renders every board with the real vendored fonts, walks every text node, blanks the text, photographs what is behind it, and computes the WCAG contrast ratio of each run against the actual pixels (10th percentile, so gradients and photos count). Text under an open modal or inside an `inert` region is skipped, as WCAG 1.4.3 allows.

| | Before | After |
|---|---|---|
| Text runs audited (Sky + Scene, 43 boards) | 2,120 | 2,354 |
| Below WCAG AA | **411** | **0** |

The scripts are in `source/audit/` so the check can run in CI against the real app.

### What changed

| Was | Now | Why |
|---|---|---|
| `FAINT #6d7ba3` — 3.6:1 on raised panels | `#95a2cb` — lowest 4.6:1 anywhere; `MUT` lifted to `#aebbdc` to keep three steps | The single biggest source of failures (≈300 of 411). |
| Accent `#5b86ff` used as link text — 4.6:1 on raised, 4.1 on overlays | Split: `accent #5b86ff` for fills, bars and the focus ring; **`accent-text #86a6ff`** for words | One colour cannot be both a fill and small text on four surfaces. |
| Primary button: gradient `#6f95ff → #3a63e8` with a blue glow; white text 2.8:1 at the light end | **Flat `#3558d6`**, no shadow. White label 6.0:1 | The glow was an AI tell and the gradient failed contrast on its own label. |
| Chip counts at 60% opacity | A colour, not an opacity | Opacity text is unmeasurable and failed on every chip. |
| The sky hidden behind a scrim and a hero panel | **The hero sits on the sky.** Stars across the top 560px, one crescent moon, a moonlit cloud bank behind the hero; the ground only takes over below the fold | The sky is the product's signature. It now shows on Home, Profile and every settings page without costing contrast (audited). |
| Baloo and Figtree at similar weights everywhere | **Story-world names are set in Newsreader** — stories, characters, places, books — like a title page. App chrome keeps Baloo 800 | Two voices: the app speaks in Baloo, the story speaks in Newsreader. Hero title 50px, profile name 54px. |
| "Dive back in" beside "New story" on some screens, "Continue" on others | **Continue** everywhere you resume, **New story** everywhere you start | One verb per action. |
| The Scene on warm brown glass with amber Send | **Same ladder, translucent over the place art.** Navy glass, `#eef2ff` ink, flat blue Send, amber kept only for memory and state. The time skip is a night card under rolling cloud, not a white card | It now reads as one product. The warm painted places stay. |
| Only one theme | **Day**: its own palette (`#edf2ff` ground, white panels, `#0f1733` ink, darker amber `#8a4f0a`), a daylight sky with sun and cloud. Board: `Sky2-Home-Day` | Built from the same token names, audited to the same bar. |
| Only one width | **1024 wide**: rail folds to 72px icons (labels kept for screen readers), four characters instead of five, the hero still narrows to 360. Board: `Sky2-Home-Compact` | The smallest supported window. |
| RTL claimed, never drawn | **Arabic, mirrored**: `Sky2-Home-Arabic` | See below. |
| Accessibility asserted | **`Sky2-Access`**: contrast matrix for both themes (computed from tokens), focus ring, keyboard order, reduced-motion substitutions, the 200% text proof, target sizes | Every number on it is produced by the build. |

### Right to left — the rules the Arabic board proves

1. **Logical sides only.** Every `left/right` in layout is `inset-inline-start/end`, `margin-inline-*`, `text-align: start/end`. The board was produced by flipping those and nothing else, which is how the app should work.
2. **Fonts:** display Baloo Bhaijaan 2, UI IBM Plex Sans Arabic, story Noto Naskh Arabic.
3. **No letter-spacing and no italics** in Arabic (tracking breaks the joins; Arabic has no italic). Eyebrows lose uppercase and tracking.
4. **Small sizes go up:** 12px and below +2px, up to 15px +1px. Line height for Naskh titles 1.45.
5. **User content keeps its own direction.** Anything the player wrote is wrapped in `<bdi>` (or `dir="auto"`). The board leaves one English story — *The Long Way Home* — inside the Arabic UI on purpose, to show it.
6. **Plurals through ICU MessageFormat**, never string concatenation: Arabic has six plural forms (`قبل ساعتين` is the dual of "2 hours ago").
7. **Western digits by default**, `م` for pm; Eastern Arabic digits are a setting.
8. The **moon mirrors** with the layout; arrows in running text flip (`واضحة ← ضبابية`).

### Still to draw

1. Empty World, empty Stories, no search results.
2. Edit character and group scene setup.
3. Day and RTL versions of the remaining screens — mechanical now, since both are token and direction switches the generator already does.
4. A usability test with five people from the personas in `UX-STUDY.md`. Nothing here has met a user yet; that is the one thing the design cannot measure about itself.
