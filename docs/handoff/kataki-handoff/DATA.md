# Data

What the screens read and write. Storage engine and file layout are the implementer’s choice as long as the rules at the end hold. Types are TypeScript-flavoured; `id` is a ULID string; times are ISO strings in UTC; `storyTime` is the story’s own clock (below).

## Library

One folder, default `%USERPROFILE%\Kataki\` (Windows), with three roots the Data page lists separately and the user can move: `library/` (the database and `damaged/`), `art/` (portraits, places, uploads, music), `models/`. Backups go wherever Settings › Data › Backups points.

## Entities

### Character
| Field | Type | Notes |
|---|---|---|
| id, createdAt, updatedAt | | `editCount` increments on every save (“edited 3 times”) |
| name | string ≤ 60 | required |
| tagline | string ≤ 120 | the card line (“Barista at Halcyon. Son of the queen’s hairdresser.”) |
| pronouns | `she` \| `he` \| `they` \| `{custom}` | drives `{he}/{him}/{his}` in templates |
| portrait | `{ file, focusX, focusY, alt } \| null` | focus in % (0–100); `alt` required when a file is set |
| about | text ≤ 2000 | “About them” |
| greeting | text ≤ 1000 | “How they say hi”; required; becomes the first line of every new story |
| sampleLines | text[] (0–6, each ≤ 500) | “How they talk” |
| secret | text ≤ 1000 \| null | null ⇒ `state = draft` |
| tags | string[] ≤ 3 | |
| relationships | `{ targetId, targetKind: character\|persona, relationship }[]` | authored starting point; the engine moves it |
| placeIds | id[] | places they know |
| modelOverride | `{ connectionId, model } \| null` | |
| memory | `{ fade: inherit\|fast\|lifelike\|slow\|never, canBeWrong: bool, canDoubt: bool }` | overrides Settings; `inherit` shows as “Like Settings · {value}” |
| favourite | bool | |
| source | `shipped` \| `made` \| `imported` | `importedFrom` file name for imported |
| deletedAt | time \| null | soft delete for the Undo window |

Derived: `state` = in a story (in any story with presence ≠ gone) · draft (no secret) · never played. `lastPlayedAt`, `storiesCount`, `linesCount`, `memoriesCount`, `firstPlayedAt`.

### Persona
`id, name, pronouns, about, tags[≤3], portrait, isDefault, isAlsoCharacterId?, deletedAt`. Exactly one default. “Director” is not a stored persona (You shows it as a card, “Play no one. Narrate, and let them talk.”); it is `story.personaId = null` with `story.director = true`.

### Story
| Field | Type | Notes |
|---|---|---|
| id, name (≤ 60), createdAt, lastPlayedAt | | name default `{place} · {weekday}` |
| bookId | id \| null | |
| personaId / director | id \| null, bool | |
| placeId | id | the current place |
| clock | `{ calendarDate, time, label }` | story time now; `label` is the authored/derived scene label (“the gala”) |
| timeOfDay, weather | enum | dawn · day · dusk · night; clear · rain · snow · fog |
| cast | `{ characterId, presence: here\|nearby\|gone, exit? }[]` | |
| pinned | bool | |
| settings | `{ composerMode, advanced, narratorLines, fade, model }` all nullable = inherit | Story settings (P18) |
| music | `{ match: bool, trackId?, volume }` | |
| widgetLayout | `{ kind, refId?, x, y, pinned }[]` | per story |
| branchOf | `{ storyId, lineId } \| null` | |

### Line
| Field | Type | Notes |
|---|---|---|
| id, storyId, seq | | seq is the order; gaps allowed |
| kind | `line` \| `titleCard` \| `note` | notes are joins/leaves |
| speaker | `{ kind: persona\|character\|narrator, id? }` | |
| mode | `say` \| `do` \| `whisper` \| `think` \| `narrate` \| `mixed` | parsed on send |
| takes | `{ text, createdAt, connectionId, model, stopped?, tokensIn, tokensOut, ms }[]` | |
| activeTake | int | |
| hidden, edited | bool | |
| storyTime | `{ calendarDate, time }` | the clock when it was said |
| heardBy | characterId[] | presence + mode + hearing rule at send time |
| recalledMemoryIds | id[] | drives ✦ and the RecallBox |
| thoughtMs | int \| null | “Thought for {s} s” |
| error | `{ code, detail } \| null` | a failed reply slot (P19) |

### Memory
| Field | Type | Notes |
|---|---|---|
| id, characterId, text (≤ 300) | | written by the memory reader, or from the card |
| aboutKind / aboutId | persona \| character \| place \| world | whom it is about |
| source | `witnessed` \| `heard` \| `told` \| `overheard` \| `inferred` \| `card` | `heard`: said to them directly; `told` carries `sourceId` (“told by Liv”, reported by someone else) |
| importance | 1–10 | |
| sharpness | 0–1 | decays by story time × fade setting; `pinned` stops decay |
| sharpnessHistory | `{ storyTime, value }[]` | for “sharp 3 weeks ago · hazy now” |
| doubted | bool | set when a newer memory conflicts |
| storyId, lineId, storyTime, createdAt | | |
| forgottenAt | time \| null | purged 30 days later |

Sharpness word: `sharp` ≥ 0.6 · `hazy` 0.2–0.6 · `forgotten` < 0.2 (or forgottenAt). UI phrases: sharp → “held tight”, hazy → “going hazy”, doubted → “doubted”.

### Feeling (per character, toward a persona or character)
`characterId, targetKind, targetId, warmth 0–100, trust 0–100, doubt 0–100, relationship (enum), history[{ lineId, field, from, to }]`. Moved by fixed increments on known events; never judged at render time.

### Event
`id, storyId, lineId, characterId, type, payload, createdAt`. Types: `memory_added`, `memory_faded`, `memory_doubted`, `memory_contradicted`, `feeling_changed`, `mood_changed`, `reaction` (payload `disliked` …), `joined`, `left`, `secret_told`. Reactions and “Since you last played” are templates over events.

### Mood (on each character reply)
`calm · wary · uneasy · glad · doubtful · thinking · hurt · amused · cold · worried · suspicious`. The pill shows the capitalised word.

### Place · Plot · Book · Group
- **Place**: `id, name, description, picture {file, alt}, usualTime, exits string[], bookId?, storyId? (filed under a story), musicTags[]`.
- **Plot**: `id, name, hook, opening, narratorNotes, placeId?, cast characterId[], bookId?, beats[{ label, relTime }]` (beats feed Pass time’s “from The Invitation” presets).
- **Book**: `id, name, about, cover?`.
- **Group**: `id, name, memberIds (ordered), placeId?`.

### Connections and jobs
- **Connection**: `id, kind: builtin|llamacpp|ollama|lmstudio|koboldcpp|tgwui|openrouter|openai|anthropic|custom, name, address, keyRef (safeStorage handle), order, lastStatus {ok, code?, at, ms}`.
- **Job**: `characters | narrator | memoryReader | reasoning | recall` → `{ connectionId|inherit, model, effort: none|low|medium|high, temperature, contextLength, maxTokens, topP, minP, repetitionPenalty, stop[], seed? }`.

### TurnLog (Backstage)
Per turn: `{ storyId, lineId, turn, speakerId, stages: [{ name, connectionId, model, startedAt, ms, state, input, output, items? }], prompt: { segments: [{ name, tokens, limit, text }], cacheReuse }, reply: { tokensIn, tokensOut, ms }, changes: [...] }`. Stored with the story; pruned to the last 200 turns per story unless the user pins one.

### Settings, shortcuts, outbox, crash
- **Settings**: flat keys, e.g. `general.openTo`, `appearance.theme`, `appearance.zoom`, `appearance.reduceMotion`, `appearance.highContrast`, `appearance.stars`, `appearance.storyFace`, `language.ui`, `language.clock`, `language.digits`, `memory.fade`, `memory.canBeWrong`, `memory.canDoubt`, `memory.thinking`, `memory.hearing`, `memory.recallByMeaning`, `memory.lookBack`, `story.*` defaults, `backups.*`, `ui.charactersView`.
- **Shortcuts**: `{ actionId: keys[] }` overrides of the defaults in `KEYBOARD.md`.
- **Outbox**: queued feedback `{ id, kind, body, attachments[], createdAt }`.
- **Crash**: `{ ref, at, lastStoryId, lastSavedLineId, unfinishedReply? }`.

## Templates (strings file, ICU)

```
home.stats            = "{memories, plural, one {# memory} other {# memories}} · {changed} changed since you left"
home.events           = "{n, plural, one {# event} other {# events}} · {lastPlayed}"
home.where            = "{relative} · {place} · {time}"
characters.sub        = "{characters, plural, one {# character} other {# characters}} · {drafts, plural, =0 {} one {# draft} other {# drafts}} · {groups, plural, =0 {} one {# group} other {# groups}}"
profile.stats         = "{stories} stories · {lines} lines · together since {firstPlayed, date, medium} · {places} places"
profile.holding       = "{shown} of {total}"
card.when.played      = "Played {relative}"
event.faded           = "Memory faded"      event.sharpness = "{was} → {now}"
memory.meta           = "{sharpnessWord} · {source} · {story} · {time}"
memory.source.told    = "told by {name}"
story.relative        = "{n} {unit} later"
newStory.personMeta   = "{memories} memories · {stories} stories{knows, select, true { · knows this place} other {}}"
react.remember        = "{name} will remember this"                       // memory_added, importance ≥ 7
react.trust           = "{name} trusts you {size, select, s {a little more} m {more} other {much more}}"  // +1–9 · +10–19 · +20
react.doubts          = "{name} has {pronoun, select, he {his} she {her} other {their}} doubts"  // memory_doubted
react.disliked        = "{name} didn’t like that"
react.moodToYou       = "{name} is {mood} of you"
react.worried         = "{name} is worried for you"
react.glad            = "{name} is glad to see you"                        // joined + warmth ≥ 60
react.gladCame        = "{name} is glad you came in"                       // persona arrives at a place where name is, warmth ≥ 60
react.mood            = "{name} is {mood}"                                  // mood_changed, not toward you (“Mike is uneasy”)
react.relation        = "{name} is {relationship} of {other}"
note.joins            = "{name} joins."
note.left             = "{name} went {exit}."
widget.status         = "{presence} · {detail}"                           // Here · fond of you / trust +6 this scene / Joined · 2 min ago / Not invited · three weeks
widget.thinking       = "Choosing {pronoun, select, he {his} she {her} other {their}} words"
crash.body            = "Last time, Kataki stopped at {time} while {name} was answering. Everything up to {his} last finished line is safe. The line {he} was writing is gone."
recall.title          = "{name} remembered, {sharpness, select, sharp {clearly} other {vaguely}}"
recall.meta           = "{was} {ago} · {now} now · {source}"
skip.note             = "{name}’s memory of {scene} is going {sharpness}"
composer.hearing      = "Only {names} will hear this"
composer.tokens       = "~{used} / {limit} tokens"
```

## Rules the screens depend on

1. **Every write that the user made is durable before the UI shows it as done.** Lines are written before the model is called.
2. **Deletes are soft for the length of their Undo** (10 s), then real. Forgotten memories are soft for 30 days. Nothing else is ever deleted silently.
3. **The renderer never touches files.** It asks the main process over IPC; the main process validates paths against the library roots and user-chosen folders.
4. **Imports and exports never modify the source files.** Exports write to a temp name and rename.
5. **Keys** live only in `safeStorage`; the library stores a handle. Exports, logs and bug reports never include them.
6. **Schema version** is stored in the library. Opening a newer library refuses (LIBRARY_NEWER); migrating an older one copies first (LIBRARY_MIGRATION_FAILED on failure).
