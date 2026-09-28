# Screens

Every route and every state of it. Overlays are summarised where they open and specified in `OVERLAYS-AND-MENUS.md`. The story screen has its own file, `SCENE.md`.

**Exact copy lives on the boards** and, extracted, in `strings.boards.en.json`. This file quotes copy only where behaviour depends on it. Anything in `{braces}` is data.

## Conventions that apply to every Sky page

- **Frame**: `.app` = Rail + `.app__main` (padding 24 40 56, gap 32). The Sky component sits behind the main column from inline-start 200. Page title: `.pg-title` (Baloo 2, 32/36, 800). Section title: `.sec-title` (24/28, 700).
- **Top bar** (`TopBar`): persona switch at inline-start, search field (Ctrl K) at inline-end. On Settings and first-run pages it is as drawn on the board.
- **Loading**: the library is local, so pages render from a synchronous-feeling IPC read. If a read takes more than 150 ms, show `Skeleton` blocks shaped like the content; never a page spinner. Anything that takes longer by nature (download, export, backup, test a connection) shows its own progress on its own board.
- **Scrolling**: `.app__main` scrolls; the Rail and the Sky don’t. Scroll position is kept per route for the session.
- **Dates**: relative in lists (“2 hours ago”, “last week”), exact on hover (Stamp/Tooltip: `24 May 2026, 7:22 pm`). Story time is always relative to the story (“three weeks later”) and never mixed with real time in the same phrase.
- **Counts**: ICU plurals from the strings file. Zero counts hide the label rather than say “0 …”, except where a board shows 0.
- **Right-click** on any card, row or line opens the same menu as its ··· button (`OVERLAYS-AND-MENUS.md` › Menus). Shift F10 opens it for the focused item.
- **Drag and drop** of files onto a page: image → PortraitPicker flow on character pages; `.png/.json/.kataki` → ImportCards (D4) anywhere in the Sky.
- **The model can be gone** on any page. Sky pages never block on it. Home shows C3’s status line; everything else stays usable.

---

## A · Opening

### `/opening` — A1 Opening, A2 OpeningFailed

**Purpose**: the only thing on screen while the library opens. No rail.

**Layout**: centred 760 column, 150 from the top: wordmark, a line of copy (“Waking six people up.” — the count is `characters.count` in words up to twelve, else digits), `StepList` with three steps, then the privacy line.

**Steps and their data**

| Step | Doing text | Done text | Failed |
|---|---|---|---|
| Library read | Reading… | `{lines} lines, {characters} characters, {stories} stories` | A2 |
| Memories rebuilt | `{done} of {total}` | same, final | never blocks: rebuild continues after Home opens |
| Model reached | `{server} · {model}` | same | never blocks: Home shows C3 |

**A2 (library unreadable)**: the failed step reads “library.db would not open”; later steps say “waiting for the library”. `Alert` “Kataki can’t read your library.” with code `LIBRARY_UNREADABLE` and four actions: **Restore yesterday’s backup** (primary, only when a backup exists; label uses the backup’s relative date), **Open the folder**, **Try again**, **Start with an empty library** (ghost). The two callouts below explain restore and start fresh. `LIBRARY_NEWER` and `LIBRARY_MIGRATION_FAILED` use this same layout with their own copy from `errors.json`.

- Restore → copy the backup beside the damaged file as `library.restored-{date}` and open that. The damaged file is moved into `library/damaged/` with a timestamp, never deleted.
- Start with an empty library → confirm dialog (“Start with an empty library? Your old library stays in its folder.” · Cancel · Start empty) → `/welcome`.

### A3 CrashRecovered (overlay on `/home`)

Opens on the first launch after an unclean exit (the main process writes a `running` flag and clears it on clean quit). Dialog over Home:

- Title “Kataki closed unexpectedly”. Body from the `crash.body` template (`DATA.md`): “Last time, Kataki stopped at {time} while {name} was answering. Everything up to {his} last finished line is safe. The line {he} was writing is gone.”
- Three `KeyValue` rows: Last story · Lost · Checked.
- Checkbox “Ask me before reopening the last scene next time” (sets `general.askAfterCrash`).
- Note: “Kataki goes to Home first after a crash either way.” and “Crash log saved · KT-CRASH-{nnnn}”.
- Actions: **Report it** (opens BugReport L2 with the crash log attached), **Stay here**, **Continue the story** (primary → `/story/{id}`).

---

## B · First run

All first-run pages: no rail; 1160 column centred, 72 from the top; wordmark at inline-start, “Step {n} of 2” at inline-end. Esc does nothing on the first page (there is nowhere to go back to).

### `/welcome` — B1 FirstRun

Three `DoorCard`s side by side, then the six-portrait `AvatarStack` line, then “All of this lives in Settings afterwards.” and **Skip for now**.

| Door | Tag | Shown when | Primary | Secondary |
|---|---|---|---|---|
| Start now | Recommended | always | **Start now** → `/welcome/download` | — |
| Use a model server | Found on this computer (only when the probe found one) | always; copy switches between “Found {server} running, with {model} loaded…” and the not-found line | **Use this** (found) → saves the connection → `/welcome/who`; when nothing is found the primary is “Add one” → `/welcome/server` | **Look again** re-probes in place (no navigation) |
| Use an online model | Sends your story elsewhere | always | **Add a key** → `/welcome/online` | — |

**Skip for now** → `/welcome/who` with no model chosen (Home and the Scene then show SERVER_UNREACHABLE’s banner variant until one is added). The probe runs on page load (ports 8080, 11434, 1234, 5000, 5001 on localhost, 1.5 s timeout each, in parallel).

HARDWARE_TOO_SMALL shows as a warm callout inside the Start now door when free RAM is under the model’s requirement.

### `/welcome/download` — B2 FirstRunDownload

Left: the download card. Right: “If it stops” — the three error callouts and the Ready callout, shown one at a time in place in the real app (the board shows all four so they can be built).

- `ProgressBar` label “Downloading”, value text `{done} of {total} GB · about {eta} left`. ETA appears after 3 s of samples; before that the value text is just the sizes.
- `StepList`: Room on this computer → Downloading → Checked → Said hello. Each step’s detail is on the board.
- **Pause** / **Resume** toggles; **Cancel** asks “Stop downloading? What’s downloaded so far is kept for next time.” (Keep downloading · Stop). The primary **Meanwhile, pick who you’ll meet** → `/welcome/who` without stopping the download.
- On failure, the matching callout replaces the step list: DOWNLOAD_NETWORK (Resume), DOWNLOAD_DISK (Choose a folder → folder picker; updates `models.folder`), DOWNLOAD_CHECKSUM (Download again).
- On success: the Ready callout, then the page moves on to `/welcome/who` by itself after 1.5 s unless the user already left.

### `/welcome/server` — B3 FirstRunServer

Form: **Address** (URL; defaults to the first common port not in use), **Kind of server** (`Select`: Automatic, llama.cpp, Ollama, LM Studio, KoboldCpp, text-generation-webui, Other, OpenAI-compatible), **Key** (optional, password field, “Kept in this computer’s keychain.”).

**Test** runs: GET `/v1/models` → pick the loaded model → a 1-token completion → time it. The result appears in place as one `StatusLine`; the board shows all six outcomes: “Testing {address}”, “Connected”, “Connected, but no model loaded” (SERVER_NO_MODEL), “Nothing answered” (SERVER_UNREACHABLE; also as the Address field error), “It answered, but not like a model server” (SERVER_NOT_COMPATIBLE), “It wants a key” (SERVER_UNAUTHORIZED). Exact copy in `errors.json`. **Use this server** is disabled until Connected; then → `/welcome/who`.

### `/welcome/online` — B4 FirstRunOnline

`RadioGroup` of services: OpenRouter (“Hundreds of models behind one key.”), OpenAI, Anthropic, and “Something else that speaks the OpenAI API” (“You give it an address.”, reveals an Address field), **Key**, **Model** (`Select`, disabled with “Pick after the key works” until the key tests), the warm “Your story leaves this computer” callout, and the key-storage privacy line.

**Test and continue**: validates the key (GET models), fills the Model list, picks a default (the service’s recommended chat model, else the first), and continues to `/welcome/who`. Outcomes on the board: “Key works” (`{service} · {n} models · {model} picked · {price} a reply at this length`, the price only when the service reports one), “Key not valid” (API_KEY_INVALID; also as the Key field error), “No credit left on this key” (API_NO_CREDIT), “Too many requests” (API_RATE_LIMITED), “Couldn’t reach the service” (API_UNREACHABLE).

### `/welcome/who` — B5 FirstRunWho (interactive on the canvas)

Six `CharacterCard`s in a row. One is selected (Mike by default; the selection ring and a check). Dani carries the Draft badge (“Half-written, on purpose”). Below: “And you are” with the persona’s avatar and name and **Change** → B6.

- Primary: **Start with {name}** → creates a story: that character + the default persona, at the character’s first known place, no book, name `{place} · {weekday}` → `/story/:id` (SceneFirst P20).
- **Back** → the previous first-run page. **Skip and go to an empty library** → `/home` (C2).
- Arrow keys move the selection; Enter starts.

### B6 FirstRunPersona (overlay on `/welcome/who`)

Dialog “Who are you in these stories?” Fields: picture (Choose a picture · Remove; “Optional. Without one, characters still know your name.”), **Name** (required, prefilled “Liv Sandoval”), **Who you are, in a line or two**, checkbox “Or just be “You” for now” (disables the fields; characters call you “you”). Save writes the default persona. Cancel keeps the existing one.

---

## C · Home, palette, search

### `/home` — C1 Home, C2 HomeEmpty, C3 HomeOffline

**C1 sections, top to bottom**

1. **Skip to the story** link (visually hidden until focused) → Continue.
2. `TopBar`.
3. `ContinueHero` for the most recently played story: title, book, last stored line (Newsreader), the other character’s avatar + `mood` pill + `{memories} memories · {changed} changed since you left`, story-time line `{relative} · {place} · {time}`, the place still with its caption. Buttons: **Continue** (primary) and **New story**.
4. **Since you last played** — `Eyebrow` + `{n} events · {last_played:relative}`, then up to three `EventCard`s: newest events since `story.lastPlayedAt` across all stories, one per (character, type). Hidden when there are none.
5. **Your characters** — filter chips All / In a story / Drafts with counts; cards in a row: the character from the hero first as `featured`, then by last played; then the `AddCard` (“New character · or import a card”). Maximum one row; the rest are in Characters.
6. **Other threads** — up to three `StoryCard`s (the next most recent stories) + **All stories**.
7. Privacy line with **Where is my data?** → `/settings/data`.

**C2 HomeEmpty** (no story ever played): hero replaced by “Day one · Nobody knows you yet.”, then **Start with someone**: the five shipped characters who are ready to play (drafts like Dani are left out), each card with its own **Say hello** that creates the story and opens it (→ P20), then “Or start from nothing” with three `DoorCard`s: Write a character, Import your cards, Make a place first; then the “One thing worth knowing” callout. Rail and top bar unchanged.

**C3 HomeOffline**: C1 plus a bad `StatusLine` under the top bar — SERVER_UNREACHABLE’s banner variant: “Nobody is answering” · `{server} at {address} stopped answering {ago}. You can read, edit and export everything; new replies wait until it is back.` · action **What happened** → `/status/model` (N1). It disappears by itself when the connection answers.

**Interactions**

| Element | Does |
|---|---|
| Continue | `/story/:id` of the hero story, scrolled to the end |
| New story | `/stories/new` with the hero’s cast preselected |
| EventCard | `/characters/:id` of that character, Memories open at that memory |
| Character card | `/characters/:id`; hover shows Continue (their last story) and ··· (CharacterMenu) |
| Filter chips | filter the row in place; not persisted |
| Story card | `/story/:id`; ··· = StoryMenu |

### C4 PersonaMenu (overlay)

`Menu` titled “Playing as”, from the persona switch (Ctrl P). Items: each persona (avatar, name; meta “default” on the default), checked = the current one; “Director · play no one”; divider; New persona (→ `/you` with EditPersona open, empty); Manage personas (→ `/you`). Footer: “Switching changes who you are in new lines. Stories you already started keep their persona.” So choosing here sets the default for **new** stories only; a started story changes persona in Story settings (P18), which shows `toast.persona.switched`.

### C5–C7 Command palette (overlay, any Sky route)

`CommandPalette`, top-centred, 640 wide, opened by Ctrl K or clicking the top-bar search field. (`/` focuses a page’s own search field where it has one — Stories, Search, Memories, Shortcuts — and opens the palette where it doesn’t.)

- **C6 nothing typed**: three groups. **Recent** (last 3 things opened: story, character, place, with a type meta). **Do**: New story (Ctrl N), New character, Switch persona (Ctrl P), Import cards, Settings (Ctrl ,), Give feedback. **Go to**: Home (G then H), Stories (G then S), Characters (G then C).
- **C5 typing**: groups in order **Jump to** (stories, characters, places, plots, books whose name matches; meta `{type} · {book or “not filed yet”}`), **Lines** (stored lines matching, avatar + quote, meta `{speaker} · {story} · {story time}`), **Do** (contextual actions built from the top match: “New story with {name}”, “Switch persona to {name}”, “Export {story}”, and always last “See all {n} results for “{q}”” with Ctrl Enter). Max 3 per group in Jump to and Lines. Enter opens the highlighted item; Ctrl Enter → `/search?q=`.
- **C7 no matches**: “Nothing called “{q}””, a “Did you mean “{suggestion}”?” row when an edit-distance-1 name exists, “Search lines and memories for “{q}”” (→ `/search`), and Make it: “New character called “{q}””, “New place called “{q}””.
- ↑ ↓ move, Enter opens, Tab moves between groups, Esc closes and returns focus.
- Search is local full-text (see `SEARCH_INDEXING` in `ERRORS.md` while the index builds).

### `/search?q=` — C8 Search, C9 SearchNone

Large `SearchField` with the query and the line “{n} results across everything · names, lines, memories, places and plots”; `Tabs`: All / Lines / Stories / Characters / Places and plots / Memories, with counts. Sort `Select`: Best match, Newest first, Oldest first. Results are `SearchResult` rows with the match highlighted, grouped under the tab; `ShowMore` (“{n} more”) per group on All.

- Line result → `/story/:id` scrolled to that line, line flashed (focus ring for 1.2 s).
- Memory result → `/characters/:id` with Memories open, filtered to it.
- **C9**: `EmptyState` “Nothing called “{q}”” + the explanatory line + “Did you mean” chips + “New character called “{q}”” + **Clear search**.

---

## D · Characters

### `/characters` — D1 grid, D2 list, D3 empty filter

**Header**: `.pg-head` with “Characters” and the computed sub-line `{characters} characters · {drafts} draft · {groups} group` (ICU plurals, zero parts dropped). Actions: **Import cards** (secondary → D4), **New character** (primary → `/characters/new`).

**Toolbar**: filter chips All / In a story / Favourites / Drafts / Also a persona with counts (`Chip`, one at a time; below 1280 wide they collapse into FilterMenu); **Show as** `Segmented` Grid / List (persisted in `ui.charactersView`); **Sort by** `Select` (Recently played, Recently written, Favourites first, Name, A to Z, Most stories). The section heading above the cards reads “Everyone” (or the filter’s name).

**D1 Grid**: `CharacterCard`s, 168 wide, wrapping, the most recently played `featured` (324). Badges: In a story (warm), Also a persona, Draft. `when` = `Played {relative}` or “Never played”. Last item: `AddCard`.
**D2 List**: `ListRow`s: avatar 40, name (Newsreader), tagline, meta `Played {relative} · {n} stories`, a `StatePill` for mood / Draft / Also a persona, ··· button.
**Groups** section below both: “Groups · sets of characters you start a scene with”, group rows (`AvatarStack` + name + `{names} · {n} stories`) with **New story** and ··· (GroupMenu) per group, and **New group** (→ D5).
**D3**: when the active filter has nobody: `EmptyState` “No favourites yet · Star someone from their ··· menu or their profile and they show up here.” + “Show everyone”.

Card hover (and focus): Continue (their last story) and ··· (CharacterMenu). Enter opens the profile.

### D4 ImportCards (overlay, `dlg--lg`)

Drop zone (“Drop cards here · Several at once, or a whole folder. Nothing is added until you press Import.”), **Choose files**, **Choose a folder**. After choosing: a summary line `{found} found in {folder}` and `{ready} ready · {dupes} already here · {bad} can’t be read`, then one row per file: avatar or initial, name, `{file} · Card V{n} · {places} places, {plots} plot in its lorebook`, and a pill (Ready / Skipped). A duplicate row (“{file} · someone called {name} is already here”, IMPORT_DUPLICATE) has a `Select`: Keep both · Replace the one here · Skip this card. An unreadable one reads “No character card inside this picture. IMPORT_NO_CARD” with the Skipped pill. Card versions V1, V2 and V3 are read. Checkbox: “Bring their example conversations in as “How they talk””. Footer note: “Copied into your library. The files you chose aren’t changed or moved.” Actions: Cancel · **Import {n}** (disabled at 0).

Import runs in the main process; the dialog shows per-row progress; on finish it closes and shows `toast.import.done`.

### D5 NewGroup (overlay)

Fields: **Name**; **Who is in it** (chips of chosen people with remove, + Find); order hint “Two or more. Order is who speaks first when nobody is addressed.”; **Where they usually are** (`Select` of places + Nowhere in particular). Counter line `{n} people · {names}`. **Make the group** disabled under two people.

---

## E · A character’s profile

### `/characters/:id?tab=story|profile` — E1, E2

**Header** (both tabs): portrait still (focus-cropped), name (`StoryName` title), tagline, tags, `Played {relative}`, and actions **Continue** (primary; their most recent story) · **New story** · ☆ Favourite (`IconButton`, pressed state) · ··· (CharacterMenu). `Tabs`: Story · Profile.

**E1 Story tab** — the living state, all read from the engine’s rows:
- **Right now**: `mood` pill + `at {scene}, {relative}`.
- **How he feels about you**: three `Meter`s warmth / trust / doubt (0–100) with the current persona.
- **What he still holds onto** · `{shown} of {total}`: top three memories by importance as `MemoryRow`s (word = sharpness label, value = sharpness, meta = `{source} · {story} · {time}`), then **All {total} memories** (→ E3) and **Open Backstage**.
- **Who he knows**: `RelationshipCard`s (`relationship` enum → “wary of him”, “fond of her”, “never met”).
- **Moments together** and **Stories together**: story rows with dates and Continue.
- `StatRow`: `{stories} stories · {lines} lines · together since {date} · {places} places`.
- **How he talks** (sample lines as `Bubble`s) and his secret (`SecretCard`, “Private”) also sit on this tab, beside the living state.
- **Export everything about Mike** (link → ExportStory-style dialog scoped to the character).

**E2 Profile tab** — what the user wrote, read-only here, with **Edit profile** (→ `/characters/:id/edit`): About, How he says hi (a `Bubble`), How he talks · sample lines, `SecretCard` (“Private”), Details (`SettingsRow`s: Pronouns, Places he knows, Which model plays him, Memory, Made `{date} · edited {n} times`).

### E3 ProfileMemories (overlay, side sheet 560)

“Everything {name} remembers about you” · “{n} memories, sharpest first. Stored when they happened; nothing here is written now.” Search field (“Search {name}’s memories”), a **Story** `Select` (Every story, then each story), filter chips All / Sharp / Hazy / Doubted / Forgotten, and a scrolling list of `MemoryRow`s, each with ··· (MemoryMenu). MemoryMenu › Forget this… opens E4 with that memory selected.

### E4 ForgetMemory (overlay, `dlg--lg`)

“Make Mike forget something” · body “He won’t remember it happened. The lines stay in the story; he just can’t recall them. You can undo this for 30 days.” · a “Find a memory” search field and the memories with checkboxes (the one it was opened from is checked) · `RadioGroup` **Also**: Just these memories · Everything from the scene they came from (“{scene} · {n} memories”) · note “{n} memories · this can’t be seen by Mike, only by you” · Cancel · **Forget {n}** (danger). Forgotten memories get `forgottenAt`; a daily job purges them after 30 days. Toast with Undo.

### E5 DeleteCharacter (overlay, Dialog tone bad)

“Delete Mike?” · “His profile, portrait and {memories} memories go. The {stories} stories he is in stay, with his lines kept and his name greyed out.” · “Export him first if you might want him back.” · `RadioGroup` **The stories he’s in**: Keep them, with his lines (default) · Delete them too · confirm field “Type Mike to confirm” (CONFIRM_MISMATCH until it matches) · **Keep him** · Export first · **Delete Mike** (danger, disabled until it matches). After: `/characters`, toast with Undo (10 s; the delete is soft until the toast expires).

---

## F · Making and editing a character

### `/characters/new` — F1, F2, F3

Two columns: the form (inline-start) and a sticky preview card “As they will look” (inline-end, 320) that updates live: portrait or initial, name, greeting bubble, Draft pill until a secret exists.

Page title “New character”, sub “Two things are required. Everything else can wait, or never happen.”, and **Import a card** (→ D4) at the top.

**Required** (always open): Portrait drop zone (“Give them a face · Drop an image, pick one from Kataki’s set, or leave it. They get an initial until you decide.” · Choose a file · Pick from Kataki’s set → F4), **Name** (`TextField`, required, max 40, hint “What you call them. You can change it later.”), **How they say hi** (`TextArea story`, “Their first line in every new story. Actions go between *asterisks*.”), and **Stuck? Start from** `ChoiceChips` (Warm, Guarded, In a hurry, Mid-argument) which fill the greeting with a static example the user edits.

**Optional · add any of these whenever** — six collapsed rows that expand in place, each with a Written/Empty state and a counter “{n} of 6 written” (F2 shows every one open): **About them** (About them, Tags — up to three, Pronouns — she / her · he / him · they / them · Something else) · **How they talk** (two sample lines + Add a line) · **Their secret** · **Relationships** (Who · Feels `Select` of the `relationship` enum · remove · Add someone) · **Places they know** (chips + New place → I5) · **Which model plays them, and how they remember** (Model `Select` of connected models, “Only models that are connected now are listed.”; How fast their memories fade `Select` Like Settings · life-like · Fast · Life-like · Slow · Never; They can doubt you `Toggle`).

**Preview column** (inline-end): the live card, the greeting bubble, a readiness `Callout` — ok “They can start now” (“A name and a greeting is enough to play. {name} stays a draft until you give {her} a secret…”, or “Everything that matters is here. {name} is ready for a story.”), bad “Not yet” (“A name and a greeting is all it takes.”) — then **Create {name}** (primary, full width; “Create” when the name is empty), and below it Save as draft · Cancel, and “Saved to this computer · nothing is uploaded”.

**F3 errors** (Create with required fields missing): a bad `Callout` at the top “Two things are missing · A name and how they say hi. Everything else can stay empty.”; inline errors “Give them a name. It’s the one thing Kataki can’t guess.” (NAME_REQUIRED) and “Write how they say hi. It’s their first line in every new story.” (GREETING_REQUIRED); the readiness callout turns to “Not yet”; focus moves to the first invalid field. NAME_TAKEN is a warning only.

A character without a secret saves as a Draft; it can still play.

### F4 PortraitPicker (overlay, `dlg--xl`) · F5 PortraitFocus (overlay, `dlg--xl`)

F4 “Kataki’s portraits · Painted for Kataki and free to use for anyone you make. Nobody else in your library has these.” Filter All / Unused. A grid of portraits (radio group; arrow keys move; a used portrait shows who has it). Footer: “Portrait 5 · focus set for you, change it after” · Cancel · **Use this one**.

F5 “Where is their face? · Drag the circle onto the face. Every crop, from the 20 px avatar to the full card, centres on it.” Large image with a draggable focus circle (arrow keys move it 1%, Shift+arrow 10%; live value “Face focus, {x}% across, {y}% down.”), and “How it crops” previews: Avatar · list · card · scene widget. **Describe the picture** field (alt text, “Read aloud by screen readers. About them, not the file.”). File info line `{file} · {w} × {h} · face at {x}% {y}%`. A file that can’t be used shows the bad callout “That file isn’t a picture Kataki can use · PNG, JPG or WEBP, up to 20 MB.” (PORTRAIT_UNSUPPORTED) with Choose a file. Cancel · **Use it**. Files are copied into the library and re-encoded; the original isn’t touched.

### `/characters/:id/edit` — F6 EditCharacter · F7 DiscardChanges

The F1 form with every section that has content open, prefilled. Differences: title “Edit {name}” with sub “Made {date} · {n} stories · {m} memories”, the readiness callout reads “He stays the same person · Edits change who he is from now on, not what already happened.”, a warm callout at the top “Changes apply from his next line · What Mike already said stays as written. His memories aren’t touched by editing his profile.”, and the footer shows `{n} unsaved changes` + the changed section names, **Discard**, **Save changes**.

Leaving with unsaved changes (Rail, Alt ←, Esc, closing the window) opens **F7**: Dialog (sm, warm) “Leave without saving?” · “You changed {sections}. If you leave now, those changes are lost.” · **Keep editing** (focus) · **Discard changes** (danger) · **Save and leave** (primary).

---

## G · New story

### `/stories/new` — G1, G2, G4 (G3 overlay)

`StepHeader` “New story · Four choices, three of them optional.” then four numbered sections, and a sticky summary card at inline-end showing the scene still, the name, and “{names}, with you as {persona}”.

1. **Who is in it** — selected people as large chips with portrait and computed meta (`{memories} memories · {stories} stories · knows this place`); a row of suggestions; **Find** (→ G3); “Or a group” chips. **G2** (two or more): a presence `Select` per person (Here from the start · Out back, joins later · Not here tonight) and the note “Whoever fits answers each line. To pick who speaks, use Advanced in the composer.”
2. **You are** — `PersonaCard`s; a character who is also a persona can’t be both (“Also your persona · can’t be both in one story”).
3. **Where** — place stills (Halcyon Coffee, Corvel Palace, the flat on Ardenne, **Somewhere new**). **G4 Somewhere new**: inline Name, What it’s like, Time of day `Segmented` (Dawn, Day, Dusk, Night), checkbox **Keep it in World** (“Filed under {book}, so other stories can go there.” — the book chosen in File it under).
4. **What is happening** — plot cards from World (hook in quotes, “{plot} · a plot · opens with …”) or **Nothing in particular** (“Start on an empty scene and let it happen. You can drop a plot in later from the story menu.”).

Then **Name it** (optional; “Leave it and it’s named after the place and the day.”) and **File it under** (`Select`: books · Not in a book · New book…; hint “A new story in this book. Or leave it unfiled.”). Footer: **Start the scene** (primary; disabled until at least one person). Leaving is the Rail or Esc; there is no Cancel button.

Start creates the story and goes to `/story/:id` (P20 for a new story; P21 when a plot was chosen, the narrator’s opening line first).

### G3 NewStoryFind (overlay)

Dialog “Who is in it · Everyone you’ve made or imported. Pick as many as you like.” Search field “Find someone”, then rows with checkbox, avatar, name, meta (`Draft · no secret yet · can still play`, `Imported yesterday · never played`, `Also your persona · can’t be both in one story` disabled). Cancel · **Done**.

---

## H · Stories

### `/stories?by=story|character` — H1, H2, H3

**Header**: “Stories” + **New story** (primary). Toolbar: `SearchField` “Find a story”, chips All / Pinned / one per book (Close to the Crown, The Flat on Ardenne) / one per non-default persona with stories (As Cas) / Unfinished, `Segmented` By story / By character, Sort (Recently played, Recently written, Story time, Name, A to Z).

**H1 By story**: two columns. Inline-start: a list of `StoryCard`s in the chosen sort (books are filters, not headers), each (people, title, book, last stored line, `when`, story time). The selected story shows in the inline-end **`StoryPreview`** (sticky): the place still, title, meta, last played, **Continue**, “Who is here” with per-character memories count and mood pill, “New since you left” `EventCard`s, “Where it happens” places, and **Rename · Export · Unpin · Delete**.
**H2 By character**: one section per character (avatar, name, `{n} stories · {m} memories`), their stories as compact cards with `{n} memories from this story` and doubts.
**H3 Empty**: `EmptyState` “No stories yet · A story starts the first time you say something to someone. Every one you play is kept here, with who was in it and where.” + **New story** and **Import a story**.

### H4 RenameStory (popover at the card) · H5 DeleteStory (dialog) · H6 ExportStory (dialog)

- **H4**: `Popover` “Rename” with the Name field (story face, max 60, hint “Only the name changes. Characters don’t notice.”) · Cancel · **Rename**. Enter saves, Esc cancels.
- **H5**: Dialog “Delete “{story}”?” · “{lines} lines and the {memories} memories {names} made in it go with it. There is no copy anywhere else.” · checkbox “Also make {names} forget it” with the note “Otherwise they keep what they remember from it, and it can come up in other stories.” · Keep it · Export first · **Delete story** (danger). Toast with Undo.
- **H6**: “Export “{story}” · Readable files you can keep, share, or import on another computer.” `RadioGroup` As: A folder of readable files (story.md, story.json, art/) · One Markdown file · A .kataki file. Include checkboxes: What {names} remember from it (`{n} memories, with how sharp they are now`) · Every take and edit · Their profiles and portraits. **Where** folder row (default `Documents\Kataki\exports`, Choose). Note “About {size} · works without the model running”. Cancel · **Export**. Writes to a temp name and renames when done (no partial files). Toast `toast.export.done` with Show.

---

## I · World

### `/world` — I1, I2

**Header**: “World · Places and plots, filed under the books and stories they belong to.” Actions: New book · New plot · **New place** (primary).

**Layout**: a book list at inline-start (Everything {n}, then each book with its stories and counts, “Not in a book”, “other books · {n} not filed yet”), content at inline-end: `Breadcrumbs` (World › {book} › {item}), a `Segmented` **Show** All / Places / Plots and a sort `Select` (Recently used, Recently made, Name A to Z). Places as `PlaceCard`s (still, name, `TimeStrip`, blurb), plots as `PlotCard`s (hook in quotes). An unfiled place shows **File it** (→ I8). Cards open I3 / I4.

**I2 Empty**: `EmptyState` “No places yet · Places appear here when a story goes somewhere, or when you make one. Plots are openings you can drop into any story. Books keep both tidy.” + New place · New plot · Import a lorebook (→ D4, lorebooks come in as places and plots).

### I3 PlaceDetail · I4 PlotDetail (overlays, side sheet 560)

- **I3**: the still with caption, name, `TimeStrip`, description, **Ways out** (exits), **Who knows it** (avatars), **Stories here**, **Music when you’re here**, actions **New story here** (primary) · Edit · Export · ··· (PlaceMenu).
- **I4**: “A plot · {book} · used in {n} story”, hook, **How it opens**, **Who is in it**, **Where**, **What the narrator knows** (shown only here, never in a story), **Used in**, actions **New story from this plot** (primary) · Edit · Drop into a story… · ···.

### I5 NewPlace · I6 NewPlot · I7 NewBook · I8 FileDialog

- **I5** (`dlg--lg`): Name · A picture of it (drop zone; “Shown behind the story, blurred and dimmed. Leave it and the scene uses a plain dusk.”) · What it’s like (“Everyone there can see this. The narrator reads it when a scene starts.”) · Usual time (`Segmented` Dawn/Day/Dusk/Night) · Ways out (“Used when someone leaves: “Theo went along the sea wall.” Separate with commas.”) · File it under. **Make the place**.
- **I6** (`dlg--lg`): Name · The hook (“One line. It’s what you see on the card.”) · How it opens (“The narrator’s first line when the plot starts.”) · What only the narrator knows (“Steers the narrator. Never shown in the story.”, placeholder “Where it’s going. Characters never see this.”) · Where · File it under. Footer note “Anyone can be put in it when you start”. **Make the plot**.
- **I7**: Name · What it’s about (placeholder “For you. Characters don’t read this.”) · Move these into it (checkbox list, e.g. “The Long Way Home · Story · as Cas”; “Only things not filed yet are listed.”). **Make the book**.
- **I8** (`Popover` at the card): “File Corvel Palace · File it so it shows up where it belongs.” · **Book** `Select` · **Stories** `Select` · **Who knows it** chips · Cancel · **File it**.

---

## J · You

### `/you` — J1

“You · Who you play as, and what each character knows about them.” Persona cards (`PersonaCard`: picture, name, line, tags, `Playing as · default` pill, Edit persona, Switch), the **Director** card (“Play no one. Narrate, and let them talk.” — a mode, not a stored persona), and **New persona** `AddCard`. For the selected persona: **Who knows {name}** — per character, per story, how sure they are: `MemoryRow`s grouped by character (“Her mother is the queen’s step-sister. · Mike · Two Sugars, No Title · going hazy” + **Make him forget** → E4 for that character). Footer links: Export everything about {name} · Make a character forget something · Delete this persona (→ J3).

### J2 EditPersona (`dlg--lg`) · J3 DeletePersona (Dialog)

- **J2** “Edit {name} · Characters see this person, not you. Changes apply from your next line.” Picture (Change picture · Crop and focus · Remove), Name, Pronouns (`Select`), Who you are, Tags, `Toggle` “Use {name} when a new story doesn’t pick someone”. Note “The default persona · {n} stories”. Cancel · **Save**.
- **J3** “Delete {name} as a persona?” · “You won’t be able to play as {name}. {name} the character stays, with everyone {name} knows. {story} keeps your lines, marked as a persona you deleted.” · checkbox “Also make characters forget what they know about {name} as a persona” (`{n} memories, held by {names}`) · **Keep {name}** · **Delete the persona** (danger). The default persona can’t be deleted: the dialog instead says “You can’t delete the default persona. Pick another default first.” with only Close.

---

## K · Settings

All settings pages: `.set` grid — `SideNav` (218) with General, Appearance, Language, Models, Memory and thinking, Data and privacy, Shortcuts, About, footer link “What’s new” (with a dot when unseen) — and a panel of `SettingsSection`s made of `SettingsRow`s. **Every change applies immediately and saves itself**; there is no Save button except inside dialogs. A setting that restarts something says so in its description.

### K1 General · `/settings/general`

| Row | Control | Values (default first) | Stored as |
|---|---|---|---|
| When Kataki opens | Select | Home · The last scene | `general.openTo` |
| Autosave | pill “Always on” | — | — |
| Keep a history of edits | Select | 30 days · 90 days · Forever | `general.editHistoryDays` |
| Check for updates | Select | Weekly · Daily · Never | `general.updates` |
| Start with Windows | Toggle | off | OS login item |
| Closing the window | Select | Quits Kataki · Keeps it in the tray | `general.closeAction` |
| Send anonymous usage data | pill “Not collected” | — | — (no code path exists) |
| Default persona | Select | personas · Director · play no one | `story.defaultPersonaId` |
| Composer mode | Select | Auto · Say · Do · Whisper · Think · Narrate | `story.composerMode` |
| Show who hears what | Toggle | off | `story.advancedComposer` |
| Music | Select | Match the scene · Keep one track · Quiet | `story.music` |
| Music volume | Slider | 62% | `story.musicVolume` |

### K2 Appearance · `/settings/appearance`

Theme `ThemeTile`s Night (“The default”) · Day (“Its own palette”) · Follow the system (“Windows decides”); Text size `Segmented` 100% · 125% · 150% (Ctrl + continues to 200%); Reduce motion (Follow Windows · Always reduce · Never reduce); Show the stars (Toggle, on); Story typeface (Newsreader, a book face · Figtree, plain · Atkinson Hyperlegible); High contrast (Toggle); and the callout “What isn’t adjustable, on purpose”.

### K3 Language · `/settings/language`

`LanguageTile`s with completeness (English Complete; العربية Right to left · in progress; others Not started — tiles for incomplete languages are selectable only when at least 95% translated, else disabled with their status). Rows: Mirror the layout for right-to-left languages (Automatic), The real clock (12-hour · 24 on hover / 24-hour), Digits (Western · Eastern Arabic; only for Arabic), Help translate Kataki (**Open the file** opens `strings/` in the file manager). Callout: “Switching language restarts the window · Your place is kept. Anything you were typing stays in the composer.”

### K4 Models · `/settings/models` — K5 Advanced · K6 failing

1. **Status** at the top: a `StatusLine` — ok “Everything is working · Running on {model} through {server} on this computer · last reply took {s} s” · warm “Using the fallback · {server} isn’t answering, so Kataki’s own model is speaking for now. Replies are shorter and plainer until it’s back.” · **Test again**.
2. **Where it runs**: `ConnectionRow`s in priority order (name, state pill Connected / Ready / Fallback / Not answering, detail, Test, Remove, ··· ConnectionMenu). Kataki’s own model is always last and can’t be removed while it is the only one. **Look for servers on this computer** (→ K8) · **Add an online model** (→ K7) · **Change the order** (drag handles or Alt ↑ ↓).
3. **Who does what**: `JobRow`s for Characters, Narrator, Memory reader, Reasoning, Recall by meaning, each with its model. **K5**: a job opened shows its model `Select`, Thinking before replying (`Select` None · Low · Medium · High — the reasoning effort sent to models that support it; Memory and thinking › Thinking decides whether the pass runs at all), Temperature, Context length, Longest reply (`Slider`s), Top-p, Min-p, Repetition penalty (`TextField`s), Stop sequences (`TextField`, optional, “One per line. Kataki adds the persona’s name for you.”), Seed (“Set one to make a reply repeat exactly.”), and **Back to defaults**. Note: “Changes apply from the next reply · Backstage shows the values each turn used”.
4. **K6**: failing connections show inline error blocks under their row, using the Settings variants in `errors.json`: “Nothing answered at {address} · Tested {ago}: connection refused. Is {server} still running?” (Test again) and “{provider} turned the key down · It answered 401. The key may have been revoked or mistyped.” (Replace the key). The status at the top switches to “Using the fallback”.

### K7 AddApi · K8 FindServers (overlays, `dlg--lg`)

- **K7** “Add an online model”: Service `Segmented` (OpenRouter · OpenAI · Anthropic · Something else), Address (Something else only, e.g. a Together endpoint), Key, **Call it** (display name, “How it’s listed in Where it runs.”). The privacy callout. **Test** fills a result line (`{service} · {n} models · {model} picked`) and a **Model** `Select`, then **Add it**.
- **K8** “Servers on this computer · Looked on the usual ports just now. Nothing on your network is scanned, only this computer.” Rows: llama.cpp · port 8080 (Added), Ollama · port 11434 (`{n} models: …` · **Add**), LM Studio · port 1234 (Not running), KoboldCpp · port 5001 (Not found). “Or add one by address” field (“Another computer on your network works too, if its server allows it.”). **Look again** · **Done**.

### K9 Memory and thinking · `/settings/memory`

How fast memories fade (Fast · Life-like · Slow · Never), They can be wrong (Toggle), They can doubt you (Toggle), Thinking (None · Some · A lot), Hearing (Realistic · Everyone hears everything), Recall by meaning (Toggle; needs an embedding model), How far back they look (Slider, messages), and the “Backstage shows you all of this happening” callout with **Open Backstage** (→ the last story with Backstage on).

### K10 Data and privacy · `/settings/data`

The privacy callout, then: **Where your things live** (`FolderRow`s: Stories and characters · Portraits and places · Models, each with path, size and Open folder; **Move the library somewhere else**), **Take it with you** (Export everything → K11), **Automatic backups** (summary line + Change → K12), **Import** (→ D4, also accepts .kataki and a whole exported library), **Keys** (“{n} keys in Windows Credential Manager: {names}. Never written to a file.” · Forget both keys), **Delete** (Delete something → K13).

### K11 ExportAll · K12 Backups · K13 DeleteSomething (overlays)

- **K11** progress dialog “Exporting everything · To {folder}. Keep using Kataki; this runs on its own.” `StepList` (Stories · `{n} as Markdown and JSON` · Characters and personas · `{n} as JSON with portraits` · Art · `{done} of {total} pictures` · World · `{n} places and plots`), `ProgressBar`, note “Models aren’t included; they download again anywhere.” **Stop**. Done state: “Exported · {files} files, {size}. Everything you made, readable without Kataki.” · **Open the folder** (primary) · Done.
- **K12** “Backups · A full copy of your library, made in the background.” Where (folder, Choose; “Another drive is safest.”), How often (Daily · Weekly · When Kataki closes), Keep (The last 7 · The last 30 · All of them), list of backups (when, size, **Restore**), **Back up now**, total `{n} backups · {size} on {drive}`. Restore opens the warm callout “Restoring replaces your library · What you have now is backed up first, so restoring can be undone. Kataki restarts to finish.”
- **K13** “Delete something”: `RadioGroup` One story · One character · One persona · Everything (“Back to first run, as if Kataki were just installed”). One X → a picker then that item’s own delete dialog. Everything → the bad callout “Everything means everything · {counts}. Models and keys stay.” + “There is no server copy. Your backups are the only way back.” + confirm field “Type DELETE EVERYTHING to confirm” (CONFIRM_MISMATCH “That doesn’t match yet.”) · Keep it all · Export everything first · **Delete everything** (danger). Afterwards Kataki restarts to `/welcome`.

### K14 Shortcuts · `/settings/shortcuts` · K15 remap

“Every one of these can be changed: click it and press the new keys. Nothing in Kataki needs a mouse.” with a “Find a shortcut” search field and **Reset all** at the top right. Two columns: Anywhere and Moving around (inline-start), In a story (inline-end), each a list of `ShortcutRow`s (see `KEYBOARD.md`). Clicking a row (or Enter) starts **recording** (K15): the row shows “Press the new keys…” and Cancel; Esc cancels; the first non-modifier key with its modifiers is taken. SHORTCUT_TAKEN shows as a warm callout above the lists (“Ctrl R already regenerates the last reply · Use it for Reading mode instead, and leave Regenerate without a shortcut?”) with **Use it here** · **Pick other keys**; SHORTCUT_RESERVED blocks.

### K16 About · `/settings/about` — K17 update states · K18 Licences

Identity card (“Kataki RPAI · Version {v} · {os} · local-first · nothing here phones home”) with Check for updates · Licences (→ K18) · The manual. **Tell us something** (Give feedback · Report a bug · Suggest something → L1 in each kind). **What’s new** (`Changelog`). K17 shows every state of Check for updates in order (checking, up to date, available, downloading, ready, UPDATE_VERIFY_FAILED, off). K18 lists licences with **Read it** links that open bundled texts offline.

---

## L · Feedback (overlay on any route)

One dialog with **What kind** `Segmented`: Feedback · Bug · Suggestion.

- **L1 Feedback**: What’s on your mind (TextArea; “Two sentences is fine. Anything at all.”), Where can we answer you (optional email; “Only used to reply to this. Never added to anything.”).
- **L2 Bug**: What happened · Tell us a bit more · **What will be sent** panel: “Nothing here is collected automatically. Remove anything you don’t want to send.” with removable rows: `Kataki {v} · {os}`, `{server} · {model}`, `Last error · {file}:{line}` (Show it), Screenshot of this screen (Look at it), The story this happened in · not attached (Attach). Note “No story text, no character names and no file paths are included unless you attach them.”
- **L3 Suggestion**: What did you want Kataki to do (“What you tried, and what you expected. Not how to build it.”), checkbox Attach a screenshot of this screen (“The one on the left. It shows your character and story names.”) with Choose a different picture.
- Footer: **Copy instead** · **Send**. Send posts to [FEEDBACK HOST].
- **L4 results**: Sent (“Sent. Thank you. Reference KT-{xxxx}. If you left an address, the answer comes there. Nothing else was kept.” · Done), Copied (“The whole report is on your clipboard as plain text, attachments listed. Paste it wherever you like.”), Couldn’t send it (FEEDBACK_OFFLINE: “This computer isn’t reaching the internet. The report is saved and goes the next time Kataki is online, unless you cancel it.” · Cancel it · Copy instead · Try again).

---

## N · System

### `/status/model` — N1 ModelGone

A Sky page (Rail, Home active). `Alert` “Nobody is home to answer.” with the MODEL_GONE copy and actions Try again · Use Kataki’s own model instead · Open Settings; a live status line “Trying again every 10 s · next in {s} s · this page closes itself when it answers” (returns to where the user came from on success, with `toast.model.back`). **What still works**: Read · Write · Export callouts. **What usually causes this**: four fixed causes chosen by the error detail (ECONNREFUSED → server closed; wake from sleep → the computer went to sleep; model unloaded → with a button to use Kataki’s own model; port changed → Look for servers). “Still stuck? Report this with the log attached” → L2.

### N2 DiskFull (takeover)

Replaces the window when a write fails for space (DISK_FULL) or permission (DISK_READONLY). Alert, “What Kataki uses on {drive}” meters (Models, Portraits and places, Stories and characters, Backups), two callouts (Move models to another drive · Keep fewer backups), and a live line “Checking for room every 30 s · {n} lines waiting to be saved”. Writes queue in memory; the takeover lifts itself when a write succeeds.

### N3 AlreadyOpen (takeover in a second window)

Shown only if the first instance doesn’t respond to the single-instance handoff within 3 s. **Switch to it** (tries again to focus the other window) · **Quit this one**.

---

## R · Proofs

R1–R6 are not screens; they are acceptance tests for the rules in `ROUTES.md` › Layout breakpoints and `ACCESSIBILITY-AND-MOTION.md`. R6 is Home in the Day theme, the reference for Day across every page.
