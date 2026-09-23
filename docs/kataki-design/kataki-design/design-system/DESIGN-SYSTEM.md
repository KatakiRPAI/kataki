# Kataki RPAI design system

Kataki is a local-first desktop app (Electron, Windows first) for AI role-play with characters who remember. This document is the contract between the design and the code. Values live in `tokens.json` / `tokens.css`, component styles in `components.css`, and a live gallery in `components.html`.

---

## 1. Principles

1. **Two worlds, one crossing.** Outside a story you are in the **Sky**: bright, social, playful. Inside a story you are in the **Scene**: warm, dim, cinematic. The **dive** through the clouds is the only way between them, and it should feel like a signature.
2. **The role-play comes first.** Memory, hearing and the engine are what make Kataki different, but they stay quiet. The chat shows how characters *feel* ("Tobin didn't like that", "Mira trusts you a little more") and, now and then, what they *remember* ("Mira remembered, vaguely…"). Who heard what, who answers next and token counts live behind the Advanced toggle and in Backstage.
3. **The chat is the screen.** Inside a story the conversation runs the full height of the window, in the middle. Everything else is a widget around it, and the user decides which widgets they want and where.
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
- reaction colours: **rose `#f4a595`** feelings and distrust, **sage `#a9dcb8`** warmth and trust, **sky `#9cc8ff`** mood and thinking, **lilac `#cbb8ff`** beliefs, amber for the rare memory signal
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
- **Scene:** crossfades, slow parallax (2–6 px), light flicker done with opacity. An unpinned widget that appears because something happened slides in 16 px with a light bounce, so you notice it.
- **Reduced motion:** the place and portraits become still images with crossfades, with no parallax, bounce or breathing orb; widgets appear without sliding. Every duration token collapses to 0 (see `tokens.css`).

**The dive, going in:** the clouds (two copies of `clouds.svg`, one mirrored) scale up by 1.2 and part left and right. The sky gradient fades to the place, then the chat column rises 24 px into place and fades in, with the corners and widgets last.

**The dive, coming out:** the reverse, floating up. The thread saves a still of the last moment as its cover in Chats and on the Continue card.

---

## 3. Layout

**Sky (1440×900)**
- nav rail: glass, 92 px wide, at left 20 / top 20 / bottom 20, radius 32
- content: starts at x 144, 24 px right margin
- headers: greeting or title on the left; search, bell and main action on the right

**Scene (1440×900): full-height chat with widgets either side**

- **Place layer:** the place image fills the window, blurred 3 px and dimmed to about 55%, with a warm tint (cool at night) and a vignette. It crossfades when the story moves to another place, or when the story clock crosses dawn / day / dusk / night.
- **Chat column:** centred, 800 wide, from 16 px below the top to 16 px above the bottom (the full height). Dark glass at 80% with a 20 px blur, radius 30. The text measure inside is capped at 680. The composer is docked inside the bottom of the column.
- **Corners:** top left is the cloud button (back to the Sky), the story title and "as Aren". Top right is the Backstage switch and the ⋯ story menu.
- **Widget columns:** 272 wide, 24 px from each edge. By default, character widgets stack on the right from y 84; the story clock and music sit at the bottom left. The top left stays clear so the place shows through.
- Widgets are the user's: in **Edit widgets** mode they can be dragged anywhere on the screen, including over the chat, as well as pinned, removed and added.
- **Reading mode:** hides widgets and corners and leaves only the chat.

**Backstage:** the same window. **Mind** on the left (about 864 wide), with Prompt, Cast and Engine stacked on the right (about 512 wide).

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
  - Contents: logo (cloud tile + "Kataki"); Home, **Characters**, Chats, **Places & Plots**, Activity, You; a spacer; Settings; the orb with "Dive in".
  - "Places & Plots" wraps to two lines, so the item is 76×68. The tab holds both, and the name says so.
  - Active item: white pill, accent colour, `aria-current="page"`.
- **Avatar** `.k-avatar` (`--s`, `--bg`)
  - A circular crop of the portrait art on the character's backdrop gradient.
  - `.k-avatar--ring` for your own avatar, which opens the persona switcher.
  - `.k-avatar-stack` for group threads.
- **Portrait + name plate** `.k-portrait`, `.k-nameplate`
  - Art anchored to the bottom, a soft light bloom top-left, and a strong-glass plate at the bottom.
- **Character card** `.k-friend-card`, 196×268
  - Contents: portrait, favourite heart (top right), name, one-line tagline (2 lines max), and **when you last played with them in real time** ("Played 2 hours ago", "Never played"). Hovering shows the exact date and place ("Today, 7:12 pm · at The Gull").
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
  - Contents: stacked avatars, title, pin, **the real time since you last played** ("2 h ago", hover for the exact date), last line (one line, ellipsis), then "as Aren · six years after the storm" in accent, and a gold memory-event badge with a spark.
  - The selected row is solid white.
- **Persona switcher** (dialog anchored to your avatar)
  - One row per persona (avatar, name, tagline, a check when selected), then "Director · Play no one", then "+ New persona".
  - A footnote: "Each chat keeps the persona it started with."
**Places and Plots** (the library)

- One tab holds both, because they belong together: a place is where a story happens, a plot is what it starts from.
- **Everything is filed under a book or a story.** A book holds stories; places and plots link to a book, to one or more stories, and to the characters who know them. Anything unlinked lands in "Not in a book" and shows a Link action.
- **Filter panel** (left, 280 wide): "Everything", then BOOKS as a tree (book → its stories, each with a count), "Not in a book", then CHARACTERS as face chips. Picking any of them filters the grid; the header says what is being shown ("Showing Mira's places and plots").
- **Tabs:** All · Places · Plots. **Sort:** Recently used, A–Z, Most used.
- **Grid**, grouped by book, each group with a heading (book name, "2 stories · 4 places · 2 plots").
- **Place card:** the image, the name, a four-part strip previewing dawn / day / dusk / night, the description, link chips (book, stories) and the faces of characters who know it, then "Start a scene here" and Edit.
- **Plot card:** a violet header with the name, the premise in story type, the opening narration, the same link chips and faces, then "Start this plot" and Edit.
- **Link dialog** (from a card's ⋯): Book (select), Stories (checkboxes), Characters who know it (face chips + Add), Cancel / Link.

- **Server card** (Models)
  - Contents: candy tile, name, host in mono, status badges ("connected", "qwen3.5-9b loaded", "key stored"), Test and Remove.
- **Job card** (Models)
  - Collapsed: icon, job name, model or "Same as Characters", a detail line.
  - Expanded (Characters shown): Server, Model, Context size, Thinking (As the model likes / On / Off), Kind (Detect automatically / Standard / Reasoning + "Detect now"), Sampler preset, and a JSON box.

### 4.2 Scene

**Chat**

- **Chat column** `.k-chat`: full height, 800 wide. Lines stack from the bottom, and the top edge fades out.
- **Line** `.k-line` (`--speaker` colour)
  - Anatomy: speaker name, story time (12-hour), an optional spark, optional marks ("edited", "stopped"), the prose, then any reactions.
  - **Story time** is 12-hour (`7:02 pm`). Hovering it shows a tooltip with the 24-hour time and the full story date: "19:02 · Day 1 · the night of the storm". See §6.
  - **Hover or focus** shows the tools pill: `‹ 2/3 ›` takes (the last arrow rolls a new take), Edit, Hide.
  - **Hidden line** `.is-hidden`: dimmed with a dotted strike. It stays in the story but never reaches the AI.
- **Editing a line:** the line turns into an editor in place, with three actions.
  - **Save edit** changes only what the model reads from now on; the story after it stays as written.
  - **Save and regenerate from here** rewrites everything after the line. The old continuation is kept as the previous take.
  - **Cancel.**
  - When more than 2 messages come after the line, a warning sits above the buttons: "Regenerating from here rewrites the 5 messages after this one. They'll be kept as the previous take, so you can flip back." The lines that would be rewritten dim while the editor is open.
- **Reactions** `.k-react`, one or more per line, wrapping. Each is a small pill: the character's face, an icon, and a sentence about them.
  - **Feelings** (rose): "Tobin didn't like that", "Tobin is suspicious of you", "Mira is wary of Tobin".
  - **Warmth** (sage): "Mira trusts you a little more", "Mira is glad to see you".
  - **Mood** (sky blue): "Mira is worried for you".
  - **Belief** (lilac): "Mira has her doubts", "Mira knows that's not true", "Mira believed you".
  - **Memory** (amber): "Mira will remember this". Use it only for moments that matter, at most once every few lines.
  - Feelings should outnumber memory signals by a wide margin.
- **Recall box** `.k-recall`: the one place memory speaks up in the chat. It appears under a reply that leaned on a memory: "MIRA REMEMBERED, VAGUELY · The ledger is somewhere behind the bar." plus one line of context ("Six years ago she knew exactly where."). Use it when the recall changes the scene, not on every reply.
- **Title card** `.k-titlecard`: "The Gull · the night of the storm", and "Six years later" (with Undo) after a skip.
- **Story note** `.k-note`: arrivals and departures in plain story language. "Tobin joins." "Tobin went to the bar." There is no "he won't hear" text in Simple mode.
- **A reply arriving:** the stamp reads "writing…", and text streams with an amber block caret. A collapsed "Thought for 4 s" chip opens the notes in Backstage. The speaker's character widget shows "thinking…" while a reasoning model works.

**Composer** `.k-composer`, docked inside the chat column

- **Simple (default):**
  - The text area (Newsreader 18). Placeholder "Speak or act as Aren…", or "Direct the story…" when you play no one.
  - Bottom left: the **Simple · Advanced** toggle and a Continue button (the story goes on without a line from you).
  - Bottom right: the **mode chip** and **Send**. Send becomes **Stop** while a reply streams, and stopping keeps what was written.
- **Mode chip** `.k-mode`: works like a model picker in an AI chat.
  - The default is **Auto**. Auto reads the line's formatting: `*like this*` is an action, plain text or “quotes” is speech, `(like this)` is a thought no one hears, `@Mira …` is a whisper to Mira, and `>> …` is narration.
  - While you type, the chip shows what Auto detected: "Auto · Do + Say".
  - Clicking it opens a menu with Auto, Say, Do, Whisper, Think and Narrate, each with its syntax on the right. Picking one overrides Auto for this line only.
- **Advanced** adds, above the text area:
  - who will hear the line ("Only Mira will hear this", with away characters greyed)
  - who answers next (Whoever fits, one chip per character, Narrator)
  - Pass time
  - the token count, and a token meter along the top edge

  The toggle is remembered per user.

**Widgets** `.k-widget`: glass cards, radius 24, independent of each other. Any number of any type, including several of the same type.

- **Character widget** (one character each)
  - Anatomy: portrait art in their current expression, name, expression chip (colour by feeling), and one line of how they are right now ("Worried someone overheard"), plus a pin button.
  - The art crossfades when the expression changes.
  - A compact row variant is used for away characters: face, name, "At the bar · away".
  - Clicking it opens the character card.
- **Story clock widget**
  - The story time, big and 12-hour ("7:22 pm"); hovering it shows 24-hour and the full date.
  - The story-relative date under it ("Six years after the storm").
  - A sun/moon arc, the place, and **Pass time**.
- **Music widget**
  - Play/pause, the track name with a small level meter, where it comes from ("Matched to the scene", "Your upload"), and mute.
  - Clicking the track opens the **music picker**:
    - a "Match the scene" toggle
    - suggested ambience and music
    - the user's uploads
    - **Upload a track…** (mp3, ogg, wav)
    - volume
- **Place widget:** the scene image in full colour, with the place name.
- **Cast widget:** everyone in the scene as faces.
- **Notes widget:** the user's own notes for this story.
- **Pinned vs unpinned:** a pinned widget always shows. An unpinned widget stays tucked away and appears when something happens to it (a character's expression or feeling changes, the clock jumps, the track changes). It fades back after about six seconds unless hovered.

**Edit widgets** (⋯ menu → Edit widgets)

- The place dims under a dot grid. A bar at the top reads "Editing widgets · Drag anywhere…" with **Reset layout** and **Done**.
- Every widget gets a dashed amber outline, a drag handle (top left, outside the card) and two buttons (top right): **Pin** (filled amber when pinned) and **Remove** (red).
- Widgets drag freely anywhere on the screen. Where a widget came from, a dashed empty slot shows while you drag.
- **Add widget** (top left) opens a list: Character, Story clock, Music, Place, Cast, Notes. Character asks which character. The same type can be added any number of times.
- Layouts are saved per story, with a default for new stories.

**Story menu** (⋯): Edit widgets, Reading mode, Scene and place, Story settings, Export story, then Delete story in red.

**Character card** `.k-peek`: opens from a character widget, over a dimmed screen.

- Header: portrait, name, expression, role, and **Add as widget**.
- Right now: Holding, Wearing, Where.
- How she feels about you: warmth, trust and doubt bars.
- On her mind: one line.
- Relationship chips; the Secret (blurred, Reveal).
- Actions: Let her answer next, Send away, Edit.

**Time skip** `.k-timeskip`: see §5.3.

### 4.3 Backstage

The same scene from behind. It shows how a character's mind produced the last reply, not only what they remember. Mono type, blueprint lines.

- **Panel** `.k-bs-panel` with a title bar `.k-bs-title` (mono, letter-spaced, dashed divider).
- **Mind** (the main panel): the last reply, traced through the character's mind as a small network. Tabs switch between the characters and the Narrator.
  - **IN:** what reached them this turn: heard ("Aren: 'buried it by the lighthouse'"), saw, place, time.
  - **SENSE:** perception ("A claim that clashes with what she knows") and attention.
  - **INSIDE:** the modules that shaped the reply: Recall, Feeling, Belief, Goals, Persona. Memory is one node among several.
  - **DECIDE:** intent ("Question it, gently") and expression ("doubtful").
  - Each node shows its activation (0–1) as a number and a thin bar. Edges are curves whose width is their weight. **The winning path is drawn in gold**, the rest in blueprint blue.
  - Under the graph: **Spoke** (the line that came out, with its time and token count), and **How she feels about Aren, across the story** (warmth, trust and doubt lines, with story events such as "six years later" marked).
  - Footer: "Memory · 41" (opens the full memory list), and "Replay this turn".
  - Clicking a node shows what went into it and what came out.
- **Prompt:** "~7,300 / 16,384 tokens", cache reuse, a stacked bar `.k-tokenbar` of the prompt parts (rules, cards, mind, examples, history, tail) with each part against its limit, what was cut, and "full prompt".
- **Cast:** one row per entity (face or icon, name, kind, current state such as "here · doubtful · mug in hand"), with a gold "found" badge for things the reader discovered, and "These two are the same" to merge duplicates.
- **Engine · this turn:** one row per job (Characters, Reasoning, Recall, Feelings, Memory reader, Narrator) with the model, time, tokens and status ("waiting · 2 new lines"), plus "Read what is waiting now" and Logs.
- **Memory list** (from "Memory · 41"): tier, how it was learned, importance, recall score, pin, hide, and Write a memory. It is kept, but one click deeper than before.

## 5. Behaviour rules for memory and feelings

### 5.1 Who heard what (Advanced only)

Hearing is still tracked for every line, but the chat doesn't show it by default. With the composer on **Advanced**, hovering a line shows small chips: "Mira heard it", "Tobin wasn't there". The composer shows who will hear the next line. Everywhere else, hearing only surfaces through its consequences: a reaction, a recall box, a belief.

The underlying states, used in Advanced and in Backstage:

| State | Meaning |
|---|---|
| heard | present when it was said; not yet filed by the memory reader |
| sharp | filed, remembered clearly |
| hazy | only the gist remains |
| forgotten | gone |
| absent | wasn't there, heard nothing |

### 5.2 Reaction wording

- Memory: "Mira will remember this".
- Feelings: "Tobin didn't like that", "Mira trusts you a little more", "Tobin is suspicious of you".
- Beliefs, when you tell them something, chosen by their clarity about the related memory:
  - sharp → "Mira knows that's not true"
  - hazy → "Mira has her doubts"
  - no memory → "Mira believed you"

Callouts attach to the line they are about and also appear in Activity.

### 5.3 Time skip sequence

1. The place blurs further, and a pale overlay (82%) with drifting clouds covers the whole screen, chat and widgets included.
2. A solid white card (no transparency, so no text can show through) holds:
   - "THE THIRD FLOORBOARD"
   - "Six years later" (Newsreader italic 68, ink `#1f1a2b`)
   - the old story date → the new one ("The night of the storm → Six years after the storm")
   - a single line about memory ("Mira's memories of that night are growing hazy.")
   - Undo (dark button, white text)
3. The clock widget rolls forward, and the place crossfades to its new light (dusk → night: cooler, darker, moon in the window).
4. A title card "Six years later" (with Undo) stays in the chat.

All text in the sequence is dark on white, at a contrast of at least 7:1.

### 5.4 Arrivals and departures

Only people on stage hear. Someone you bring in gets a story note ("Tobin joins.") and a character widget that appears with a "Joined" badge. If you don't pin it, it tucks away again. Someone who leaves gets a story note ("Tobin went to the bar."), and their widget turns into the compact grey row.

When the story text itself says someone arrived or left, the stage follows once the memory reader notices, with Undo.

---

## 6. Content style

**Two clocks**

Kataki has two: the real one (when you played) and the story one (when it happened). Use the real clock wherever the user is looking at their own history, and the story clock inside a story.

| Where | Shows | On hover |
|---|---|---|
| Character card, profile, "Last played" | real time since you played ("Played 2 hours ago") | the exact date and place ("Today, 7:12 pm · at The Gull") |
| Chats list | real time ("2 h ago"); the story date sits under it, with the persona | the exact date |
| Activity | real time ("2 hours ago"); the story date in the item's second line | — |
| Inside a story: line stamps, the clock widget, title cards | story time (12-hour) and the story-relative date | 24-hour time and the full story date |

**Story dates**
- Times are 12-hour everywhere in the chat and widgets ("7:02 pm"). Hovering shows the 24-hour time and the full date ("19:02 · Day 1 · the night of the storm").
- A bare "Day 1, 19:00" tells the reader nothing, so it is the last resort, never the first choice. The date follows the story, in this order:
  1. If the story, book or setting has a calendar, use it ("14 Frostmoon, 1203").
  2. If it has a defining event, date relative to it: "The night of the storm", "5 days after the proposal", "Six years after the storm". Relative dates update as time passes.
  3. Only if neither exists, use "Day 1", "Day 2"… ("Year 7, Day 1" after the first year).
- The count (Day / Year) is always available on hover, so continuity is never lost.
- Outside a story, prefer the real clock: "Played 2 hours ago", "Played yesterday", "Never played".

**Voice**
- Friendly, specific greetings in the Sky ("Good evening, Aren").
- Write each signal as a sentence about a person: "Tobin is suspicious of you." Avoid system phrasing like "Memory event created".
- Prefer feelings over mechanics in the chat. Keep "will remember" for the moments that matter.
- In Models and Backstage, use the real names: server names, model ids, hosts, token counts.

## 7. Not designed yet (leave room)

These still need design:

- Places & Plots (the sky-islands map)
- the dive storyboard
- reading mode
- empty states (no friends, a story not started, model server unreachable)
- phone layouts
- Books → Stories → Chapters
- import and export
