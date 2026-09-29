# Where every string comes from

**The rule: rendering a screen must never require a model call.**

If a sentence can only be written by a model that has read the whole history, it is not a feature — it is a per-render cost with no cache key, no test, and no offline behaviour. It also breaks the product's own promise: a local-first app that keeps working when the model server is down (see `Sky2-Error.html`) cannot have screens that go blank without one.

This caught a real mistake. The first pass had lines like *"Four stories together since May. He has met Theo, and did not like it."* and *"Mike is turning that over. He is not sure you said what he remembers."* Those read well and are impossible to ship: each one needs a summarisation call over the full relationship, on every page view.

---

## The four sources a string may have

Every piece of text in the Sky must be one of these. Nothing else is allowed.

| | Source | What it is | Cost to render | Example |
|---|---|---|---|---|
| **1** | **Static copy** | Written once by us, in the strings file. Translatable. | Zero | "Nothing leaves this computer unless you pick the third door." |
| **2** | **Authored content** | Typed by the user when they made the thing. | Zero | "Barista at Halcyon. Son of the queen's hairdresser." |
| **3** | **Computed** | Counts, dates, durations, percentages — from a query. May be interpolated into a static template. | One query | "4 stories · 412 lines · together since 24 May" |
| **4** | **Stored row** | Text a model wrote **once, at turn time**, saved to the database, displayed verbatim afterwards. | Zero | "She didn't want to be on the gala list." |

Source 4 is the important one, and it is the difference between this app and a wrapper. The memory reader already writes a memory line when an event happens — that call is part of the turn the user paid for. Displaying that row later is free, cacheable, testable, and works with the server off. **A model writes into the database; the UI only reads from it.**

So the pattern everywhere is: **a stored row, labelled by an enum, with a number beside it.**

---

## Enums the engine sets

Fixed vocabularies. The engine picks one from the list; the UI maps it to a colour and a label. No free text, so they translate cleanly and can be asserted in tests.

| Field | Values | Set by |
|---|---|---|
| `mood` | calm · wary · uneasy · glad · doubtful · thinking · hurt · amused · cold | The character turn, one per reply |
| `memory.sharpness` | sharp · hazy · forgotten | Decay function over `importance` and elapsed story time |
| `memory.source` | witnessed · told by X · overheard · inferred | Recorded at write time |
| `memory.doubted` | true / false | Set when a new memory conflicts with an existing one |
| `event.type` | new memory · memory faded · memory doubted · memory contradicted · feeling changed · joined · left · secret told | The engine, appended to the event log |
| `relationship` | fond · wary · close · uneasy · hostile · never met | Authored, or moved by the feeling scores crossing a threshold |
| `character.state` | in a story · draft · never played | Derived from the rows |

## Numbers the engine keeps

`warmth`, `trust`, `doubt` — 0–100 per character per persona. Shown as three bars on the living card. They move by fixed increments on known events; they are not judged by a model at render time.

---

## The inventory

Every non-static string in the Sky v2 screens, with its source. The Scene is covered in its own section below.

### Home
| Element | Source | Note |
|---|---|---|
| "Two Sugars, No Title" | 2 | The story name the user typed |
| The last line, in Newsreader | 4 | The message row |
| "Doubtful" pill | enum | `mood` on the character's last turn |
| "41 memories · 2 changed since you left" | 3 | `count(memories)`, `count(events since last_played_at)` |
| "Three weeks later · Corvel Palace · 7:22 pm" | 3 + 2 | Relative date computed from timestamps; place name authored |
| "the gala, three weeks later" (still caption) | 2 + 3 | Scene label authored; "three weeks later" computed |
| Since-you-last-played rows | enum + 4 + 3 | Event type, the stored memory line, "sharp → hazy" from the two stored sharpness values |
| Character cards: name, tagline | 2 | |
| "Played 2 hours ago", "4 stories" | 3 | |
| "In a story" / "Draft" | enum | |

### Mike's profile
| Element | Source | Note |
|---|---|---|
| Name, tagline, tags, About, How he talks, The secret | 2 | All authored at character creation |
| "4 stories · 412 lines · together since 24 May · 2 places" | 3 | Four queries |
| "Doubtful", "at the gala, three weeks later" | enum + 3 | |
| warmth 72 / trust 54 / doubt 46 | numbers | Stored scores |
| "What he still holds onto" — three lines | 4 | Memory rows, ordered by importance |
| "going hazy / held tight / doubted" | enum | From `sharpness` and `doubted` |
| "3 of 41" | 3 | |
| Who he knows: "wary of him", "never met" | enum | `relationship` |
| Stories together, dates | 2 + 3 | |

### Stories
| Element | Source |
|---|---|
| Titles, book names | 2 |
| Last line preview | 4 |
| "2 h ago" / "three weeks later" | 3 |
| "12 memories from this story", "1 doubted" | 3 |
| New since you left | enum + 4 |
| "Where it happens" | 2 |

### World
Place and plot names, blurbs, opening narration: **all source 2** — the user wrote them, or they came with the sample world. Time strips are a per-place enum. "Known by" is a join. Counts are queries.

### New story
"Mike — 63 memories · 4 stories · knows this place" is three queries against a template. It replaced *"Mike remembers your last four stories. Theo has never met you here before."*, which was source zero.

### Characters
"6 characters · 1 draft · 1 group" — three counts. Replaced *"Six people, one of them half-written. Groups are further down."*

### Home · other threads, Search
Each thread shows its **last stored line**, not a summary of the story. Replaced *"Nico will not show you the painting"* and *"Liv and Jae, two days before the gala. Three messages, unfinished."* (now `Liv, Jae · 3 messages · two days before the gala`).

### Settings, errors, empty states, first run
All **source 1**. Including the error page's four causes — a fixed list matched to an error code (`ECONNREFUSED` → cause 1), not a diagnosis written on the spot.

---

## The Scene

The Scene is older than this rule and was swept with it. What it shows, and where each piece comes from:

### Reactions under a line — templates over events

These read like sentences but each is one fixed template, chosen by an event type and a threshold. Nothing is written per line.

| Shown | Template | Fires when |
|---|---|---|
| Mike will remember this | `{name} will remember this` | `memory_added`, importance ≥ 7 |
| Mike trusts you a little more | `{name} trusts you {a little more · more · much more}` | `trust` delta +1–9 · +10–19 · +20 |
| Mike has his doubts | `{name} has {his/her/their} doubts` | `memory_doubted` (pronoun is a character field) |
| Theo didn't like that | `{name} didn't like that` | reaction enum `disliked` |
| Theo is suspicious of you | `{name} is {mood} of you` | `mood` changes to a toward-you value |
| Mike is worried for you | `{name} is worried for you` | `mood` = worried |
| Mike is glad to see you | `{name} is glad to see you` | `joined` + `warmth` ≥ 60 |
| Mike is wary of Theo | `{name} is {relationship} of {other}` | `relationship` row between two present characters |
| Theo went out to the back. | `{name} went {exit}.` | `left` event; `exit` is authored on the place |

### Character widgets

Name + `mood` pill + **one status line in a fixed format**: `{here|away|joined} · {relationship to you | feeling delta this scene | time since}`.
`Here · fond of you`, `Here · trust +6 this scene`, `Joined · 2 min ago`, `Out back · away`.
Replaced free lines like *"Closing up. Glad of the company."* and *"Worried someone overheard."*

### The recall box
`{name} remembered, {sharp → clearly | hazy → vaguely}` + the **stored memory line** + `sharp 3 weeks ago · hazy now · witnessed` (the stored sharpness history and source). Replaced *"Three weeks ago he knew exactly what you said."*

### The character card (peek)
*Right now* is **Where** (the place), **Scene** (its title + relative date), **Here since** (a time) — replaced *"A cloth he keeps folding", "A borrowed jacket, one size out"*. *On his mind* became **Holding onto · 3 of 41**: a stored memory row with its `doubted` flag.

### The time skip
`{name}'s memory of {scene title} is going {sharpness}` — one template, the character with the most memories of that scene.

### Backstage
Backstage is the one place prose-like text is correct, because it **displays the stored output of each stage of a turn that already happened**: what the perception stage recorded, the recall that matched, the goal list, the chosen intent. Those strings were written during the turn and saved with it. Nothing on Backstage is generated in order to be displayed; "Replay this turn" re-runs the pipeline and is an explicit, costed action.

---

## Boards that predate this rule

The **original Sky** (`Sky-*`, including the four dark ones) and the **five style studies** (`Style-A…E`) still contain model-only copy — *"3 new memory events"* is fine, but lines like *"Mike is turning that over"* are on every style study. They are kept as history. **Do not lift strings from them.** Sky v2 and the Scene are the source of truth.

---

## How this was checked

Every visible text node on the 39 live screens (25 Sky v2, 14 Scene) was extracted and classified against the four sources above — 239 distinct strings in the Sky, 158 in the Scene. Each offender was replaced and the sweep re-run with every flagged phrase as a search term: **0 remain.** The generator for each board (`source/generators/sky2.py`, `scene3.py`) is where to re-run it.

---

## Templates, not prose

Where a sentence is wanted, it is a **static template with computed slots**, held in the strings file so it can be translated:

```
profile.meta      = "{stories} stories · {lines} lines · together since {first_played:date}"
event.faded       = "{character} · memory faded"
event.sharpness   = "{was} → {now}"
memory.source.told= "told by {character}"
story.relative    = "{n} {unit} later"          // three weeks later
home.changed      = "{n} events · {last_played:relative}"
scene.who         = "{n} memories from this story"
```

Pluralisation is the usual ICU problem and is handled in the strings file, not by a model.

---

## What is still allowed to cost a call

Exactly one thing, and it is inside the turn the user started, never on a render:

- **The memory reader**, which writes a memory row when something happens in a scene.

Everything else the user sees in the Sky is a read.

---

## How to check this

A screen passes if it renders correctly with the model server stopped. That is a real test, and `Sky2-Error.html` is the screen that proves the app is designed for it: the story is still readable, still editable, still exportable, because none of those surfaces needed a model to draw themselves.

If a new screen wants a sentence that no query can produce — stop, and either make it a stored row written at turn time, or a template over numbers.
