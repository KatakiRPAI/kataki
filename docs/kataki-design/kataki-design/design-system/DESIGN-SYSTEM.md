# Kataki RPAI design system

Kataki is a local-first desktop app (Electron, Windows first) for AI role-play with characters who remember. This document is the contract between the design and the code. Values live in `tokens.json` / `tokens.css`, component styles in `components.css`, and a live gallery in `components.html`.

---

## 1. Principles

1. **Two worlds, one crossing.** Outside a story you are in the **Sky**: bright, social, playful. Inside a story you are in the **Scene**: warm, dim, cinematic. The **dive** through the clouds is the only way between them, and it should feel like a signature.
2. **Memory is shown, not told.** Who heard a line, who will remember it, and how clearly are the product's core. Show them as small, quiet, beautiful signals: receipts, callouts, fading. They should never need explaining.
3. **The text is the hero in a scene.** The stage is alive but subordinate: the text column always sits on a scrim, and the controls fade while you read.
4. **Friendly on the surface, exact underneath.** Sky screens are playful. Models, Backstage and anything technical stay precise: real names, real numbers, mono type.
5. **Light on the GPU.** The AI model often shares the graphics card. Use layered images, transforms, opacity and crossfades. No per-frame blurs, no WebGL, no heavy 3D.
6. **Characters are fictional.** Use illustrated or painted art only, never photos of real people. Keep mockups general-audience.

---

## 2. Foundations

### 2.1 Typography

| Role | Family | Where |
|---|---|---|
| Display | **Chewy** | Big moments in the Sky only: the greeting name, page titles (Chats, Activity, Models), profile names, the First run headline. Never inside a scene. |
| UI | **Figtree** | All interface text in every world. |
| Story | **Newsreader** | Story prose (19/1.5), story titles, title cards, the time-skip lettering, peek card names. |
| Mono | **JetBrains Mono** | Backstage, model ids, hosts, JSON, token counts. |

The scale is in `tokens.json → type`. The key sizes:

- story body 19/1.5
- h2 22/800
- h3 16/800
- UI body 14–15
- caption 12
- eyebrow 11/700, +0.12em, uppercase

Actions inside story text are `*italic*` in `--k-scene-action`, and emphasis is `**bold**`.

### 2.2 Colour

**The Sky**
- background: gradient `#e4f0ff → #c3dafc → #aec4f7 → #b9b3f2`, with a cloud layer (`assets/places/clouds.svg`) near the bottom
- ink `#14264d`, muted `#4b5d82`, accent `#2f63f0`
- glass: white at 60%, 1 px white border at 92%, soft blue shadow, 16 px backdrop blur
- candy icon pairs (blue, pink, purple, green, orange, gold), for icon tiles and filters
- character backdrop gradients, one per character, used behind their portrait and avatar
- Activity event colours: memory `#e59a1e`, feeling `#ff5d7e`, belief `#8a63f0`, time `#2f9bd6`

**The Scene**
- background `#0e0a08`, story ink `#f4e9da`, muted `#cdbba4`, action italic `#dcc8ad`
- **amber `#f0b35a`** is the one accent: Send, memory glow, "will remember"
- **lilac `#cbb8ff`** is for beliefs, **rose `#f4a595`** for feelings and distrust
- speaker colours: persona (Aren) cool blue `#a9c8ff`; characters warm (Mira `#f2b870`, Tobin `#e8cc6a`). Assign each new character a warm speaker colour at creation.

**Backstage**
- blueprint background `#06203f` with a 24/120 px grid; panel `rgba(8,28,54,.86)`
- line `#8cc3ff`, ink `#e4f0ff`, muted `#9db8d8`, tier gold `#ffd08a`
- prompt part colours: rules, cards, memory, examples, history, tail

**Contrast:** body text is at least 4.5:1 in every world. Muted text on Sky glass is about 6:1. Scene muted on the scrim is about 7:1. Never put text straight on art without a scrim.

### 2.3 Shape, space, elevation

- **Radii:** 8, 12, 14, 16, 20, 22, 24, 28 (cards), 32, 34 (hero cards), pill. The Sky uses generous radii everywhere. In the Scene, keep pills and 22 px panels. Backstage is tighter (8 and 16).
- **Spacing steps:** 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 40.
- **Elevation:** Sky glass shadow `0 14px 34px rgba(62,92,170,.14)`, hero cards `0 24px 50px rgba(30,50,120,.3)`, overlays `0 30px 70px`. The Scene has no shadows except the peek card and the character drop shadow.
- **Hit target:** at least 44 px. Dense rows can use 34 px buttons, but the whole row stays clickable.

### 2.4 Iconography

There are 66 line icons: 24×24, 1.8 stroke, round caps and joins, `currentColor`. They're in `icons/sprite.svg` (symbols `i-<name>`) and `icons/icons.json`.

- On a candy tile, draw the icon white with a 2.2 stroke.
- Icon-only buttons need an `aria-label`.
- No emoji anywhere.

**The orb** is the brand object: a glossy deep-blue sphere with a white rim and a slow "breathing" glow. It always means "dive into a scene".

### 2.5 Motion

| Token | Value | Use |
|---|---|---|
| quick | 120 ms | hover, press |
| base | 200 ms | toggles, chips |
| slow | 320 ms | cards, callouts landing, peek |
| scene | 600 ms | characters stepping in or out, light changes |
| dive | 900 ms | Sky ↔ Scene crossing |
| time-skip | 1800 ms | the time-skip sequence |

- **Sky:** things float, bounce and settle. Use the `bounce` ease for appear and hover (cards lift 4 px, candy tiles straighten from −4° and hop).
- **Scene:** crossfades, slow parallax (2–6 px), light flicker done with opacity. No bounce.
- **Reduced motion:** the stage becomes still images with crossfades, with no parallax, bounce or breathing orb. Every duration token collapses to 0 (see `tokens.css`).

**The dive, going in:** the clouds (two copies of `clouds.svg`, one mirrored) scale up by 1.2 and part left and right. The sky gradient fades to the scene's still frame, then the stage fades from 0 to 1 at 1.02 → 1.0 scale. The UI (top bar, conversation, composer) fades in last.

**The dive, coming out:** the reverse, floating up. The thread saves a still of the last moment as its cover in Chats and on the Continue card.

---

## 3. Layout

**Sky (1440×900)**
- nav rail: glass, 92 px wide, at left 20 / top 20 / bottom 20, radius 32
- content: starts at x 144, 24 px right margin
- headers: greeting or title on the left; search, bell and main action on the right

**Scene (1440×900)**
- **Stage:** the place image fills the window, then characters, then a foreground layer (table), then the vignette.
  - One-to-one: the character is large and close (about 640 wide, face centre around x 410).
  - Two or three present: the speaker is in front and lit, the others are smaller and softened (`brightness .62, blur 1.5px, sepia .2`).
  - More than three: extra people go into an avatar row.
- **Top bar** (88 px, top scrim), left to right:
  - cloud button (back to the Sky)
  - story title with "with Mira · as Aren"
  - place + clock pill with a sun/moon arc
  - "Playing …" with mute
  - Backstage switch, reading mode, menu
- **Conversation column:** a scrim from x 740 to the right edge, text column x 836, width 560. Lines stack from the bottom, and the top edge fades out.
- **Composer:** from x 822 to 24 px from the right, 24 px from the bottom.
- **Tray:** left 24, top 300, width 206. People who are away or could join.
- **Reading mode:** hides the tray and top bar and widens the text over a blurred stage.

**Backstage:** the same window. Memory panel on the left (about 820 wide); Prompt, Cast and Reading stacked on the right (about 548 wide).

At 1280 wide, shrink the character and move the text column left. At 1920, grow the stage and keep the text column at most 600 wide.

---

## 4. Components

Class names refer to `components.css`. Each entry lists anatomy, then states. `components.html` shows all of them.

### 4.1 Sky

- **Glass card** `.k-glass` / `.k-card`
  - Anatomy: an h3 title with an optional right-aligned action, then content with a 14 px gap.
- **Button** `.k-btn`, with variants `--dark` (the main action on a screen), `--primary` (accent), default (white glass), `--ghost`, `--danger`, and sizes `--sm` / `--lg`.
  - States: hover lifts 1 px, active presses, visible focus ring.
- **Icon button** `.k-icon-btn` with an optional `.k-badge-count` (pink, white border).
- **Chip** `.k-chip` (filter; `aria-pressed`), **Tag** `.k-tag`, **Status** `.k-status` (`--idle`, `--warn`; dot plus text).
- **Candy tile** `.k-candy` (+ colour modifier) and **Candy filter** `.k-candy-filter`
  - A tile with a label below; the selected one's label gets bolder.
- **Orb** `.k-orb`
  - Sizes: 54 (rail), 48 (Message button), 70–74 (Continue card, Chats preview).
  - Always paired with the words "Dive in" or "Dive back in", or an aria-label.
- **Nav rail** `.k-rail`
  - Contents: logo (cloud tile + "Kataki"); Home, Friends, Chats, Places, Activity, You; a spacer; Settings; the orb with "Dive in".
  - Active item: white pill, accent colour, `aria-current="page"`.
- **Avatar** `.k-avatar` (`--s`, `--bg`)
  - A circular crop of the portrait art on the character's backdrop gradient.
  - `.k-avatar--ring` for your own avatar, which opens the persona switcher.
  - `.k-avatar-stack` for group threads.
- **Portrait + name plate** `.k-portrait`, `.k-nameplate`
  - Art anchored to the bottom, a soft light bloom top-left, and a strong-glass plate at the bottom.
- **Friend card** `.k-friend-card`, 196×268
  - Contents: portrait, favourite heart (top right), name, one-line tagline (2 lines max), status ("At The Gull · Year 7", "Not in a story yet").
  - A new friend shows a completeness ring top-left.
  - Hover lifts. Clicking opens their profile.
- **Continue card** `.k-continue`
  - A still of the last scene with the character in it, a scrim on the right, and a "Continue · N new memory events" chip.
  - Also: the story title (Newsreader), place, clock and persona, the character's last line, and the orb with "Dive back in".
- **Event item** `.k-event--memory|feeling|belief|time`
  - The avatar carries a coloured kind badge. Below the text: story and story clock.
  - Clicking opens the line it came from.
- **Stat tile**: a candy tile plus a big line ("Remembers 38 things") and a small line ("about Aren").
- **Living profile / Right now card**: labelled rows (Last seen, Holding, Wearing, Feels about you) and a memory bar (sharp solid, hazy striped, forgotten as the empty remainder).
  - A story selector chip ("In The Third Floorboard ▾"), because memories belong to a story.
- **Speech bubble** `.k-bubble`: the character's avatar with a white bubble with a squared bottom-left corner. Used for How they talk and How they say hi.
- **Secret card** `.k-secret`: dark indigo, lock icon, "Only Mira knows this", the text blurred at 7 px, and "Reveal as author" (`.is-revealed` unblurs it).
- **Completeness ring** `.k-ring` (`--p`): paired with a nudge ("Add a secret to make Wren more real").
- **Inputs:**
  - `.k-search` (glass pill)
  - `.k-field` + `.k-input` / `.k-select`
  - `.k-textarea` (large, accent border, focus halo)
  - `.k-seg` segmented control
- **Stepper** `.k-step` (`is-done` shows a green check; the current step uses `aria-current="step"` with a blue ring).
- **Thread row** (Chats)
  - Contents: stacked avatars, title, pin, story clock (in place of a real timestamp), last line (one line, ellipsis), "as Aren" in accent, and a gold memory-event badge with a spark.
  - The selected row is solid white.
- **Persona switcher** (dialog anchored to your avatar)
  - One row per persona (avatar, name, tagline, a check when selected), then "Director · Play no one", then "+ New persona".
  - A footnote: "Each chat keeps the persona it started with."
- **Server card** (Models)
  - Contents: candy tile, name, host in mono, status badges ("connected", "qwen3.5-9b loaded", "key stored"), Test and Remove.
- **Job card** (Models)
  - Collapsed: icon, job name, model or "Same as Characters", a detail line.
  - Expanded (Characters shown): Server, Model, Context size, Thinking (As the model likes / On / Off), Kind (Detect automatically / Standard / Reasoning + "Detect now"), Sampler preset, and a JSON box.

### 4.2 Scene

- **Stage** `.k-stage`: layers are place, characters (`.k-stage__char`), foreground, vignette.
  - Character states: speaking (lit), `.is-softened` (present, not speaking), `.is-entering` / `.is-leaving` (600 ms step in or out from the right), away (only in the tray, greyscale).
  - Expressions swap by crossfade: neutral, smiling, wary, surprised, doubtful, thinking.
- **Top bar** `.k-topbar`, with scene pills `.k-scene-pill` and round buttons `.k-scene-round`.
  - **Sun/moon arc:** a dashed arc with the sun or moon placed by the story clock (dawn at the left, noon at the top, dusk at the right, night shows the moon).
  - **Backstage switch** `.k-switch.is-on`.
- **Tray** `.k-tray`
  - Title "Nearby", a list of people (avatar, name, "away · at the bar" / "could join"), "Bring someone in", and a drag hint.
  - Dragging onto the stage brings a person in; dragging off the stage sends them away.
- **Line** `.k-line` (`--speaker` colour)
  - Anatomy: speaker name, story-clock stamp, optional spark, optional marks ("edited", "stopped"), the prose, receipts, then any callouts.
  - **Hover / focus** shows the tools pill top-right: `‹ 2/3 ›` takes (the last arrow rolls a new take; choosing an earlier take switches the branch), Edit, Hide.
  - **Hidden line** `.is-hidden`: dimmed with a dotted strike. It stays in the story but never reaches the AI.
- **Receipts** `.k-receipts`
  - A row of 16 px avatars plus a short text. Quiet by default (80% opacity), full on hover.
  - Expanded variant: `.k-receipt-chip` pills with labels.
  - See §5 for the states.
- **Callout / reaction** `.k-callout` (memory amber, `--feeling` rose, `--belief` lilac)
  - Anatomy: avatar, icon, sentence.
  - Lands with a small bounce when the memory reader files it. `.is-faded` after a time skip.
- **Spark + recall** `.k-spark`, `.k-recall`
  - A spark after the stamp marks a reply that drew on memory.
  - Hovering shows "MIRA REMEMBERED, VAGUELY", the recalled text, a clarity meter (`.k-clarity[data-level]`) and its source ("hazy · witnessed Day 1 · once sharp: …").
- **Title card** `.k-titlecard`: "The Gull · Day 1, 19:00" and "Six years later · Year 7" (with Undo).
- **System note** `.k-sysnote`: arrivals and departures.
  - Arrival: "Tobin joins" + "Brought in by you · he hears everything from here on" + Undo.
  - Departure: "Tobin left. He won't hear what's said now." with a greyscale avatar.
  - Newly met, narrator-voiced people ("a hooded stranger") appear as a lighter silhouette card.
- **Name card**: a floating glass card on the stage when someone steps in (avatar, "Tobin joins" in Newsreader italic, their tagline).
- **Thinking and streaming:**
  - "Mira is thinking…" with three pulsing amber dots and "Her notes stay backstage · read them".
  - "Mira is trying to remember…" when recall is slow.
  - Streaming text ends in an amber block caret `.k-caret`, and the stamp reads "writing…".
  - After the reply, a collapsed "Thought for 4 s" chip opens the notes backstage.
- **Composer** `.k-composer`
  - **Top edge:** the token meter (`--used`, 0–1).
  - **Row 1:** who will hear (avatars) + "Only Mira will hear this" / "Mira and Tobin will hear this", away people greyed ("Tobin is away"); on the right, Pass time (menu: a few hours, next morning, a week, years…) and Continue.
  - **Row 2:** textarea in Newsreader 18. Placeholder "Speak or act as Aren…", or "Direct the story…" when playing no one.
  - **Row 3:** modes `.k-modes` (Say, Do, Whisper, Think) on the left; Send `.k-send` or, while a reply streams, Stop `.k-stop` on the right ("Stopping keeps what Mira has written so far").
  - **Row 4:** "Who answers": Whoever fits, one chip per present character, Narrator.
  - **Keys:** Enter sends, Shift+Enter adds a new line.
  - **Whisper** changes row 1 into a picker of who hears. **Think:** "No one will hear this".
- **Peek card** `.k-peek`: a glass card over the stage when you click a character.
  - Header: avatar, name, expression chip, one-line role · present.
  - Right now: Holding, Wearing, Where, Injury.
  - On her mind: a tier + what she recalled for her last line.
  - What she knows about you: the count, two sample memories with tiers, and a link to Backstage.
  - Relationship chips; the Secret (blurred, Reveal).
  - Actions: Let her answer next (amber), Send away, Edit.
- **Tier badge** `.k-tier`: sharp (solid), hazy (dashed), forgotten (dotted grey).
- **Time skip** `.k-timeskip`: see §5.3.

### 4.3 Backstage

- **Panel** `.k-bs-panel` with a title bar `.k-bs-title` (mono, letter-spaced, dashed divider).
- **Memory** panel:
  - Character tabs, tier filters ("all 41, sharp 23, hazy 12, forgotten 6").
  - Row columns (`.k-bs-row`): tier | memory text + story time (+ struck-through "was sharp: …") | how learned (witnessed, told by X, overheard, rumor, inferred) + "doubted" + recall score | importance meter `.k-importance` (10 bars) | Pin, Hide.
  - Footer: "Pinned facts sit in every prompt".
  - **Write a memory** form: text, importance 1–10, who knows (a character or "Everyone knows it"), "Keep it in every prompt", Save.
- **Prompt:** "~7,300 / 16,384 tokens", counted tokens, cache reuse.
  - A stacked bar `.k-tokenbar` of the prompt parts, with a legend showing each part against its limit.
  - Recalled memories with scores, what was cut, and "full prompt".
- **Cast:** one row per entity (avatar or icon, name, kind, current state such as "location: The Gull").
  - A gold "found" badge for things the reader discovered.
  - "These two are the same" merges duplicates.
- **Reading:** memory reader runs (#, status dot, trigger, attempts, filed and skipped counts, a "stale" badge, errors).
  - Buttons: "Read what is waiting now", "Read again carefully".

---

## 5. Behaviour rules for memory signals

### 5.1 Receipt states (per character, per line)

| State | Look | When |
|---|---|---|
| **heard** | avatar at 85%, thin white ring, plus three pending dots | **Instant.** The character was present when the line was said. |
| **sharp** (lit) | amber ring with glow | **A few turns later**, when the memory reader has filed it and they remember it clearly. Crossfade 600 ms, like a read receipt arriving. |
| **hazy** | 42% opacity, 0.5 px blur, faint ring | Story time has passed and only the gist is left. Transition 1.2 s. |
| **forgotten** | avatar removed from the row | Faded out entirely. Backstage still lists it. |
| **absent** | empty dashed circle with the initial, plus "Tobin wasn't there" | **Instant.** The character was not in the scene and heard nothing. |

The persona you play never gets a receipt; receipts are about the AI characters.

### 5.2 Callout wording

- Memory: "Mira will remember this".
- Feelings: "Tobin didn't like that", "Mira trusts you a little more", "Tobin is suspicious of you".
- Beliefs, when you tell them something, chosen by their clarity about the related memory:
  - sharp → "Mira knows that's not true"
  - hazy → "Mira has her doubts"
  - no memory → "Mira believed you"

Callouts attach to the line they are about and also appear in Activity.

### 5.3 Time skip sequence

1. The stage blurs and the clouds drift in.
2. A title card shows "Six years later" (Newsreader italic 76), with the old clock struck through → the new clock.
3. A summary pill reads "12 of Mira's memories are going hazy", with an Undo button.
4. The clock rolls forward and the place re-lights (dusk → night: cooler, darker, moon in the window).
5. Receipts across the whole conversation animate to their new states, so you watch characters forget.
6. A title card "Six years later · Year 7" (with Undo) stays in the flow.

### 5.4 Arrivals and departures

Only people on stage hear. Someone you bring in steps in (600 ms), gets a name card and a system note. Someone who leaves steps off and gets a system note.

When the story text itself says someone arrived or left, the stage follows once the memory reader notices, with Undo.

---

## 6. Content style

- Story clock everywhere a timestamp would go: "Day 1, 19:02", "Year 7, Day 1, 19:22".
- Friendly, specific greetings in the Sky ("Good evening, Aren").
- Write each signal as a sentence about a person: "Mira will remember that you hid the ledger." Avoid system phrasing like "Memory event created".
- In Models and Backstage, use the real names: server names, model ids, hosts, token counts.
- Keep the copy from the current app where the reference in the brief quotes it, such as "No one: I direct the story", "away: hears nothing said here" and "Pinned facts sit in every prompt".

## 7. Not designed yet (leave room)

These still need design:

- Places & Plots (the sky-islands map)
- the dive storyboard
- reading mode
- empty states (no friends, a story not started, model server unreachable)
- phone layouts
- Books → Stories → Chapters
- import and export
