# The Scene · `/story/:id`

Boards P1–P21 and Q1–Q5. P1 is interactive on the canvas: type in the composer and send.

## Layout at 1440 × 900

| Region | Position | Contents |
|---|---|---|
| Place art | full bleed, 30 px overscan, blur 3 px, brightness 0.55 | the current place’s picture; plain dusk when it has none |
| Tint and vignette | full bleed | `--scene-tint`, `--scene-glow`, radial vignette |
| Header | inline-start 24, top 20 | `SceneHeader`: cloud button (“Back to the Sky”), story name, `as {persona} · {book}` |
| Header actions | inline-end 24, top 20 | `BackstageToggle`, Search (“Search this story”), ··· (“Story menu”) |
| Chat | inline-start 320, top 16, 800 × 868 | `ChatPanel` with the lines and the `Composer` |
| Widgets | inline-end 24, top 84, 272 wide | character widgets, stacked, gap 14 |
| Clock and music | inline-start 24, bottom 24, 272 wide | `ClockWidget`, `MusicWidget` (plus any widgets the user moved there) |

The Scene always uses the scene palette (`--scene-*`), whatever the Sky theme. Other widths: `ROUTES.md` › Layout breakpoints.

## Lines

Each stored line renders as one of:

| Row kind | Component | When |
|---|---|---|
| Title card | `TitleCard` | story start, a place change, a time skip (`{place} · {relative}`); after a skip it carries Undo until the next line |
| Story note | `StoryNote` | joins and leaves: template `{name} joins.` / `{name} went {exit}.` with the avatar (away style for leaves) |
| Line | `ChatLine` | a persona, character or narrator line. Speaker colour from `--speaker-{id}`; the narrator uses scene ink |
| Hidden marker | dashed row “You hid {n} line here” + **Show it** | where the user hid lines |
| Edit | `EditLine` | the line being edited (P8) |
| Error | `.lineerr` | where a reply failed (P19) |

A `ChatLine` shows: name, time (relative story clock; `Stamp` with the exact time and the story-date detail on hover/focus), the ✦ “Drew on memory” mark when the reply used a recalled memory, the text with `*actions*` in the action style, then children in order: `RecallBox` (P13), heard chips (P6), reactions, and “Thought for {s} s” when reasoning ran.

**Reactions** are templates over the events a turn wrote (`DATA.md` › Templates). At most three under a line; more collapse into “+{n}” which expands. Kinds: memory, feeling, warm, belief, mood. `soft` style for low-importance ones.

**Line tools** (P10): hover or focus a line → `LineTools` above it: previous take ‹, `{take}/{takes}`, next take › (a new take when on the last), Edit, Hide. Right-click → LineMenu (`OVERLAYS-AND-MENUS.md`).

Long stories: the lines list is virtualised; 200 lines render around the viewport; scrolling up loads more. Opening a story scrolls to the end. A “Jump to the latest” chip appears when the user has scrolled more than one screen up and a new line arrives.

## The composer

`Composer` in the chat panel.

- **Simple** (default): the text field, `Segmented` Simple/Advanced, ⏩ “Continue the story” (Ctrl J: the next character speaks without a user line), the mode chip, **Send**.
- **Advanced** (P6; default from Settings › General › Show who hears what): adds above the field “Only {names} will hear this” with avatars, away names (“Theo is away”), and **Answers** chips (Whoever fits · each present character · Narrator; ··· for more when over three → WhoAnswersMenu), and below it **Pass time** and the token meter `~{used} / {limit} tokens`.
- **Placeholder**: `Speak or act as {persona}…`; while a reply streams (P9): `{name} is answering…`; first moment (P20): `Say hello to {name}, as {persona}. *Actions* go between asterisks.`; model offline (P19): “You can keep writing. Lines wait until the model is back.”
- **Keys**: Enter sends, Shift Enter new line, Ctrl Enter send and pass time (opens Pass time after sending), ↑ in an empty field edits your last line, Esc while streaming stops the reply, Tab cycles who answers (Advanced).

### How a line is read (P7)

The mode chip shows **Auto** and what it detected (`Auto · Do + Say`). ModeMenu (radio): Auto (works it out from how you write) · Say (plain text) · Do (`*between asterisks*`) · Whisper (`(in brackets)`) · Think (`_underscores_`) · Narrate (`> a line starting with >`). Picking one overrides for this line only, then returns to the story’s default mode. Detection is a parser, not a model: the markers above, applied per span.

Whisper: only characters “close” (same place, marked here) hear it, per Settings › Memory › Hearing. Think: nobody hears it; it is stored as the persona’s thought. Narrate: written as a narrator line under the user’s name.

## A turn, as the UI sees it

```
Send
 1. the user line is written to disk (it never waits for a model)
 2. the answering character’s widget shows “thinking…”; the composer switches to Stop
 3. reasoning (optional)      → “Thought for {s} s” under the reply when done
 4. the reply streams in        → a ChatLine with “writing…” and a caret (P9)
 5. the reply is written to disk
 6. events are written          → reactions appear under the lines they belong to, 150 ms apart
 7. the memory reader runs      → no visible change except reactions of kind memory; Backstage shows it
```

- **Stop** (Esc or the button): the partial text is kept as a take and marked stopped; reactions don’t run for it.
- **Queued**: while a reply is streaming the user can type; Send is replaced by Stop, and Enter queues the new line (a small “1 waiting” note in the bar). Queued lines send in order.
- **Screen readers** hear the reply once it’s finished, then the reactions; never the stream (see `ACCESSIBILITY-AND-MOTION.md`).
- **Failure** (P19): the reply slot becomes a `.lineerr` block with the title, text and code from `errors.json` (REPLY_UNREACHABLE, REPLY_TIMEOUT, REPLY_EMPTY, REPLY_CUT_OFF, API_*), and **Try again** · **Use Kataki’s own model** · **Edit my line**. Kataki retries on its own every 10 s while the error is a connection error; the block disappears when a reply arrives. After three failures the header shows a bad dot on the cloud button and MODEL_GONE’s page is one click away.

## Takes, edits, hiding (P8, P10)

- **New take** (Ctrl R on the last reply, › on the last take): regenerates that reply. Takes are kept; ‹ › flip. Only the active take is in the story and in memory.
- **Edit** (P8): `EditLine` in place. **Save edit** changes the line only (“only changes what the model reads from now on. The story after it stays as written.”). **Save and regenerate from here**: rewrites the {n} messages after it; they are kept as the previous take (“Regenerating from here rewrites the {n} messages after this one. They’ll be kept as the previous take, so you can flip back.”). Lines after an open edit are dimmed.
- **Hide**: removes the line from the story and from what models read; a hidden marker stays with **Show it**. Toast with Undo.
- **Rewind to here…** (LineMenu, danger): confirm “Rewind to {time}? The {n} lines after it are removed from this story, and what characters learned from them is forgotten.” · Cancel · **Rewind** (keeps them in edit history for `general.editHistoryDays`).
- **Branch a new story from here**: creates a copy up to this line, named `{story} · branch`, and opens it.

## People: joining, leaving, presence (P4, P5)

Presence per character per story: **here**, **nearby** (could join), **gone**. A join or leave is an event written by the engine (or by the user in Scene and place) and shows as a `StoryNote` plus a widget change: joined characters get an unpinned widget with the badge “Joined” for two minutes of real time.

Character widget status line is a fixed format, `widget.status` = `{presence} · {detail}`: presence is Here · Joined · the exit they left by (“Out back”) · Not invited (left behind by a time skip); detail is the relationship to you (“fond of you”), a feeling delta this scene (“trust +6 this scene”), time since (“2 min ago”, “three weeks”), or presence detail (“away”, “could join”). While the character is answering, the whole line is `widget.thinking` “Choosing {his} words”. Examples on the boards: “Here · fond of you”, “Here · trust +6 this scene”, “Joined · 2 min ago”, “Out back · away”, “Out back · could join”, “Not invited · three weeks”.

## Widgets (P3, P21)

Kinds: **Character** (`CharacterWidget` card, or `CharacterRowWidget` for away/nearby people), **Story clock**, **Music**, **Place**, **Cast** (everyone here as faces), **Notes** (the user’s own notes for this story; “Only you see these”).

- **Pinned** widgets always show. **Unpinned** ones show only when something happens to them (a character speaks or reacts, the clock jumps) and fade after 30 s.
- **Edit widgets** (P3; Ctrl E or the story menu): the scene dims under a dot grid; the chat becomes inert; each widget shows a drag handle and pin/remove controls; an empty slot shows where a dragged widget will land. The bar at the top: “Editing widgets · Drag anywhere · pinned ones stay, unpinned ones appear when something happens · Space picks one up, arrows move it” · Reset layout · **Add widget** (menu: Character — pick who, Story clock, Music, Place, Cast, Notes) · **Done**.
- Layout is per story, stored as positions in 8 px steps snapped to the two columns; free placement anywhere that doesn’t cover the chat.
- Keyboard: Tab to a widget, Space picks it up, arrows move 8 px (Shift 64), Space drops, Esc puts it back.

## Story time (P11–P13)

- The clock widget shows the story time (`7:14 pm`), its relation to the story (“The evening it rained”, “Three weeks later · the gala”), and the place. Hover or focus: exact time and the story calendar date.
- **Pass time** (P11, from the clock, Advanced composer, story menu, or Ctrl Enter): presets “A moment later +5 min”, “An hour later”, “The next morning”, “A week later”, plus any plot beats with a time (“Three weeks later · the gala · from The Invitation”), and **Choose a time…**. **Where**: Stay here · Somewhere else (then a place picker). **Pass time** confirms.
- **The time skip** (P12): the clouds sweep in (still card with reduced motion) and `TimeSkipCard` shows the story, the big relative label, from → to, and the fade note template `{name}’s memory of {scene} is going {sharpness}` for the character with the most memories of the scene just left. **Undo** stays on the card and then on the title card until the next line.
- The skip is **one transaction**: clock, presence, place, and memory fade. If any part fails → TIMESKIP_FAILED and everything stays as it was.
- **After the skip** (P13): memory-driven lines show `RecallBox` (“{name} remembered, vaguely” + the stored memory + `sharp {when} · hazy now · {source}`) and the time Stamp opens once on the first line to show the new date.

## Music (P14)

`MusicWidget`: play/pause, track and source (“Matched to the scene” or the upload name), volume. The picker: **Match the scene** toggle (picks from tracks tagged for the place and time of day), a list of ambience and music tracks (bundled, plus uploads), **Upload a track · mp3, ogg, wav** (copied into the library; MUSIC_UNSUPPORTED otherwise), **Volume** slider. Ctrl M mutes. Music never autoplays when the OS reports a screen reader running until the user presses play once.

## Other overlays in a story

- **Story menu** (P2): `OVERLAYS-AND-MENUS.md` › SceneStoryMenu.
- **A character’s card** (P15, `Sheet` tone scene, from a character widget): mood + tag, **Right now** (Where, Scene, Here since), **How he feels about you** meters, **Holding onto · {n} of {total}** (top memory, doubted flag), relationship chips, the secret (`SecretCard`, only after the user reveals it on the profile), **Add as widget**, **Let him answer next**, **Send him away**.
- **Scene and place** (P17, dialog): current place still + name + relative time; **Move the scene to** (places, Somewhere new…; “The clouds part and the scene goes there. Nobody’s memory changes.”), Time of day, Weather (Clear · Rain · Snow · Fog), **Who is here** with a presence select per character, Cancel · **Change the scene**. Changing place plays the cloud transition and writes a title card.
- **Story settings** (P18, sheet): Name, Book, You are (persona; “Changing it mid-story: characters meet the new person from the next line.”), Composer mode, Show who hears what, Let the narrator add scene lines, How fast memories fade here, Model for this story. “Saved as you change it” · Reset to defaults.
- **Find in story** (Ctrl F): `OVERLAYS-AND-MENUS.md` › FindInStory.

## Reading mode (P16)

Ctrl Shift R or the story menu. Widgets, composer and header chrome go; a centred 720 column of lines at 21/33 with a fade at the top; header shows only ✕ “Leave reading mode” with the hint “Reading mode · Esc to leave · widgets and the composer are hidden”, plus Search and Export. Reactions and tools are hidden. Esc leaves.

## The first moment (P20)

A story with no user lines: the title card and the character’s greeting (their “How they say hi”, sent as their first line at story creation; not generated). The composer placeholder teaches the action syntax. The widget reads “Here · never met you” when it’s true.

## Narrator and plots (P21)

A plot dropped in (story menu › Drop in a plot…, or chosen in New story) writes a title card `{plot} · a plot` and the narrator speaks its **How it opens** line. The narrator then adds scene lines when Story settings allows it. Narrator lines use the narrator speaker style and can be edited and regenerated like any reply.

## Backstage (Q1–Q5)

Toggle with the header switch or Ctrl B. A blueprint layer (`.bs`: deep blue, 78% opacity) over the scene; all mono. Nothing on it is generated for display: it reads the **TurnLog** the engine wrote (`DATA.md`).

- **Left column**: **Engine · this turn** (`EngineRow` per job: Recall, Feelings, Reasoning, Characters, Memory reader, Narrator; model, time, detail; ok / wait / idle / bad dot), **Whose mind** tabs (present characters, away ones marked, Narrator) and a **turn** slider (1…current), then the view switch: mind · prompt · memories · logs.
- **Q1 mind**: “{name}’s mind · turn {n}” as four columns left to right: **In** (HEARD, SCENE, WHO), **Sense** (RECALL, FEELS), **Inside** (GOALS, BELIEFS, SECRET), **Decide** (the candidate intents with scores; the chosen one marked). Each node is a `MindNode` with its strength 0–1; hot nodes are the ones that most changed the outcome. **copy as JSON**.
- **Q2 one stage**: clicking a node opens its record: what it was asked, what it searched, the threshold, the matched items (memory, sharpness, source, score, used/below), and what it sent on (verbatim). **copy** · **run this stage again** (a real, costed model call; labelled as such).
- **Q3 the full prompt**: `PromptBar` with the six segments (rules, cards, mind, examples, history, tail) and their limits, cache reuse, then the exact prompt text split by segment. Read-only: “What the model saw, exactly. Change it in Settings → Memory and thinking.” **copy all**.
- **Q4 every memory**: the selected character’s memories as a table (memory, sharpness, source, story time, forget), filter field and chips all / sharp / hazy / doubted. Forget asks first (E4).
- **Q5 logs**: this session’s log lines (time, level, source, message), filter field and level chips, **save log file**. “Logs stay on this computer. Nothing here is sent unless you attach it to a bug report.”
- **Right column** (mind and node views): **Prompt** summary and **The reply** (said, tokens in/out, time, what changed).
- Leave: the toggle, Ctrl B, Esc, or ✕.
