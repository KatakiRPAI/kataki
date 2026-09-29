# UX study · the Sky

Written 26 September 2026, before the design pass that follows it. It exists to answer one question before a single pixel moves: **who opens Kataki, what are they trying to do, and where does the current Sky get in their way?**

Everything here is grounded in two things: the sample world in `../sample-world/WORLD.md` (Liv, Mike, Halcyon Coffee, "Two Sugars, No Title"), and the competitor evidence in `COMPETITORS.md`. Where a claim comes from research it is linked; where it is a judgement call it says so.

---

## 1. Who this is for

Five personas. They are not demographic sketches — each one is a **different relationship to the app**, which is what actually changes the design.

### P1 · Sam, the escapee (the biggest group)

Came from Character.AI or Talkie. Left because of filters, memory loss, ads, or a UI change they hated — all four are documented complaint clusters. Not technical. Has never run a local model. Wants the thing they already had, minus the betrayal.

- **Mental model:** "It's a chat app with characters in it."
- **Opens the app to:** keep talking to one character they care about.
- **Vocabulary they already have:** character, chat, persona (maybe), memory.
- **Vocabulary they do NOT have:** model, context window, token, GGUF, quantisation, backend, sampler, lorebook, scan depth.
- **What kills them:** being asked to "connect a model" before they can do anything. This is the single highest-stakes moment in the whole product.
- **Success on day one:** a real conversation with a character who felt like a person, inside ten minutes, having understood every screen they passed through.

### P2 · Ko, the tinkerer

Came from SillyTavern, or is the sort of person who would. Runs llama.cpp or Ollama already. Reads changelogs. Has opinions about samplers. SillyTavern's own docs concede the learning curve is steep and its community treats that as a feature; Ko is the person who agrees.

- **Mental model:** "It's a front-end. Where are the knobs?"
- **Opens the app to:** see whether the memory engine is actually different, and to find out how fast they can get to the prompt.
- **What kills them:** a walled garden. If Ko cannot see the prompt, swap the model per job, or export their data, they leave in twenty minutes and say so publicly.
- **Success on day one:** found Settings → Models, pointed it at their own server, opened Backstage, read the actual prompt, and thought "oh, this is doing something new."

### P3 · Noor, the writer

Writing a novel, or a long-running serial. Uses the app as a character-simulation tool: what would Mike actually say here. Cares about **continuity** more than anything — that is why Kataki's memory engine exists.

- **Mental model:** "It's a writing room. Characters are the cast, stories are the drafts."
- **Opens the app to:** continue a story that is weeks old, and check what a character still believes.
- **What kills them:** losing work. An edit that silently rewrites twelve messages, an export that doesn't exist, a story that can't be organised into books.
- **Success:** can answer "what does Mike still know about the gala?" without reading the transcript.

### P4 · Priya, the returner

Has 200 hours in one story. Comes back after two weeks away. Is not starting anything — she is **resuming**.

- **Mental model:** "Where was I?"
- **Opens the app to:** get back into one specific scene as fast as possible.
- **What kills them:** having to remember. If the app makes her reconstruct where she was, it has failed at the one thing a memory app should be good at.
- **Success:** understood the state of her story in under five seconds from the home screen, and was back in the scene in one click.

### P5 · Dev, the drive-by

Downloaded it because someone posted a screenshot. Will spend four minutes deciding whether this is worth it. Might be a journalist, might be a curious dev, might be a fifteen-year-old — the app should not assume.

- **Mental model:** none yet.
- **What kills them:** an empty app. If the first screen after setup is a blank grid saying "Add a character", Dev closes it.
- **Success:** understood what the app is *for* without reading anything, from one screen.

### A note on all five

None of them is "the average user". The design has to hold **P1 and P2 at the same time** — that tension is the whole brief. Every rule in §5 exists to resolve it.

---

## 2. What each persona expects, screen by screen

This is the **expected journey** — what each persona thinks will happen — written before looking at what the Sky currently does. Divergence between this and §3 is the friction.

### P1 · Sam

1. Opens the app. Expects a welcome and a list of characters to try — like every consumer app.
2. Expects to tap a character and start talking.
3. Expects the app to ask for a login. (It won't. That needs saying out loud, as a *good* thing.)
4. Expects "settings" to contain notifications and dark mode, not inference parameters.
5. When something is slow, expects a spinner and a reason.

**Where reality bites:** step 2 is blocked by "connect a model". Sam has no model. Today's `Sky-FirstRun` does handle this — it looks for llama.cpp on the computer and offers an online API — but the language is still engine language, and there is no path that says "just start; I'll sort the model out for you."

### P2 · Ko

1. Opens the app. Expects to be able to skip onboarding entirely.
2. Goes straight for Settings. Expects Models, and expects to point it at `http://localhost:8080`.
3. Expects per-job model assignment (character vs narrator vs memory) — this is Kataki's real differentiator and Ko will look for it in the first two minutes.
4. Expects a command palette on `Ctrl+K`. Every tool they use has one.
5. Expects keyboard navigation everywhere, and will judge the app on whether `Esc` closes things.
6. Expects to find the raw prompt. Backstage delivers this; Ko needs to *discover* it, which today needs a trip into a story.

### P3 · Noor

1. Expects characters and stories to be separable — that a character can be in several stories.
2. Expects to organise: folders, books, tags. (Places & Plots does this; the character list does not.)
3. Expects to search across everything by text.
4. Expects export. Prominently. Local-first means nothing without it.
5. Expects editing a line to be safe by default and destructive only on purpose — which the Scene's two-button edit already gets right.

### P4 · Priya

1. Expects the home screen to open on **her story**, not on a grid of everything she owns.
2. Expects "what changed while I was gone" — not notifications, but *story* state: what a character now believes, what's unresolved.
3. Expects one click back in.

### P5 · Dev

1. Expects the first screen to explain the product in one sentence and one picture.
2. Expects to poke something without committing to anything.

---

## 3. Friction log

Every friction found in the current nine Sky screens, rated by how much damage it does. `H` = loses the user, `M` = costs trust, `L` = papercut.

| # | Where | Friction | Who it hurts | Sev |
|---|---|---|---|---|
| F1 | First run | "Connect a model" is step 1 of 3 and is a hard gate. A non-technical user has nothing to connect. | P1, P5 | **H** |
| F2 | First run | The word "model", "llama.cpp", "API key" and "engine" all appear before the user has seen a character. | P1, P5 | **H** |
| F3 | Home | After setup the grid is nearly empty. Nothing to do but author a character from scratch — a 6-step wizard. Backyard AI, Janitor and Chub all ship a starter roster for exactly this reason. | P1, P5 | **H** |
| F4 | Home | The home screen is a *browse* screen (greeting, search, character grid, moments) with the Continue card as one card among many. Priya's whole journey is that card. | P4 | **M** |
| F5 | Everywhere | No command palette. Ko expects `Ctrl+K`; Janitor AI already has it. | P2 | **M** |
| F6 | Nav | Six rail items (Home, Characters, Chats, Places & Plots, Activity, You) plus Settings. "Chats" and "Characters" overlap heavily in a user's head — a chat *is* a character, mostly. | all | **M** |
| F7 | Nav | "Places & Plots" is one destination holding two different object types with a shared filter tree. It is the most conceptually loaded item in the rail and it sits fourth. | P1 | **M** |
| F8 | Activity | An entire top-level destination for memory events. This is the "too much about memory" note the brief already flagged, promoted to the navigation. | P1, P4 | **M** |
| F9 | Add character | 6 steps before a character exists. Character.AI's own wizard is 8 fields but on **one** screen, and only name + greeting are required. | P1 | **M** |
| F10 | Add character | The completeness ring (60%) implies a character is deficient. Dani is *meant* to be half-finished. A progress ring turns a design intent into a nag. | P1, P3 | L |
| F11 | Profile | The Mike profile is 1500px of scroll with eleven sections. The one thing every persona wants — "Message Mike" — is above the fold, but everything after it is undifferentiated. | all | **M** |
| F12 | Profile | Four separate places show time ("Played 2 hours ago", the tile, the story rows, the hover). The two-clock idea is right; four surfaces for it is not. | P3, P4 | L |
| F13 | Chats | The thread list and the preview pane both show the same story. The preview pane repeats what the row says. | P4 | L |
| F14 | Library | The filter panel is a tree (books → stories) plus character chips plus three tabs plus a sort. Four filtering mechanisms on one screen. | P1 | **M** |
| F15 | You | The persona switcher is a menu inside a destination. Switching who you are is a *global* act; it is buried one level deep. | P3 | L |
| F16 | Models | Everything is visible at once — servers, APIs, four job assignments with every field. This is the SillyTavern failure mode, in miniature. | P1 | **M** |
| F17 | Everywhere | No visible feedback, bug-report or suggestion affordance anywhere in the Sky. The brief calls this non-negotiable. | all | **H** |
| F18 | Everywhere | No empty states designed except the character grid's Add card. No error state for "model server went away" — which, for a local app, is the single most likely failure. | all | **H** |
| F19 | Everywhere | No search results screen. There is a search field on Home and nothing behind it. | P3 | **M** |
| F20 | Everywhere | Text is baked into the layout at English widths. German is ~35% longer; RTL mirrors everything. Nothing in the current screens is built for either. | i18n | **M** |
| F21 | Everywhere | Portraits carry meaning (mood, state) with no text equivalent. Colour alone carries state in the candy filters and the memory bar. | a11y | **H** |
| F22 | Home / Profile | "Moments" (composed stills) is a lovely feature with no explanation anywhere of what it is or how one is made. | P1 | L |

---

## 4. The journey, rewritten

What the Sky *should* do, for each persona, stated as a target rather than a critique.

### First run — the ten-minute contract

The promise is **"a real conversation in ten minutes, and you understood everything you clicked."** That yields three rules:

1. **Never gate the product on the engine.** First run offers three doors, in this order of visual weight: *Try it now* (a bundled small model, or a trial-scoped hosted call, clearly labelled), *I have a model server* (auto-detected, one click), *I have an API key*. Ko takes door two in eight seconds. Sam takes door one and never learns the word "model".
2. **Ship a cast.** Four or five finished characters — the sample world is already built. The first screen after setup has people in it. This is the fix for F3 and it is the cheapest high-value change in the whole audit.
3. **Say the local-first promise once, in plain words, where it lands** — on the first screen, next to the model choice, not in a settings page. "Nothing leaves this computer unless you connect an online model." That sentence is the product's entire differentiation and it currently appears as a footnote.

### Returning — the five-second contract

Priya's home screen is not a browse screen. **Continue is the page, not a card on it.** The home layout should open with the last story at full width — the still, the last line, what changed — and the browse grid below it. Everything else on Home is secondary to that one block.

"What changed while I was gone" replaces the Activity destination (F8): it becomes a section of the continue block, in feelings language ("Mike has been thinking about the gala"), not event language ("3 new memory events").

### Going deeper — the power ramp

Ko's path must exist and must be **invisible to Sam**:

- `Ctrl+K` everywhere, opening a command palette over any screen.
- Settings → Models is two clicks from anywhere and progressive: one line per job, collapsed, with defaults that work.
- Backstage is reachable from the Sky, not only from inside a story.
- Every list is keyboard-navigable; `Esc` always closes; `/` focuses search.

### Writing — the continuity contract

Noor needs three things the Sky must not lose: **search that works across characters, stories, places and lines**; **export, visible, per story and whole-library**; and **organisation that scales past twenty characters** (books already do this for places and plots; characters need the same).

---

## 5. Balancing newbie and power user

Six rules. These are the resolution of the P1/P2 tension and they apply to every screen in the design pass that follows.

1. **Three tiers, always.** Tier 1 is always visible and has no jargon. Tier 2 is one click away behind a named control ("Advanced", "More", a `⌄`). Tier 3 lives in Settings or Backstage. Nothing is tier 1 unless a first-time user needs it in their first session. This is the explicit lesson from SillyTavern's flat, deep settings tree.
2. **Defaults must be good enough to never touch.** Every number with a sensible default is hidden by default. If a control has no good default, it does not belong in tier 1 — it belongs in the setup flow where it can be explained.
3. **Progressive disclosure is per-surface, not per-user.** No "beginner mode" account setting. A mode toggle splits the product in two and means every screen gets designed twice; the Scene's Simple/Advanced composer toggle is the one exception, and it is scoped to the composer only.
4. **Power is keyboard, not chrome.** Shortcuts, the command palette and direct manipulation give Ko everything without adding a single button Sam has to ignore. Teach them the way Linear does: a contextual hint on hover, never a modal tour.
5. **Jargon is earned.** A term appears in tier 1 only after the app has shown the thing it names. "Memory" is fine after the user has watched a character remember. "Context window" never appears in tier 1 at all.
6. **Never remove a shipped affordance silently.** Janitor AI's silently-removed mobile search was the single most repeated non-performance complaint in the research. Every visible change gets a changelog entry the user can reach from the app.

---

## 6. The four always-present flows

The brief names these as non-negotiable; they are specified here so the design pass has to place them.

| Flow | Where it lives | Rule |
|---|---|---|
| **Feedback** | A persistent, low-weight affordance in the Sky's rail footer, and in the Scene's ⋯ menu. | Two clicks from anywhere, never a modal that blocks work, never a link that opens a browser to a form. |
| **Bug report** | Same entry point, second option. Attaches app version, OS, model config and the last error — **shown to the user before sending**, with every field removable. | A local-first app cannot silently upload diagnostics. Consent is the whole design. |
| **Suggestion** | Same entry point, third option. | Should be able to attach the screen the user is on as a screenshot, again with a preview. |
| **Changelog** | Settings → About, plus a one-line dot on the rail footer after an update. | Every visible UI change gets an entry. Dismissible, never modal. |

---

## 7. Accessibility and language, as UX not as compliance

Treated in full in the design system; the journey-level requirements are:

- **State is never colour alone.** The candy filters, the memory bar, the mood chips and the completeness ring all currently rely on hue. Each needs a second channel: text, shape, or position.
- **Portraits have alt text that is about the character, not the file.** "Mike, leaning on the counter, looking wary" — the mood *is* content.
- **Every image that carries mood needs a text mirror in the DOM**, because mood is the app's core signal and a screen-reader user must get it.
- **Keyboard: every screen completable without a mouse**, focus visible against both themes, focus never trapped, and the Scene's widget-drag layer needs a keyboard equivalent (move with arrows, `Space` to pick up).
- **Motion respects `prefers-reduced-motion`** — the dive, the cloud parting, the streaming caret and the crossfade all need a reduced form that still communicates the state change.
- **Text scales to 200%** without clipping. The current fixed-height cards will break; sizes need to be min-heights.
- **Layout is language-agnostic:** no text baked into fixed-width chrome, ~35% expansion headroom on every label, logical properties (`margin-inline-start`, not `margin-left`) throughout so RTL is a `dir="rtl"` flip rather than a rebuild. English ships first; the layout must not have to change when Arabic does.

---

## 8. What this study changes

The seven decisions the design pass inherits from this document:

1. First run offers a zero-configuration door and ships a cast. (F1, F2, F3)
2. Home opens on continuing, not on browsing. (F4)
3. Activity stops being a destination and becomes "what changed" inside the continue block. (F8)
4. The rail loses an item; Characters and Chats are reconsidered as one surface with two views. (F6)
5. A command palette exists on `Ctrl+K`. (F5)
6. Feedback, bug report, suggestion and changelog get a permanent home in the rail footer. (F17)
7. Empty, loading and error states are designed for every screen, starting with "your model server went away". (F18)
