# Kataki RPAI — Milestone 1 UI: the Sky, the Scene and the memory signals

> The master plan (M0–M5) and the M0/M1 engine spec with its Progress section live in the repo at
> `docs/specs/2026-09-18-m0-m1-design.md`. This file plans the M1 UI rebuild. It is **the source of
> truth** (task 1 copied it here from the approved plan) and its Progress list is where the loop
> records work.
>
> Start the loop with:
> `/loop Continue the Kataki UI rebuild: follow the loop protocol in docs/specs/2026-09-19-ui-redesign.md and do the next unchecked task (if that file does not exist yet, read C:\Users\user\.claude\plans\openroleplayai-openrpai-orpai-is-inherited-wadler.md and do task 1 first).`

## Context

Milestone 1 (chat + the full memory engine) works and was verified against a real model, but its UI
is a plain, text-only set of screens (~1,700 lines: App, Story, Inspector, Models, Library, Stories).
The user commissioned design concepts, now in `docs/kataki-design/kataki-design/` (design system,
17 mockups, placeholder art), written from `docs/design-brief.md`. The concepts are a reference, not
a 1:1 spec. The user wants the M1 UI rebuilt in that design before Milestone 2, and approved:

1. **Scope:** the full M1 UI **including the memory signals** (per-line receipts, callouts, the
   recall spark, the time-skip sequence, Activity, living profiles), plus the small engine endpoints
   they need. Left out, as room rather than fake placeholders: generated art, expressions and
   Moments (M3); music and Sound settings (M4); the Places map and books (M2); import/export;
   phone layouts.
2. **Art:** image uploads for characters, personas and places (stored locally with the library);
   anything without one gets a generated stand-in.
3. **Approach A:** vendor the design system's own CSS, fonts and icon sprite; thin React components
   emit its `k-*` classes; native `<dialog>`/popover; a tiny hash router; **no new dependencies**.
4. **Structure:** the Sky (rail: Home, Friends, Chats, Places, Activity, You, Settings, orb "Dive
   in") and the Scene (stage, conversation, composer; the Backstage switch shows today's Inspector
   as a blueprint lens). Library characters → Friends (AI) and personas (under You); places →
   Places, with scenarios as Plots; stories → Chats; Models → Settings; first launch → First run.
5. Everything else: "I approve everything, don't wait for my approval, plan with your best choices."
   Built in passes: foundation + Sky, Scene + Backstage, memory signals, polish.

Outcome: the app looks and behaves like the concepts. Every feature listed in the brief's
"Reference: what the app does today" stays reachable. The memory system becomes visible: who heard
a line, who will remember it and how clearly, and characters forgetting across a time skip.

## Ground rules
- No new npm or Python dependencies. The vendored design files are never edited; changes go in
  `app/src/app.css` under `ka-` classes.
- The old UI (renamed "classic") stays mounted and working until task 24 retires it, so the app is
  usable at every commit.
- Engine work is test-first. Every task leaves the engine suite, typecheck, build and smoke green.
- The loop never starts the user's GPU model server (llama-server). The demo's fake model covers UI
  work. If llama-server is **already** running on :8080, the loop may use it for an optional check.

---

## Progress
(The loop ticks a box and adds a note line `YYYY-MM-DD · task n · what landed · deviations` in the same commit.
A pass's box is ticked once all its tasks are; a task is done when its number carries `[x]`.)

- [x] **Pass 0**: [x] 1 file the handoff and plan · [x] 2 design base layer and foundation
- [x] **Pass 1**: [x] 3 media and library · [x] 4 stories for the Sky · [x] 5 demo library and fake model · [x] 6 Sky shell and Friends · [x] 7 Chats · [x] 8 New chat · [x] 9 Add a friend / edit · [x] 10 friend profile · [x] 11 Home and persona switcher · [x] 12 Places and Plots · [x] 13 You · [x] 14 Settings and Models · [x] 15 First run, flip, dive
- [x] **Pass 2**: [x] 16 audience (Whisper/Think) · [x] 17 lines, pass time, meta · [x] 18 scene support · [x] 19 Scene frame · [x] 20 composer and streaming · [x] 21 line tools, story menu, reading mode · [x] 22 presence and new scene · [x] 23 Backstage · [x] 24 retire classic
- [ ] **Pass 3**: [x] 25 exact line and clarity · [x] 26 signals I · [x] 27 signals II · [x] 28 receipts, callouts, spark · 29 time-skip sequence · 30 activity engine · 31 Activity UI and badges · 32 people and profiles engine · 33 peek card · 34 living profile and "Who knows you"
- [ ] **Pass 4**: 35 responsive and motion · 36 accessibility and keyboard · 37 empty and error states · 38 cleanup, docs, final verification

Blocked: none. Later (ideas deliberately not built): none yet.

Notes:
- 2026-09-19 · task 1 · design handoff (`docs/kataki-design/`, `docs/design-brief.md`) and this plan committed; `docs/*.zip` ignored; font/image types marked binary; root scripts call `corepack pnpm`; `.dev/library.db` backed up to `.dev/library.pre-ui.db` · no deviations
- 2026-09-19 · task 2 · design CSS, sprite, clouds and fonts vendored in `app/src/design/` (fonts from google/fonts, all `00 01 00 00`, 41–496 KB, bundled into `dist/assets`); old screens in `classic/` with `classic.css` scoped under `.classic`; `api.ts` (query-param dev connection, `upload`, `mediaUrl`, typed item data, log, memory and stream payloads), `hooks.tsx` (race-guarded `useLoad`, `useAction`, `usePoll`, hash router), `ui.tsx` primitives; `App.tsx` sets `data-engine` and routes `#/dev/kit` (in its own `Kit.tsx`, deleted in task 38), everything else to classic; smoke watches `data-engine`. Verified: typecheck, build, smoke PASS; kit shot vs `components.html` matches; walk: 66 symbols, `document.fonts.check` true for all four families, dialog Esc returns focus, menu anchors under its button, classic Library opens · deviations: `LibraryContext` waits for task 6, where it is first used; `Menu` places itself with CSS anchor positioning (the popover's invoker is its implicit anchor); `ErrorLine` emits `ka-error` (classic.css styles it); `Prose` keeps single line breaks (`white-space: pre-line`), in classic too
- 2026-09-19 · task 3 · `media.py` (sniffed PNG/JPEG/GIF/WebP, SHA-256 names, `blobs/` beside the library via temp file + `os.replace`); `POST /media` (201, 413 over 10 MiB, 415 otherwise), `GET /media/{name}` (strict name, immutable cache, nosniff), `?token=` accepted only under `/media/`; library `data` keys documented; safe delete (plot premise kept via `json_insert`, `lib_item_id` unlinked; fixes the FK 500); `create_story` snapshots the premise into `overrides.premise`, which `context._system` reads first. Verified: ruff, format, 252 tests (13 media, 2 delete, 2 premise new) · no deviations
- 2026-09-19 · task 4 · migration 3 (`stories.pinned`, `stories.seen_run_id`); `POST /stories` takes `epoch_offset_min` (≥ 0, default 480); `PATCH` takes `pinned`; `POST /stories/{id}/seen`; one `standing()` helper feeds both `GET /stories` (pinned, then newest message; `last_at`, `messages`) and `GET /stories/{id}` (+ `epoch_offset_min`, `start_clock`), each with `pinned`, `clock`, `story_time`, `minute_of_day`, `persona`/`place` refs (`id, name, lib_item_id`), `scene_title`, AI `cast` with presence, `last_line`. Verified: ruff, format, 257 tests · deviations: both routes carry the same fields (a superset of 2.2's two shapes) so one helper serves both; ties in `last_at` (second resolution) break on the newest message id
- 2026-09-19 · task 5 · `engine/evals/demo.py`: `build` (scripted in-process model; `read_memory` writes the brief's memories keyed to transcript lines and roster handles, so ids never matter; personas Aren and Sable, `settings.persona` = Aren; 5 friends with palettes 1–7; 3 places; 2 plots; 4 stories in the brief's order, "The Third Floorboard" pinned) + `check()`; `serve-model` (stdlib, word-by-word SSE, `--think`, `{}` for memory reads, Stop-safe); Electron `KATAKI_DB` (relative to the repo root); README demo section. Verified: ruff/format/257 tests; two builds print identical summaries and identical story contents; curl streams thinking then content; a real turn through `kataki serve` on a copy of the demo gets a streamed, saved reply; smoke PASS on the demo and the dev library · deviations: Mira's greeting (her `first_message`) opens the story at 19:00 before Aren's 19:02 line; her 19:14 line adds "Your ledger's safe with me." (the plan's "says ledger"), and run 2 files that promise (importance 6); the skip marker is a bare system line until task 17; Clockmaker's Debt starts at epoch 7150 (Day 5, 23:10); Wren has name + who they are (2/6). Note for tasks 25–27: at 19:22 Mira's effortful recall succeeds (the design: pressed again, the detail comes back), so today's `inspect` shows the secret sharp; the brief lists it hazy, which task 25's clarity (cue-free, as of story time) should give
- 2026-09-19 · task 6 · `App.tsx` Sky frame (gradient, two cloud layers as in the mockup, glass rail with logo, Friends, Settings, orb "Dive in"); `LibraryProvider`/`useLibrary` in `hooks.tsx`; `art.tsx` (`PALETTES`, `paletteOf` with name hashing, `backdrop`, `pronounsOf`, `initials`, `Portrait` with initials stand-in or cover image, `Orb`); `sky/Friends.tsx` (`#/friends`: candy filters, cards oldest-first with heart, tagline, status); `api.ts` gains `Ref`, `Standing`, the new story shapes, item timestamps. Verified: typecheck, build, smoke PASS; shot at 1440×900/1190 matches the Friends section of `Sky-Home.html` (layout, order, copy; art is initials by design); walk on a copy of the demo: all five filters give the right friends, a heart persists across reload and unsets · deviations: `Avatar`/`AvatarStack` wait for task 7 (first use); someone who left shows the story's current clock ("Left The Gull · Year 7") until task 18's presence changes say when; the new-friend completeness ring comes with task 9; the card is a stretched link plus a separate heart button (the mockup nests a button in a link); a set heart is pink by stroke only (the sprite's `fill="none"` can't be overridden); Settings and Dive in open classic until tasks 14 and 20
- 2026-09-19 · task 7 · `sky/Chats.tsx` (`#/chats`, `#/chats/:id`): glass list with All / One-to-one / Groups chips, Pinned and All stories sections, rows (avatar or stack, title with pin, story clock, last line without its *actions*, "as Aren" / "directing"), a row menu (Pin/Unpin, Delete with a confirm dialog); the preview (last-moment still: `Room` by time of day + `Figure` of the last AI speaker, scrim, title, place · clock · persona, Dive in orb; "In this story" On stage / Away). `art.tsx` gains `timeOfDay`, `Avatar`, `AvatarStack`, `Room` (CSS lit room: wall, window whose sky and sun/moon follow dawn/day/dusk/night, lamp glow, floor; or the place image with a tint), `Figure` (silhouette with an ink rim light, or the portrait with a radial mask). Verified: typecheck, build, smoke PASS; shots at 1440×900 (matches `Sky-Chats.html`'s layout and copy) and 1280×800 (titles ellipsize); walk on a demo copy: select updates the preview and hash, pin moves a story into Pinned and back, filters, delete asks first ("Keep it" cancels) then removes the story and returns to `#/chats` · deviations: New chat / New group scene / "Start a fresh story with X" come with their dialog in task 8; `SunArc` waits for its first use (task 19); stacks use the design's `.k-avatar-stack` (horizontal) not the mockup's diagonal pair; the row menu sits bottom-right and shows on hover/focus so it takes no room from the title; memory badges and "New since you left" are task 31
- 2026-09-19 · task 8 · `sky/NewChat.tsx`: a native dialog with friend chips (one for New chat, several for New group scene), Where, Plot, Time of day (Dawn 360 / Day 720 / Dusk 1140 / Night 1320), You play (personas, default `settings.persona`, or "No one: I direct the story"), Title (placeholder = plot name, else "Mira at The Gull" / "Mira and Tobin"); `POST /stories`. Chats gains "New chat", "New group scene" and "Start a fresh story with X" (the last speaker, else the first friend with a library item). Verified: typecheck, build, smoke PASS; walk on a demo copy: Start is disabled until someone is picked, single mode switches, "Mira at The Lighthouse" at Dawn as Aren is created (Day 1, 06:00) and selected; a group scene with Ilsa and Oren, The Missing Ledger at Night, directing, opens with the plot's narration (Day 1, 22:00); Esc creates nothing; the fresh-story preset picks Mira; a pane screenshot of the dialog looks right · deviations: "then dive in" lands on the new story in Chats until the Scene exists (task 20 moves every Dive in to `#/story/:id`); Day is the default time of day
- 2026-09-19 · task 9 · `sky/Editor.tsx` (`#/friends/new`, `#/you/new`, `#/friend/:id/edit?step=n`): six `.k-step` steps (name + portrait upload, pronouns, Favourite, "This is me"; who they are; secret; how they talk; how they say hi; other names and tags), "Stuck? Start from" chips that start a sentence in the box, Back / Skip for now / Next: … / Done, a live card (portrait, name, tagline), the completeness ring with a nudge for the first missing step, a done/now/next checklist, Delete (confirm; the engine's safe delete). Saved as you go: a 700 ms debounce plus save on blur, on step change and on leaving, serialised so the first save creates the item exactly once (then the URL becomes its edit route). The palette is the least-used one (`nextPalette`). Friends gains "Add a friend", the dashed add card and the ring on profiles under half done. Verified: typecheck, build, smoke PASS; shot of Wren at step 3 vs `Sky-AddFriend.html` (same layout, copy and ring nudge; 33% is the real 2/6); walk on a demo copy: Next is disabled until named, naming creates "Juniper" (URL becomes `#/friend/13/edit`), a canvas PNG uploads and shows, she/her + Favourite + description + a starter-chip secret, reload returns to step 3 with everything there (engine row checked: palette #8, portrait served 200 image/png), aliases and tags save, Done → Friends shows her portrait card, Delete asks then removes her; `#/you/new` makes a persona (not listed in Friends) · deviations: the ring shows on cards under 50% (so only a just-added profile, as in the mockup) rather than on every incomplete one; Done returns to Friends (or You) until the profile page exists (task 10)
- 2026-09-19 · task 10 · `sky/Profile.tsx` (`#/friend/:id`): big portrait (initials stand-in) with name plate (Chewy name, `k-status` "At The Gull · Year 7", tagline, tags); "Message Mira" (continues the latest story, else opens New chat with her), "Start a new story", "Start a group scene", "Edit profile"; the stat tile "N stories together / as Aren and as Sable"; About (+ "What anyone in a scene can see or know", Also known as), How she talks (bubbles from the example lines, "Mira:" prefixes dropped), How she says hi, the Secret (blurred; "Reveal as author" / "Hide it again"; or an invitation to add one), Stories together (room thumbnails, "with Tobin · as Aren · Year 7"). Pronouns shape the headings ("How they talk"). Editor's Done now lands on the profile. The bottom cloud layer is anchored 280 px below the page (every mockup does this), which fixes a band on tall pages. Verified: typecheck, build, smoke PASS; shot at 1440×1500 vs `Sky-Profile-Mira.html` (same left column and the in-scope cards); walk on a demo copy: a friend card opens the profile with Friends lit in the rail, Reveal unblurs (filter none) and hides again, Message links to the latest story, Start a group scene opens the dialog with Mira picked, Wren (no stories) gets "Starts your first story together" and New chat with her picked · deviations: Remembers / Last seen tiles, Right now, Relationships and Places she's been are task 34; Moments wait for M3; until then Stories together spans both columns; Message opens the story in Chats until the Scene exists (task 20)
- 2026-09-19 · task 11 · `sky/Home.tsx` (`#/home`, first in the rail): the greeting by local time with the current persona's name (or "Director"); `PersonaSwitcher` (exported for You): your ringed avatar with a swap badge opens a popover anchored under it with each persona (tick on the current one), "Director · Play no one", "New persona" and the footnote, and writes `settings.persona`; search over friends (name, description, aliases, tags), stories (title, place, last line, cast) and places, with "Nothing matches"; "Add a friend"; the Continue card (the most recently played story: `Room` + `Figure`, scrim, "Continue" chip, title, place · clock · with who is present · as Aren, the last line with the speaker's ink, orb "Dive back in"); the Friends grid (Friends gained a `section` mode with the Home heading). Verified: typecheck, build, smoke PASS; shot at 1440×1190 vs `Sky-Home.html` (header, Continue, Friends and the clouds line up; Activity and Moments are later); walk on a demo copy: the switcher opens 6 px under the avatar, shows Aren ticked, picking Sable renames the greeting and saves `persona: 2`, New chat then defaults to Sable; search "gull" finds Wren, The Third Floorboard, Harbour Market and The Gull, "zzz" says nothing matches, clearing brings Continue back; a pane screenshot of the switcher looks right · deviations: the Continue card spans the width until the Activity preview arrives (task 31); its chip says "Continue" until memory-event counts exist (task 31); Dive back in opens classic until task 20; the bell comes with task 31
- 2026-09-19 · task 12 · `sky/Places.tsx` (`#/places`, in the rail): place cards (their picture or the `Room` at dusk, name, description, "Start a scene here", Edit) and plot cards (name, "Every character knows" + premise, the opening narration in book type, "Start this plot", Edit); one add/edit dialog per kind (place: name, what anyone there can see, picture upload with a preview, other names, tags; plot: name, premise, opening narration, tags) with Delete behind an inline confirm (the engine's safe delete); both starts open New chat with the place or plot preset. Verified: typecheck, build, smoke PASS; shot at 1440×900; walk on a demo copy: added "The Salt Stair" with a canvas PNG (the preview shows it, focus returns to "Add a place"), its card shows the picture (dusk tint), "Start a scene here" presets it, a night scene with Tobin opens in Chats with the picture and the night tint; Delete asks inline then removes; a plot "A Ship in the Fog" adds with premise and narration, and "Start this plot" presets it (title placeholder = the plot) · deviations: no map yet (the design leaves the islands map open); dialogs stay mounted and open by prop, since a close-on-unmount cleanup in `Dialog` was closing live dialogs under dev StrictMode (found in this walk, not kept)
- 2026-09-19 · task 13 · `sky/You.tsx` (`#/you`, `#/you/:id`, in the rail): the header "You are playing Aren" (or "You are the director"); "Who are you in new chats?" as a card (the rows are now `PersonaChoices`, shared with Home's switcher: each persona, Director, New persona and the footnote; the current one outlined in accent); the persona's portrait with a "Played by you" badge (or "One of your personas" and "Be Sable in new chats"), Edit; and that persona's chats (or "Stories you direct"). The editor's Done lands on `#/you/:id` for a persona. Verified: typecheck, build, smoke PASS; shot at 1440×900 vs `Sky-You.html` (same three columns, copy and outline; "Who knows Aren" is task 34); walk on a demo copy: picking Sable switches the header, portrait and chats (Frost on the Pass, Letters for the Guild), Director shows "You're directing" and no stories, `#/you/2` while playing Aren offers "Be Sable in new chats"; a pane screenshot shows Home's switcher unchanged with the shared rows · deviations: none
- 2026-09-19 · task 14 · `sky/Settings.tsx` (`#/settings`, `#/settings/about`; the rail's Settings now opens it): subnav (Models, About) and the "engine ok" pill; Model servers and APIs as cards (candy tile, "this computer · 127.0.0.1:8080" / "online API · openrouter.ai/api/v1" in mono, an automatic test whenever the list changes: connected / unreachable, "{model} loaded" or "N models", "key stored"; Test, "Change key" / "Add a key" for online APIs or stored keys via `PATCH /providers/{id}`, Remove behind an inline confirm); "Look for model servers on this computer" (found rows disappear once added; "Use this" also sets Characters when it has no model); "Add an API" dialog with presets. Jobs: the open one on the left with every classic field (server, model with the server's list, context size, thinking, kind + Detect now + "found:", room to think and effort for reasoning models, sampler presets as a segmented control that recognises the current JSON, the JSON box, Save + "Saved."), the rest as rows ("Same as Characters · Fake model · fake", "Built-in" for Recall by meaning). About: "engine ok · v · schema" and the privacy line. Verified: typecheck, build, smoke PASS; shot at 1440×1000 vs `Sky-Models.html` (same layout and copy); walk on an empty library with the fake model (`--think`): detection finds nothing on the usual ports, Add an API "Fake model" at :8099 tests connected + "fake loaded", Characters saved with fake / 16384 / thinking off / Balanced + DRY (engine row checked), Detect now says reasoning (the room-to-think and effort fields appear), the other jobs read "Same as Characters", a second API adds and the dialog closes with focus back, Remove confirms, OpenRouter via preset lists 447 models and offers "Add a key" (dialog opened and cancelled; no key written to the real keychain) · deviations: General, Sound and Privacy in the mockup's subnav are left out (M4 and later); the key dialog is offered for online APIs and stored keys only
- 2026-09-19 · task 15 · `sky/FirstRun.tsx` (`#/welcome`): the hero "They'll remember this." over clouds, three step cards (the active one wide; finished ones show a green check and a one-line summary): 1 Connect a model (detects on mount, found servers with "Use this" which adds the provider and sets Characters, "Look again", "Or add an online API" with Settings' `AddApi`, and a model picker when a server exists but Characters has none), 2 Make yourself (name, portrait, one line: a persona set as current; "Skip: I direct the story"), 3 Add your first friend (the same compact form, then "Start a story with Pell" opens New chat and dives); the privacy line and Continue / Skip / Go home. `App.tsx`: `#/` is Home (classic at `#/classic`; unknown routes fall back to Home); the gate sends every route but welcome, settings, classic and dev to `#/welcome` while no provider exists, re-asking on each route until one does and trusting only an answer for the current route; the dive overlay (`dive()` / `diveLink()` in hooks: two cloud layers, one mirrored, fade in, scale to 1.2 and part while the scene's dark rises over 900 ms, then the page changes under it and the overlay fades; reduced motion: a 200 ms crossfade) on the rail orb, Home's Continue and Chats' still (all into classic until task 20). Electron: 1440×900 capped to the work area, background `#c3dafc`. Also: dialogs keyed by counters get distinct key prefixes (Places rendered two siblings keyed `0`). Verified: typecheck, build, smoke PASS (the dev library, with no model, opens on First run); shot of `#/` on an empty library = First run matching `Sky-FirstRun.html` (fake model on :8080, checked free before and after, detected as "llama.cpp on this computer · fake"); walk on a fresh empty library: `#/home` redirects to welcome, Use this connects, Rowan becomes the persona, Pell the first friend, "Start a story with Pell" (as Rowan) dives to `#/chats/1` (an earlier walk bounced back to welcome on a stale gate answer; fixed as above), Home then greets Rowan with Pell's story; the pane runs with reduced motion (the quick path ran); forcing full motion in the page sampled the clouds from scale .95 to 1.2 and parted with the dark at 1 before landing; a sweep of all 18 routes on the demo copy lit the right rail item with no console errors · deviations: new stories still land in Chats and Dive in opens classic until the Scene exists (task 20)
- 2026-09-19 · task 16 · migration 4 (`messages.audience`, JSON: NULL everyone present, a list a whisper, `[]` a thought); `chat.audience_of`; the rule lives in `chat.heard_by` (said it, or present and in the audience), so every caller follows it; `audience` threads through `_insert` / `add_child` / `append_message` (a swipe keeps it), `turns.turn(..., audience=)` and `TurnIn.audience` (ids outside the story → 422). The four gaps: the recall cue is the last two lines the speaker heard; `select_speaker` picks among those who heard the pending line (named first, then the last speaker), and the quietest present character when nobody heard it; the memory reader's transcript marks "(whispering to Mira)" / "(thinking; no one hears)" and the applier caps who can learn a memory to those the line reached (the asserter still knows); the narrator's history drops thoughts and renders a whisper as "Aren whispers to Mira.", while a listener sees "Aren (whispering to Mira): …". Speaker guard: asking for someone not in the scene yields "Tobin isn't in the scene. Bring them in first." before anything is written. Verified: ruff, format, 267 tests (`tests/test_hearing.py`: whisper heard only by its listener, a thought in no prompt including the narrator's, whisper content out of Tobin's and the narrator's prompts, replies from hearers and the quietest after a thought, a whispered claim never reaches Tobin though the reader lists him, the reader's markers, the absent-speaker refusal with no line and no model call, the recall cue; plus the 422 and stored audience over HTTP, and the v4 migration); `demo.py build` check ok; llama-server not running, so no live_eval · deviations: listeners also see the whisper marker (not in 2.3, but it tells Mira the line was private); no existing test asserted the old behaviour
- 2026-09-19 · task 17 · `turns.say(conn, story, text, audience, skip)` writes the user's line (skip = what the line says plus what `skip` says, both read by `clock.parse_skip`) or, with no text, a marker ("— Six years later —") carrying the skip, and never calls a model; `turn()` goes through it, so Pass time then Continue is `TurnIn.skip`. `POST /stories/{id}/line` → 201 with the messages, 422 when there is neither text nor skip or the skip can't be read, pokes the worker. `meta` gains `skip` (the parent's), `from_clock`, `clock` (the reply's) and `strained` (any recalled memory rolled an effortful recall); `gen.think_ms` is first thought to first token; the messages payload gains `audience` and `think_ms`. `demo.py` writes its six-years marker with `turns.say`. Verified: ruff, format, 274 tests (pass time then continue, a skip in the user's own line in meta, strained via a rolled recall, think_ms; over HTTP a line with no reply, the skip-only marker and the unreadable skip, a thought's audience `[]`); `demo.py build` check ok; llama-server not running, so no live_eval · deviations: an unreadable skip is refused (422 / an error event) rather than written as a zero-minute marker
- 2026-09-19 · task 18 · migration 5 (`presence.run_id`, cascading with its run): the applier stamps the presence it finds, so a reread (which discards the old run) no longer duplicates it. `chat.presence_changes(conn, story, path)` walks the path from each scene's opening roster and keeps only rows that change who is there, with `found` when a reader wrote it. `GET …/cast` entities gain `lib_item_id` and the response gains `changes` (+ `clock`, the line's); `DELETE /presence/{id}` → the cast (Undo, 404 when gone); `SceneIn.skip` via a shared `turns.read_skip` (also used by `say`; 422 when unreadable) and `chat.new_scene(..., skip_minutes)` on the marker; `GET /stories/{id}/version` → `{v: "max:runs:ok:busy", waiting}`; runs carry `filed` (memories the run wrote). Verified: ruff, format, 278 tests (only real transitions with clocks and Undo, a scene after the next morning and the unreadable skip, two rereads leave one presence row stamped with the latest run and `filed` 1, `v` and `waiting` before and after a read, the v5 migration) · deviations: a scene's opening roster is not listed as a change (the scene marker already says who is there)
- 2026-09-19 · task 19 · `scene/Scene.tsx` (`#/story/:id`, `#/story/:id/line/:mid`, outside the Sky frame): one guarded `useLoad` of story, messages and cast as `refreshAll`; `usePoll` on `/version` every 3 s refreshes when `v` moves; the top bar (cloud → `rise()`, which plays the dive backwards over the sky to `lastSky`, the last Sky page App saw; italic title + "with Mira · as Aren" / "alone" / "directing"; the place + clock pill with `SunArc`; a menu with "Open in classic view"); opens at the newest line or centres and flashes the deep-linked one, else "That line is no longer in this version of the story." `scene/Stage.tsx`: `Room` by `minute_of_day`, up to three `Figure`s (the last speaker lit in front, others `.is-softened`; slots by count in vw), an avatar row beyond three, the vignette. `scene/Lines.tsx`: lines with speaker ink (the persona `--k-speaker-aren`, others their palette ink), stamps HH:MM or "Year 7 · 19:18" / "Day 3 · 08:10" when the year or day changed since the last line (as in `Scene-AfterSkip.html`), marks (edited, stopped, thought, "whispered to Mira"), hidden lines dimmed; title cards for the opening, scene cuts and skips ("Six years later · Year 7" + Undo: `skip_minutes: 0`, and `hidden` too for a skip-only marker); notes from `cast.changes` ("Tobin joins · Brought in by you · Day 1, 19:04"). `art.tsx` `SunArc`; API types for task 18 (`lib_item_id`, `changes`, `filed`, `Version`, meta fields). Verified: typecheck, build, smoke PASS; shot of the demo story at 1440×900 vs `Scene-OneToOne.html` (top bar, pill, stage figure placement and the conversation column match; the art is stand-ins by design); walk on the demo: line 7 centred and flashed, stamps and cards right, line 999 gives the notice, Undo on the skip removed the card and moved the top-bar clock back to Day 1, 19:22 (demo rebuilt after), the cloud rose to `#/chats`, 16 version polls, no console errors after a reload · deviations: tray, composer, receipts, Backstage and reading-mode buttons and the sound pill come with their own tasks (the conversation keeps the composer's 304 px); the opening card names the place only while the story has no scene cuts (the first scene's place isn't in the payload); relighting is a variable swap, not yet the 600 ms two-layer crossfade (task 35); `.k-convo` is flex-start with an auto top margin so long stories scroll
- 2026-09-19 · task 20 · `scene/Composer.tsx`: row 1 says who hears (avatars + "Only Mira will hear this" / "Mira and Tobin will hear this" / "No one is here to hear this", a greyed "Tobin is away"; Whisper swaps in a picker of who hears, preselecting a lone listener; Think says "No one will hear this"), then a pending time chip (×), the Pass time menu (a few hours, the next morning, a week, N years; phrases `clock.parse_skip` reads) and Continue; the Newsreader textarea ("Speak or act as Aren…" / "Direct the story…", Enter sends, Shift+Enter a new line); Say / Do (wraps `*…*`) / Whisper (`audience`) / Think (`POST /line` with `audience: []`, no reply); Send or Stop + "Stopping keeps what Mira has written so far."; Who answers (Whoever fits, a chip per present character, Narrator); the meter (`--used` = est ÷ budget from `GET /context`, then each `meta`; tooltip and aria-label "~590 / 16,384 tokens · 2 memories recalled"). `Scene.tsx` lifecycle (1.6): the optimistic line at once, `live` from the stream (meta: speaker, strained, clock; thoughts; tokens; `thinkMs` first thought → first word), the 400 ms wait after Stop, unmounting aborts, `settling` clears live and said in a layout effect when fresh data lands (no doubled reply for a frame), version polling paused while live; only text with nothing said (or a thought) goes to `/line`. `Lines.tsx`: `LiveLine` ("Mira is thinking…" / "is trying to remember…" with dots and "Her notes stay backstage · read them"; then the stamp, "writing…", Prose with the caret via a new `tail` prop, "Thought for N s"), `SaidLine`, and the Thought chip on saved lines with `think_ms`. Every Dive in goes to `#/story/:id` (rail orb: the story played last; Home, Chats, new chats from Chats/Places/Profile/First run). Also: the conversation no longer scrolls sideways (the lines' −14 px margins), thin scrollbar. Verified: typecheck, build, smoke PASS; walk on the demo with `serve-model --think --delay 0.15`: send (thinking row, then the reply; textarea cleared), Stop mid-reply kept "*turns the mug" marked stopped with its Thought chip, Continue added a reply with no line, Whisper → "whispered to Mira", Think → "thought" with only `/line` posted (no `/turn`), Pass time 6 years → chip, "Six years later · Year 13" card, clock Year 7 → Year 13; every dive href is `#/story/4`; shots (headless Chrome over CDP, `--delay 0.6`) of thinking and streaming vs `Scene-Reply-Thinking.html` / `Scene-Reply-Streaming.html` match in structure and copy; demo rebuilt after · deviations: "read them" and the Thought chip open the notes inline until Backstage (task 23); Pass time and Continue are disabled while a reply is written; the optimistic line has no stamp; a story with no prompt yet 404s `GET /context` (logged by the browser, handled)
- 2026-09-19 · task 21 · `Lines.tsx` `Line`: the tools pill (`.k-line__tools`, hover and focus-within) with takes `‹ i/n ›` (swipe via `POST /swipe`; on the newest reply the last arrow is "New take", streamed through the Scene's `generate('/regenerate')` with the replaced reply hidden meanwhile), inline Edit (focused textarea, Save / Cancel, Ctrl+Enter saves, Esc cancels; `PATCH text`) and Hide / Unhide (`PATCH hidden`, a "hidden" mark); every change calls `refreshAll`, so the header clock and cast follow. `Scene.tsx` `StoryMenu`: Rename…, Minutes per turn…, Pin / Unpin, Open in classic view, Delete story… (confirm; then floats up to Chats); forms mount fresh per open. Reading mode (book button, `aria-pressed`): `.is-reading` fades the top bar (back on pointer move for 2.5 s, hover or focus), a veil fades in over the stage, which blurs statically, and the conversation and composer centre and widen; Esc leaves. Dark scene dialogs. `ui.tsx` `Dialog` now focuses the first field after `showModal` (it was landing on the close button). Verified: typecheck, build, smoke PASS; walk on the demo with the fake model: New take (1/1 → 2/2), Tobin back and a line on take 2 (19:26, "with Tobin and Mira", two figures), swipe back (19:22, "with Mira", one figure) and forward (19:26, both again), Edit → "edited", Hide → `.is-hidden` + "hidden", Unhide, reading mode (column centred at the viewport middle, top bar opacity 0, stage `blur(10px)`), Esc out, Rename, Minutes per turn 5, Unpin, Delete on another story (floated to `#/chats`, gone from `/stories`); CDP shots of the hover pill, the dark dialog and reading mode; demo rebuilt after · deviations: the pin toggle reports errors nowhere (it has no dialog); a hidden line's tools still show on hover, so it can be unhidden
- 2026-09-19 · task 22 · `scene/Nearby.tsx` (new): the tray (`.k-tray`, "Nearby"): story characters who are away ("away · since Day 1", from their last departure in `cast.changes`) then library friends not in the story ("could join", favourites first), four rows, each a button and a drag source; "Bring someone in" opens a picker of everyone; the tray is the drop target for sending someone away; `NewScene` ("Where to?"): a filmstrip of story and library places (`Room` thumbnails), who is there (present people and the persona to start), an optional title, and When (Straight after, `SKIPS`, Years later… with a count) → `POST /scene` (the engine's 422 shows in the dialog). `Stage.tsx`: the drop target for bringing in (`application/x-kataki-person`, `Moving` in hooks), figures drag off to the tray, a "Send Tobin away" button on hover or focus (the button equivalent), and the arrival: `.is-entering` plus a name card ("Tobin joins" + the first line of their description, ink ring) for 3 s; whoever arrives stands in front. `Scene.tsx`: `move()` (friend → `POST /cast`; away/here → `POST /presence`), New scene… in the story menu, and the cut through black (600 ms: the POST, then black, the refresh at 300 ms under it). `Lines.tsx` notes: "Tobin joins · Brought in by you · he hears everything from here on · Undo", "Tobin left. He won't hear what's said now." with a greyscale avatar, "Noticed in the story" for reader-found ones, Undo on all (`DELETE /presence/{id}`). `SKIPS` moved to `api.ts` for the composer and the dialog. Verified: typecheck, build, smoke PASS; walk on the demo: click Tobin in (name card, `.is-entering`, in front, the join note, the card gone after 3 s), Send Tobin away (the left note), Undo (back), drag Ilsa from the tray onto the stage (joins the story, name card "A mountain guide who never loses a trail."), drag her figure to the tray (away), New scene → The Lighthouse, the next morning (black cut, "13 hours later · 08:00" and "The Lighthouse · Year 7, Day 2, 08:00", the pill follows); CDP shots of the secret (via `#/story/4/line/10`) and of Tobin joining vs `Scene-Group-Secret.html` / `Scene-Group-Joins.html` match in structure and copy; demo rebuilt after · deviations: no ghost of an absent character on the stage and no "at the bar" note (the mockup's, not in this task); departures leave without an animation (the design's `k-step-out` animates `filter`, which 1.7 rules out); the persona is a "who is there" chip in the dialog
- 2026-09-19 · task 23 · `scene/Backstage.tsx` (new), behind the top bar's Backstage `.k-switch` (`role=switch`); the scene stays mounted and hidden underneath, so a draft or a reply in progress survives, and the conversation re-scrolls on return. Memory (820 of 1392): a character per tab (AI first, then the persona), clarity filters with counts, `.k-bs-row`s (tier; the text, hazy rows with the gist and a struck "was sharp: …", the story time via a TS copy of `clock.label`; how learned + "doubted" + recall A; `.k-importance` + "importance N"; Pin / Hide), "Pinned facts sit in every prompt.", Write a memory (text, importance, who knows or everyone, keep in every prompt). Prompt: "~590 / 16,384 tokens", counted and cache reuse, the `.k-tokenbar` by part with a legend against each cap, "recalled N · A text (pinned)", "cut: 8 old lines" (evicted sections and dropped memories), the full prompt in a dialog. Cast (`GET /entities`, which already carries `lib_item_id`, now typed): portrait or kind icon, persona/kind, current flags (or the summary), other names, "found"; "these two are the same" → a keep / fold in dialog (`POST /entities/merge`). Reading: a waiting row from `/version`, runs with a status dot, trigger in words, attempts, filed and skipped counts, errors, stale; a run is picked by clicking; "Read what is waiting now" and "Read #N again carefully". The Scene's poll now keys on `v` and `waiting` and bumps a `tick` that Backstage reloads on. Verified: typecheck, build, smoke PASS; shot of the demo vs `Scene-Backstage.html` (layout, panels, columns, copy match; fixed the design's `.k-backstage button { font-family: inherit }` beating `.k-bs-btn`'s mono, and `pin` → `pushpin`); walk: Pin (pressed, "Unpin"), write "Mira owes the guild forty silver." (6 → 7 rows, input cleared), forgotten filter, merge the ledger into The Gull (its names move over), a line via `/line` then "waiting · 2 new lines" (in a visible page; the pane is hidden, so its poll rightly pauses), Read what is waiting now (run #4); demo rebuilt after · deviations: no "branch · take" label (no branch names in the payload; the title says "as she would recall it now, with no reminder"); no "faded Year 7" (no fade time); recall shows A as the engine reports it, not a 0–1 probability (Pass 3 brings clarity); the reader's model line has no thinking on/off
- 2026-09-19 · task 24 · parity walk of the brief's "Reference: what the app does today", each line found in the new UI · **Library**: characters in the friend editor's six steps (name + portrait + pronouns; "Who they are" = description; "Their secret" = private, "Only Mira knows…"; "How they talk" = example dialogue; "How they say hi" = opening line; other names and tags; walked on Mira), places and plots in Places (name; "What anyone there can see"; "Premise: every character knows this"; "Opening narration"; other names; tags; the place dialog walked), a story's copy and safe delete (engine, task 3) · **New story**: New chat (title, friends the AI plays, "You play" with "No one: I direct the story", Where, Plot, time of day; walked) · **In a story**: send with Enter, Continue, Who answers (Whoever fits, a character, Narrator), Stop keeping the partial (task 20 walk); takes, edit, hide (21); skip title cards with Undo (19); the Thought chip for reasoning models (20); the token meter "~590 / 16,384 tokens · 2 memories recalled" (20); presence: the tray, send away, "Tobin left. He won't hear what's said now." (22); someone joins from the library (22); cut to a new scene with place, title, who is there (22); delete the story (21) · **Inspector → Backstage** (23): Memory (tier, "told by Aren", "doubted", importance, recall, Pin with "Pinned facts sit in every prompt", Hide, Write a memory with importance 1–10, who knows or "Everyone knows it", "keep it in every prompt"), Prompt (estimated and counted tokens, cache reuse, parts against limits, what was cut, recalled with scores, the full prompt), Cast (kinds incl. items, "found", other names, current state, "these two are the same"), Reading (status, trigger, job and model, attempts, stale, errors, skipped, "Read what is waiting now", "Read again carefully") · **Models** (Settings, task 14; this walk saw "Look for model servers on this computer", "Add an API", the five jobs with "Same as Characters"): Test, Remove, "key stored", presets, per job server/inherit, model, kind with "Detect now", context size, thinking, room to think, effort, sampler presets (Balanced, Balanced + DRY, Creative + XTC, Focused) and the JSON box · **Status**: Settings › About "engine ok · v0.0.1 · schema 5", "engine unreachable" when down. Then deleted `app/src/classic/` (7 files, 1,400 lines), the `#/classic` route and its gate entries, and "Open in classic view" from the story menu; unknown routes (`#/classic` included) show Home with Home lit on the rail. Verified: typecheck, build, smoke PASS; walk: `#/classic` → Home lit, the story menu without classic · no deviations
- 2026-09-19 · task 25 · migration 6 (`memories.message_id`, `memories.contradicts_id`; `message_id` backfilled from `to_message_id` for read memories, left NULL for written ones). The applier stores the exact line (`where["id"]`; from/to keep the run's range) and the first contradicted memory that is live on the run's branch (`Applier.live`, `is_live`). Clarity: `retrieve.CLARITY_CUE` (S 0.5, G 1.0, no noise) in `retrieve.inspect(conn, story, knower, *, now=None)`, which counts only knowledge learned by `now` (default: the active leaf's time) as well as accesses up to it; replies keep the real cue. Backstage's note now reads "As each memory would come back if it came up now." Verified: ruff, format, 288 tests (the exact line and the run range; `contradicts_id`; the tier table: importance 5 sharp fresh, hazy at 60 days and 3 years, forgotten at 5; importance 9 hazy at 6 years; importance 2 forgotten at 6 years; a lie told just now is sharp; `inspect(now=before)` leaves out what Mira was told later; the v6 migration and backfill); `demo.py build` check ok (Mira in Year 7: the rehearsed ledger memories sharp, Day 1 trivia forgotten, the lighthouse lie contradicting memory 4); llama-server not running, so no live_eval · no deviations
- 2026-09-19 · task 26 · `signals.py` (new) and `GET /stories/{id}/signals` → `{read_to, lines: {id: {summary, receipts, recall}}}`. One hearing rule: `chat.hearing(conn, path, entity)` labels each line said / heard / away / whisper / thought, and `heard_by` is now built on it. Receipts (AI characters; not on hidden or system lines): heard + `pending` until a live run covers the line (`read_to` = the furthest live run), then the best clarity (task 25's `inspect`) of the memories anchored to that line which they know, else plain heard; `absent` (`why` away or whisper) only on your lines, and only for someone who had heard something in the scene since the last skip of a day or more (so no one is absent before they ever joined; a thought has no receipts). `summary`: "Mira will remember · Tobin wasn't there", "… remembers it vaguely", "… has forgotten", "Heard by …", "… didn't hear". Recall (from the reply's `context_log` row; only when something rendered was hazy, strained for or importance ≥ 7): up to 3 items (spark-worthy first) with `tier`, `text` (gist when hazy), `detail`, `how` from the speaker's knowledge ("witnessed Day 1, 08:02", "told by Aren …"), and the title "Mira remembered, clearly / vaguely / after straining". Verified: ruff, format, 293 tests (`tests/test_signals.py`: pending → sharp after the read with the summary, Tobin absent on the secret only, a whisper's `why`, a thought without receipts, nobody absent before joining, recall on the reply six years later; one HTTP test); the demo story takes 3 ms (the secret line "Mira will remember · Tobin wasn't there", Day 1 trivia forgotten, 19:18 "Mira remembered, vaguely", 19:22 "after straining") · deviations: the speaker gets a receipt on their own line (the mockups show "Heard by Mira" under Mira's lines); summary wordings beyond the spec's example are mine
- 2026-09-19 · task 27 · `signals.py` gains a `Scene` of shared facts (AI cast, names, hearing, clarity, live runs; pronouns from the library item's `data.pronouns`, "you" for the persona), callouts and skip reports. Callouts: memory (importance ≥ 7, not a claim, known sharp or hazy; the most important per line; `faded` when nobody is sharp; "Mira and Tobin will remember this"); belief (a claim on your line with `is_true = 0`, per hearer by belief: "Mira knows that's not true" / "Mira has her doubts" / "Mira believed you"; reason from the clarity of `contradicts_id`: "Mira remembers it clearly: “…”", "Her memory of it has gone hazy, so she can be talked out of it.", "Mira has no memory of it."); feeling (a live edge from an AI character, on the line of the same read's latest memory involving both, else the read's last line; trust / distrust-suspicious / dislike-resent-annoyed-angry-hate / like-fond-grateful-warm wordings by prefix, "no longer" when ended, the note as the reason). Skip report per present AI character: of what they knew before the skip, sharp→hazy and →forgotten counts, measured a minute before the skip line's time (a reply right after the skip logs its recall at that time; that rehearsal isn't the skip's doing), `from_clock` the line before, "2 of Mira's memories are going hazy. 3 are fading out." `demo.check()` now also requires the secret line's memory callout, "Tobin didn't like that" at 19:08, "Mira has her doubts" at 19:20, the spark at 19:18 and the skip report. Verified: ruff, format, 299 tests (after six years importance 2 forgotten, importance 9 hazy with a faded callout; the three belief wordings with the sharp reason; a feeling on the shared line and one on the read's last line; skip counts and clocks); `demo.py build` check ok (6 ms for the demo story); llama-server not running, so no live_eval · deviations: the test world gives its characters pronouns (the wording follows them: a `they` character "has their doubts"); a skip with nothing lost says "Nothing has faded."
- 2026-09-19 · task 28 · The Scene loads `/signals` with story, messages and cast, and with `/version`, whose value becomes the poll's baseline (the poll used to take its baseline on its first tick, so a read landing within 3 s of opening was never noticed: found in this walk). `Lines.tsx`: under each line `Receipts` (16 px faces `.k-receipt.is-heard/-sharp/-hazy/-absent`, absent as a dashed initial; a face that forgets fades out and leaves after 1.2 s, one already forgotten never shows; the engine's summary; pending dots), replaced on hover or focus by `.k-receipt-chip`s ("Mira heard · will remember", "Tobin wasn't there"); `CalloutChip`s (`.k-callout`, `--belief` / `--feeling`, `.is-faded`, the speaker's face, an icon, the reason below); the `.k-spark` in the head opens the `.k-recall` card on hover, focus or click ("MIRA REMEMBERED, VAGUELY", each item with `.k-clarity[data-level]` and "hazy · witnessed Day 1, 19:12 · once sharp: “…”"). The optimistic line gets instant heard faces for whoever it reaches. Receipt transitions: 600 ms box-shadow to sharp, 1.2 s opacity to hazy; the design's filter transition is dropped (1.7). `demo.py serve-model` now answers memory reads with the demo's reader (`read_memory`) instead of "nothing new", so walks can light receipts. Verified: typecheck, build, smoke PASS; engine checks (299) and `demo.py build` check ok; CDP shots vs `Scene-Group-Secret.html` (hovered secret line: both chips, "Mira will remember this", "Mira trusts you a little more" with its reason) and `Scene-AfterSkip.html` (the spark and the recall card; "Mira has her doubts" with "Mira remembers it clearly: “…”" on the lie line) match in structure and copy; walk in a visible page: a new line "the ledger is under the third floorboard" showed "Heard by Mira" with dots, then after a read "Mira will remember" with a lit face and its callouts, one signals refetch; demo rebuilt after · deviations: the belief callout sits on your lie line (the engine's anchor), where the after-skip mockup puts it under Mira's reply; box-shadow still transitions on the 16 px faces (spec'd 600 ms), only filter is dropped

---

## 1. App architecture

### 1.1 Files in `app/src` (few, focused)
| File | Holds |
|---|---|
| `main.tsx` | Boot. Imports CSS in order: `design/tokens.css`, `design/components.css`, `design/fonts/fonts.css`, `app.css`. Injects the icon sprite once. Renders `<App/>`. |
| `api.ts` | Keep `connection`, `api()`, `failure()`, `stream()`. Dev fallback moves from the URL hash to **query params** (`?port=&token=`), because the hash now belongs to the router. Add `upload(blob)`, `mediaUrl(name)` (`…/media/<name>?token=`), and complete the payload types (Message.scene_id/audience/think_ms; ContextLog message_id, speaker_id and per-memory `rendered/A_detail/effortful/tokens`; KnownMemory `A_detail/B/story_time`; typed `Item.data` flags; SSE event payloads). |
| `hooks.tsx` | `useLoad` (race-guarded with a sequence ref; same `[data, reload, error]` shape), `useAction`, `usePoll(fn, ms, enabled)` (skips while the document is hidden), the router (`parse`, `href`, `go`, `useRoute`), `LibraryContext`/`useLibrary()`. |
| `ui.tsx` | `Icon` (`<svg class="k-icon"><use href="#i-name"/></svg>`, aria-hidden), `Candy`, `Chip`, `Seg` (aria-pressed), `Glass` (`.k-card`), `Dialog` (native `<dialog>` + `showModal`, Esc closes, focus returns), `Menu` (`popovertarget` + `popover`), `Field`, `Tier` (`.k-tier` / `.k-bs-tier`), `ErrorLine`, `Prose` (`*em*`, `**strong**`, paragraphs; add `white-space: pre-line`), `SkyHeader`. |
| `art.tsx` | `PALETTES`, `paletteOf`, `pronounsOf`, `initials`, `timeOfDay`; `Avatar`, `AvatarStack`, `Portrait` (+ nameplate), `Figure` (stage), `Room` (place stand-in), `SunArc`, `Orb`. |
| `App.tsx` | Health check (sets `document.documentElement.dataset.engine = 'ok' / 'down'`), first-run gate, route switch, Sky frame and rail, dive overlay, remembers the last Sky route. |
| `sky/*.tsx` | `Friends`, `Editor` (add/edit a friend or persona), `Profile`, `Chats`, `NewChat` (dialog), `Home`, `Places`, `You`, `Settings`, `FirstRun`, `Activity`. |
| `scene/*.tsx` | `Scene` (data, streaming, polling, top bar, tray, time skip), `Lines` (lines, title cards, notes, receipts, callouts, recall), `Composer`, `Stage` (layers, figures, peek), `Backstage`. |
| `design/` | Vendored copies (never edited): `tokens.css`, `components.css`, `sprite.svg`, `clouds.svg`, `fonts/` (`fonts.css` + 6 `.ttf` + licence texts), `README.md` (provenance). |
| `app.css` | The app layer (`ka-` classes). It turns the design's fixed 1440 px positions into layouts that hold from 1280 to 1920 px. |
| `classic/` | Temporary (removed in task 24): the old `App` as `Classic.tsx`, `Story`, `Inspector`, `Library`, `Stories`, `Models`, and `classic.css` (the old `styles.css` with every selector scoped under `.classic`). |

### 1.2 Vendoring
- CSS: `tokens.css` and `components.css` copied verbatim, imported globally.
- Fonts: the files sit next to `fonts.css`, so its relative `url()` resolves and Vite bundles them
  (`base: './'` keeps `file://` working). Fix the header comment: Chewy is Apache 2.0, the others OFL.
- Sprite: `import sprite from './design/sprite.svg?raw'` and `document.body.insertAdjacentHTML('afterbegin', sprite)` once.
- Clouds: `import clouds from './design/clouds.svg'` (a URL for `<img>`).
- Never use root-absolute asset paths: they break under `file://`.

### 1.3 Router (hash, about 50 lines)
| Hash | Screen |
|---|---|
| `#/` | Classic until task 15, then Home |
| `#/home` · `#/friends` · `#/friends/new` · `#/friend/:id` · `#/friend/:id/edit?step=n` | Home, Friends, editor, profile |
| `#/you` · `#/you/:id` · `#/you/new` | Your persona, one persona, new persona |
| `#/chats` · `#/chats/:id` | Threads, selected thread |
| `#/places` · `#/activity` · `#/settings` · `#/settings/about` · `#/welcome` | Places and Plots, Activity (Pass 3), Models, About, First run |
| `#/story/:id` · `#/story/:id/line/:mid` | Scene; the deep link scrolls to the line and flashes it. If the line is off the active branch: "That line is no longer in this version of the story." |
| `#/classic…` · `#/dev/kit` | Old UI and the design kit check page (both temporary) |

- The Scene's cloud button returns to the last Sky route.
- Gate: with no provider, every route except welcome, settings and classic goes to `#/welcome`.

### 1.4 Data
- `LibraryContext`: every library item, loaded once and reloaded after any library edit. The engine
  returns `lib_item_id` on entities; the UI resolves portrait, palette and pronouns from it.
- The current persona is `settings.persona` (a library id, or null for Director), stored with the
  existing `GET/PUT /settings`.
- `PATCH /library/{id}` replaces `data` whole, so the UI always sends `{...item.data, ...changes}`.

### 1.5 Art and light
- **Palette:** stored at creation in `data.palette = {bg:[from,to], ink}`, taking the least-used
  entry. Entities with no library item (found by the reader) hash their name onto the list. In a
  scene the persona's lines always use `--k-speaker-aren` #a9c8ff.

  | # | backdrop (160deg) | ink |
  |---|---|---|
  | 1 | #c4ece4 → #6fb7c9 | #f2b870 |
  | 2 | #ffe3bf → #f2a468 | #e8cc6a |
  | 3 | #f8d8ec → #c3a0ea | #f0a58a |
  | 4 | #dbf2d4 → #8cc79a | #e2c48c |
  | 5 | #fff3bf → #f4c35a | #f5b98a |
  | 6 | #f6ccd2 → #c77886 | #eeb4a0 |
  | 7 | #d3e3ff → #7ea4f0 | #e9c08f |
  | 8 | #e4f0ff → #b9b3f2 | #f2c98a |

- **Stand-ins:**
  - avatar and portrait: up to 2 initials (Figtree 800, white) on the backdrop gradient
  - stage figure: an inline SVG head-and-shoulders silhouette, filled with the darkened backdrop, with an ink-coloured rim light
  - place: `Room`, a CSS lit room (wall gradient, a window whose sky follows the time of day, lamp glow, floor)
- **Uploads:** `data.portrait` (characters and personas) and `data.image` (places) hold media names.
  - Avatar and portrait images: `object-fit: cover; object-position: 50% 22%`.
  - Stage figure: the image with a radial `mask-image`, so its edges melt into the room.
  - Place image: `object-fit: cover` plus a time-of-day tint layer.
- **Time of day** from `minute_of_day`: dawn 05:00–07:59, day 08:00–16:59, dusk 17:00–19:59, night 20:00–04:59.
  - `Room[data-tod]` swaps CSS variables.
  - Relighting crossfades two stacked layers over 600 ms (opacity only).
  - `SunArc`: the dashed 44×24 arc. The sun is placed by the clock from 06:00 to 18:00, the moon over the night half.
- **New chat time of day** sets `epoch_offset_min`: Dawn 360, Day 720, Dusk 1140, Night 1320.

### 1.6 Scene state flow
- **State:** `story`, `messages`, `cast` (Pass 2); `signals`, `people` (Pass 3).
  `live = {speaker, text, thoughts, strained, t0, thinkMs} | null`. `said` is the optimistic line.
- **`refreshAll()`:** one sequence-guarded `Promise.all` of story, messages, cast (+ signals). Every
  mutation calls it. This fixes today's stale header clock and cast after a swipe or undo.
- **`generate()`** (one at a time; Send is disabled while `live`):
  - Keep the abort ref, abort-aware errors, and the **400 ms wait after Stop** (the engine saves the partial reply).
  - Unmounting aborts the stream (fixes today's leak).
  - `meta` sets the speaker and the meter, and plays the time skip if `meta.skip ≥ 1440`.
- **Background reads:** while the Scene is visible, `usePoll` hits `GET /stories/{id}/version` every
  3 s. When `v` changes, refetch signals and cast, plus runs if Backstage is open.
- **Seen marker:** `POST /stories/{id}/seen` on mount and on unmount (Pass 3).

### 1.7 Motion and GPU rules (the model shares an 8 GB GPU)
- Animate only `transform` and `opacity`. Never animate `filter` or `backdrop-filter`. Glass only on static layers.
- The only endless loops are the orb's breathing, the thinking dots and the caret.
- **Dive (900 ms):** two `clouds.svg` layers (one mirrored) scale to 1.2 and part while the sky fades. The stage enters from opacity 0 at scale 1.02. The UI fades in last.
- **Leaving a scene** floats up (the reverse).
- **Reduced motion:** 200 ms crossfades only.
- **Time skip:** crossfade to a statically blurred copy of the stage.
- `content-visibility: auto` on conversation lines.

---

## 2. Engine additions (tests first; new code in `media.py` and `signals.py`, the rest in existing modules)

Migrations are additive entries in `db.MIGRATIONS`, bumping `SCHEMA_VERSION` (use the next free
number if tasks move). Each one extends the migration test in `tests/test_db.py`. JSON goes in
`TEXT` columns. Reuse `chat.heard_by`, `retrieve.inspect`/`_assess`, `db.live_runs`/`live_filter`,
`library.*` and `context_log`.

| Task | Routes | Change |
|---|---|---|
| 3 | `POST /media` · `GET /media/{name}?token=` · safe `DELETE /library/{id}` | Media store; library data flags; premise snapshot |
| 4 | `GET/POST/PATCH /stories…` · `POST /stories/{id}/seen` | Summaries, time fields, pinned, seen. Migration 3 |
| 16 | `POST …/turn` (+`audience`) | Whisper/Think; hearing gaps; speaker guard. Migration 4 |
| 17 | `POST /stories/{id}/line` · `…/turn` (+`skip`) · `meta` | Line without a reply, pass time, meta fields, `think_ms` |
| 18 | `GET …/cast` · `DELETE /presence/{id}` · `POST …/scene` (+`skip`) · `GET …/version` · runs `filed` | Scene support. Migration 5 |
| 25 | `GET …/memories?knower=` | Exact line, contradiction link, clarity. Migration 6 |
| 26–27 | `GET /stories/{id}/signals` | Receipts, recall, callouts, skip reports |
| 30 | `GET /activity` · `GET /stories` (+`new_events`, `waiting`) | Activity feed |
| 32 | `GET /stories/{id}/people` · `GET /library/{id}/profile` | Peek, living profile, "Who knows you" |

### 2.1 Media and library (task 3)
- **`POST /media`** (raw body) → `201 {"name":"<sha256>.png","bytes":48211}`.
  - Format by magic bytes: PNG `\x89PNG\r\n\x1a\n`, JPEG `\xff\xd8\xff`, `GIF87a`/`GIF89a`, WebP `RIFF????WEBP`.
  - Anything else, SVG included: `415` "Only PNG, JPEG, GIF or WebP images." Over 10 MiB: `413`.
  - Stored at `<folder of the library db>/blobs/<name>` (folder from `PRAGMA database_list`), via a temp file and `os.replace`. Identical bytes get the same name.
  - `ponytail:` no sweep of unreferenced blobs.
- **`GET /media/{name}`:**
  - `404` unless the name matches `^[0-9a-f]{64}\.(png|jpg|gif|webp)$` and the file exists.
  - Headers: `Content-Type` from the extension, `Cache-Control: private, max-age=31536000, immutable`, `X-Content-Type-Options: nosniff`.
  - Auth: `require_token` also accepts `?token=` **only** for paths under `/media/`.
- **Library `data` keys** (documented in `library.py`, opaque to the engine):
  - `persona: bool`, `favourite: bool`, `pronouns: "she"|"he"|"they"` (default they)
  - `palette: {bg:[a,b], ink}`, `portrait` / `image` (media names)
  - existing: `aliases`, `first_message`, `example_dialogue`
- **Safe delete** (one transaction):
  - Stories using the item as their scenario get its description copied into `stories.overrides.premise`, and `scenario_id` becomes NULL.
  - `entities.lib_item_id` becomes NULL where it pointed at the item.
  - Then the item is deleted. This fixes today's 500.
- **Premise snapshot:** `create_story` copies the scenario description into `overrides.premise`, and `context._system` reads it first, falling back to the live row. (The brief: "editing the library never rewrites a story in progress".)
- **Tests:**
  - PNG round trip with the query token; the same name for the same bytes.
  - SVG, HTML and text give 415; oversize gives 413.
  - Bad names and traversal give 404; `?token=` elsewhere still gives 401.
  - The file lands under `blobs/`.
  - Deleting a character that a story uses gives 204, and the story keeps its copy.
  - Editing or deleting a scenario leaves the story's premise unchanged.

### 2.2 Stories for the Sky (task 4, migration 3: `stories.pinned INTEGER NOT NULL DEFAULT 0`, `stories.seen_run_id INTEGER NOT NULL DEFAULT 0`)
- **`POST /stories`** accepts `epoch_offset_min` (default 480).
- **`PATCH /stories/{id}`** accepts `pinned`.
- **`POST /stories/{id}/seen`** → 204 and sets `seen_run_id` to the story's newest run id.
- **`GET /stories`:** pinned first, then newest message first. Each entry:
  ```json
  {"id":12,"title":"The Third Floorboard","created_at":"…","last_at":"…","messages":14,"pinned":true,
   "clock":"Year 7, Day 1, 19:22","minute_of_day":1162,
   "persona":{"id":31,"name":"Aren","lib_item_id":3},"place":{"id":33,"name":"The Gull","lib_item_id":8},
   "cast":[{"id":29,"name":"Mira","lib_item_id":1,"present":true}],
   "last_line":{"speaker":"Mira","text":"*frowns* The lighthouse? I could have sworn…"}}
  ```
  - `cast` = AI characters, with presence in the current scene.
  - `last_line` = the last visible non-system line on the active path.
- **`GET /stories/{id}`** adds `pinned`, `persona`, `place`, `scene_title`, `story_time`, `minute_of_day`, `epoch_offset_min`, and `start_clock` (the label at time 0, for the opening title card).
- **Tests:** shape and order, pinning, `minute_of_day` for a 19:00 epoch, `seen`, a "Day 2" epoch labels correctly.

### 2.3 Whisper, Think and hearing (task 16, migration 4: `messages.audience TEXT`, a JSON list of entity ids; NULL = everyone present, `[]` = a thought)
- **Threading:** `audience` goes through `chat._insert` / `add_child` / `append_message` (and `append_sibling` copies it), `TurnIn.audience` (ids must belong to the story, else 422) and `turns.turn(..., audience=None)`.
- **Rule** (in `chat.heard_by`, so every caller gets it): a line reaches an entity if they said it, or if they are present and (`audience` is NULL or they are in it).
- **The four gaps:**
  1. **Recall cue:** the last two lines *the speaker heard* (not the raw `path[-2:]`).
  2. **`select_speaker`:** chooses among present AI characters who heard the pending line, for both addressed-by-name and the fallback. If nobody heard it (a thought), it uses the quietest present character.
  3. **Extraction:**
     - Transcript lines are marked `(whispering to Mira)` / `(thinking; no one hears)`.
     - The applier caps the model's participants/heard_by to those who were there (`there_for(line)`); the asserter always knows. The model can no longer hand a secret to someone absent.
  4. **Narrator:** its history leaves out thoughts and renders a whisper as "Aren whispers to Mira." with no content.
- **Speaker guard:** a requested int speaker who is not present gets, before anything is written, `("error", {"message": "Tobin isn't in the scene. Bring them in first."})`.
- **Tests:**
  - A whisper is heard only by the chosen character.
  - A thought reaches no prompt, the narrator's included.
  - Whisper content is absent from Tobin's and the narrator's prompts.
  - The speaker is chosen among hearers.
  - A whispered claim never reaches Tobin even when the model lists him.
  - An absent speaker gets an error and no new line.
  - If an existing test asserts the old leaky behaviour, change it and explain in the commit.

### 2.4 Lines without a reply, pass time, meta (task 17)
- **`turns.say(conn, story_id, text, audience, skip)`** is shared by `turn()` and `/line`.
  - It appends the persona's line (director mode: speaker NULL) with skip = `parse_skip(text) + parse_skip(skip)`.
  - With no text but a skip, it appends a system marker such as "— The next morning —" that carries the skip.
- **`POST /stories/{id}/line {text?, audience?, skip?}`** → `201` with the messages list; `422` if neither is given. It pokes the worker and never calls the model.
- **`TurnIn.skip`** uses the same path, so Pass time followed by Continue works.
- **`meta`** gains `skip`, `from_clock`, `clock`, and `strained` (an effortful recall roll happened).
- **`gen.think_ms`** = time from the first thought to the first token. The messages payload gains `audience` and `think_ms`.
- **Tests:**
  - `/line` makes no model request.
  - A skip-only request writes the marker, and the clock moves by six years.
  - `meta.skip` is 3,153,600 for "six years later".
  - `strained` is set when a pressed hazy memory rolls.
  - `think_ms` is recorded.

### 2.5 Scene support (task 18, migration 5: `presence.run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE`)
- The applier sets `run_id` on the presence rows it writes, so a reread no longer duplicates reader-found presence (today's bug).
- **`chat.presence_changes(conn, story_id, path)`:** the arrivals and departures that actually change who is there, in order.
- **`GET …/cast`:** entities gain `lib_item_id`, and the response gains `"changes":[{"id","message_id","entity_id","present","found","clock"}]` (`found` = inferred by the reader).
- **`DELETE /presence/{id}`** → the cast (Undo). `SceneIn.skip` gives a new scene a time skip.
- **`GET /stories/{id}/version`** → `{"v":"<max run id>:<runs>:<ok>:<pending+running>","waiting":<len(extract.pending)>}`.
- **Runs** gain `filed`: memories written by the run.
- **Tests:** rereading twice leaves one presence row; changes list only real transitions; Undo; `v` changes after a run; `filed`.

### 2.6 Exact line and clarity (task 25, migration 6)
- **Migration:**
  ```sql
  ALTER TABLE memories ADD COLUMN message_id INTEGER;
  ALTER TABLE memories ADD COLUMN contradicts_id INTEGER;
  UPDATE memories SET message_id = to_message_id WHERE run_id IS NOT NULL;
  ```
- The applier stores the exact line (`where["id"]`) and the first contradicted live memory. `from_message_id`/`to_message_id` keep the run range.
- **Clarity**, one definition used on every screen: the tier a memory would have for this character *if it came up* at story time T.
  - `retrieve.inspect(conn, story_id, knower_id, *, now=None)` scores with `CLARITY_CUE`: S = 0.5, G = 1.0, no noise.
  - It counts only knowledge learned by T and accesses up to T. T defaults to the active leaf.
  - Replies keep using the real cue of the moment.
  - Resulting behaviour:
    - importance 5: fresh is sharp, hazy after about a month, forgotten after about four years
    - importance 9: hazy after six years
    - importance 2: gone after six years
    - a lie told just now is sharp
  - Backstage Memory uses clarity, with the note "As each memory would come back if it came up now."
- **Tests:** the exact line; `contradicts_id`; the tier table above; `inspect(now=before)` excludes later knowledge.

### 2.7 Signals: `GET /stories/{id}/signals` (tasks 26–27, `signals.py`)
**Response shape:**
```json
{"read_to":350,"lines":{"345":{
  "summary":"Mira will remember · Tobin wasn't there",
  "receipts":[{"id":29,"state":"sharp"},{"id":30,"state":"absent","why":"away"}],
  "callouts":[{"kind":"memory","who":[29],"text":"Mira will remember this","reason":null,"faded":false,"memory_id":88}],
  "recall":{"speaker":29,"title":"Mira remembered, vaguely","items":[{"memory_id":88,"tier":"hazy","text":"Aren hid the guild ledger somewhere behind the bar.","how":"witnessed Day 1, 19:12","detail":"…under the third floorboard…"}]},
  "skip":{"minutes":3153600,"from_clock":"Day 1, 19:14","to_clock":"Year 7, Day 1, 19:16","faded":[{"id":29,"hazy":12,"gone":3}],"text":"12 of Mira's memories are going hazy. 3 are fading out."}}}}
```

**Receipts** (AI characters only; none on hidden or system lines):
- `heard` + `pending` until a live run covers the line (the lag rule keeps the newest reply pending).
- Then the best clarity among the memories anchored to that line which they know: `sharp` / `hazy` / `forgotten` (the UI drops forgotten faces). If nothing is anchored, it stays `heard` without the dots.
- `absent`, only on the persona's lines: the character didn't hear it but heard an earlier line in the same scene since the last skip of a day or more. `why` is `away`, or `whisper`.
- The engine writes the quiet `summary` sentence.

**Callouts** (the engine writes the text; pronouns from `data.pronouns`; "you" = the persona):
- **memory:**
  - When: importance ≥ 7, not a claim, known at sharp or hazy clarity.
  - One per line, the most important. `faded` when nobody is sharp.
  - Text: "Mira will remember this" / "Mira and Tobin will remember this".
- **belief:** a claim on your line with `is_true = 0`, one per hearer.
  - Text by belief: below 0.3 "Mira knows that's not true"; below 0.7 "Mira has her doubts"; otherwise "Mira believed you".
  - Reason, from the clarity of `contradicts_id`:
    - sharp: "Mira remembers it clearly: “{detail}”"
    - hazy: "Her memory of it has gone hazy, so she can be talked out of it."
    - none: "Mira has no memory of it."
- **feeling:** a live edge from an AI character. It anchors to the same run's latest memory involving both, otherwise to the run's last line.
  - trust: "Mira trusts you a little more"
  - distrust or suspicious: "Tobin is suspicious of you"
  - dislike, resent, annoyed, angry or hate: "Tobin didn't like that"
  - like, fond, grateful or warm: "Mira warmed to you"
  - ended: "X no longer {rel} Y"; anything else: "X {rel} Y"
  - The edge note becomes the reason.

**Recall:**
- From the `context_log` row of that reply.
- A spark shows when a recalled, rendered memory is hazy, effortful, or importance ≥ 7.
- Up to 3 items. `how` comes from the speaker's knowledge row.
- Title: "…remembered, clearly" / "…vaguely" / "…after straining".

**Skip report:**
- For lines that skip a day or more, per present AI character: clarity at `story_time − skip` versus `story_time`, over memories learned before the skip.
- `hazy` counts sharp→hazy; `gone` counts →forgotten. Plurals are correct.
- `ponytail:` recomputed per request; batch the queries if the demo takes over 150 ms.

**Tests** (`tests/test_signals.py`, a small ledger scene):
- pending → sharp after the read
- Tobin absent on the secret only; a whisper gives `why: whisper`
- after six years: importance 2 forgotten; importance 9 hazy, with a faded callout
- the three belief wordings
- a feeling anchored to the shared line
- recall on the reply after the skip
- skip report counts
- one HTTP test

### 2.8 Activity (task 30)
- **`GET /activity?story_id=&kind=&limit=100`**, newest first:
  ```json
  [{"key":"m88","kind":"memory","story_id":12,"story":"The Third Floorboard","message_id":345,"clock":"Day 1, 19:12",
    "who":[{"id":29,"name":"Mira","lib_item_id":1}],
    "text":"Mira will remember that Aren hid the guild ledger somewhere behind the bar.",
    "sub":"Heard by Mira · Tobin wasn't there","line":{"speaker":"Aren","text":"Quickly, while he's gone…"},"new":true}]
  ```
- Kinds: memory (from callouts), belief, feeling, time ("Six years passed in The Third Floorboard. 12 of Mira's memories went hazy.").
- `new` = `run_id > seen_run_id` (time events are never new).
- `GET /stories` gains `new_events` and `waiting`.
- **Tests:** order, filters, `new` flips after `/seen`, texts.

### 2.9 People and profiles (task 32)
- **`GET /stories/{id}/people`**, one entry per AI character:
  ```json
  {"id":29,"name":"Mira","lib_item_id":1,"present":true,"since":"Day 1, 19:10","where":"The Gull",
   "state":[{"key":"holding","value":"a mug she hasn't touched","private":false}],
   "on_mind":{"tier":"hazy","text":"The ledger is somewhere behind the bar."},
   "about_you":{"count":38,"sharp":23,"hazy":12,"forgotten":3,"samples":[{"memory_id":91,"tier":"sharp","text":"…","belief":0.5}]},
   "remembers":41,"relationships":[{"rel":"trusts","other_id":31,"other":"Aren","you":true,"since":"Day 1"}],
   "secret":"She reads every letter she carries."}
  ```
  - `about_you` = memories linked to or asserted by the persona. It is null in director mode.
- **`GET /library/{id}/profile`:**
  - `stories`: role `ai` carries the `person` entry above; role `persona` carries `known_by: [{id, name, lib_item_id, count, sharp, hazy, forgotten}]`.
  - `places`: where they have been.
- **Tests** for both routes against the ledger scene.

---

## 3. Tasks

"**Standard app check**" = `corepack pnpm -C app typecheck` + `corepack pnpm -C app build` + `corepack pnpm -C app smoke`.

"**Shot**" = headless-Chrome screenshots of the app route and of the named mockup at the same size. Read both and compare layout, hierarchy and copy; the art differs by design. Fix gaps or note them.

"**Walk**" = the built-in browser pane (navigate, find, clicks, get_page_text, javascript_tool). Its screenshots time out on this machine.

### Pass 0: set-up
**1. File the handoff and this plan.**
- `.gitignore`: add `docs/*.zip`.
- `.gitattributes`: add `*.ttf binary`, `*.woff2 binary`, `*.gif binary`, `*.webp binary`.
- Root `package.json`: nested scripts call `corepack pnpm …`, so `corepack pnpm check` works despite the broken global pnpm shim.
- Copy this plan to `docs/specs/2026-09-19-ui-redesign.md` and add a pointer line to the master spec's Progress.
- Back up `.dev/library.db` → `.dev/library.pre-ui.db`.
- Commit `docs/kataki-design/**`, `docs/design-brief.md`, the plan and the config.
- Verify: `git status` is clean; `git show --stat HEAD` has no zip.

**2. Design base layer and foundation.**
- **Vendor** as in 1.2.
- **Fonts:** download from the official google/fonts repo and check each `.ttf` starts with `00 01 00 00` and is over 20 KB.
  ```
  G=https://raw.githubusercontent.com/google/fonts/main; D=D:/OpenRolePlayAI/app/src/design/fonts
  curl -fL -o $D/Chewy-Regular.ttf              $G/apache/chewy/Chewy-Regular.ttf                  # 41 KB
  curl -fL -o $D/LICENSE-Chewy.txt              $G/apache/chewy/LICENSE.txt
  curl -fL -o $D/Figtree-Variable.ttf           "$G/ofl/figtree/Figtree%5Bwght%5D.ttf"               # 63 KB
  curl -fL -o $D/Figtree-Italic-Variable.ttf    "$G/ofl/figtree/Figtree-Italic%5Bwght%5D.ttf"        # 63 KB
  curl -fL -o $D/OFL-Figtree.txt                $G/ofl/figtree/OFL.txt
  curl -fL -o $D/Newsreader-Variable.ttf        "$G/ofl/newsreader/Newsreader%5Bopsz%2Cwght%5D.ttf"  # 452 KB
  curl -fL -o $D/Newsreader-Italic-Variable.ttf "$G/ofl/newsreader/Newsreader-Italic%5Bopsz%2Cwght%5D.ttf"  # 496 KB
  curl -fL -o $D/OFL-Newsreader.txt             $G/ofl/newsreader/OFL.txt
  curl -fL -o $D/JetBrainsMono-Variable.ttf     "$G/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"   # 187 KB
  curl -fL -o $D/OFL-JetBrainsMono.txt          $G/ofl/jetbrainsmono/OFL.txt
  ```
- **Classic:** `git mv` the old screens into `classic/` (App → `Classic.tsx`). Scope `styles.css` → `classic/classic.css` under `.classic`, by hand.
- **Foundation:** `api.ts` (query params, upload, types), `hooks.tsx`, `ui.tsx`, `main.tsx`.
- **New `App.tsx`:**
  - sets `data-engine`
  - `#/` and `#/classic*` render `<div class="classic"><Classic/></div>`
  - `#/dev/kit` shows the 4 fonts, all 66 icons, buttons, chips, candy tiles, the orb and a glass card
- **Electron:** the smoke check waits for `document.documentElement.dataset.engine === 'ok'` (15 s) and still prints `SMOKE PASS/FAIL`.
- **README:** the `?port=&token=` dev URL.
- Done when: classic works as before and the kit renders.
- Verify:
  - Standard app check; fonts land in `dist/assets`.
  - Shot `#/dev/kit` against `design-system/components.html`.
  - Walk: 66 `<symbol>`s; `document.fonts.check` is true for all four families; the classic Library opens.

### Pass 1: engine for the Sky, demo, Sky screens
**3. Engine: media and library (2.1).** Files: new `media.py`; `server.py`, `library.py`, `context.py`; tests. Verify: engine checks.

**4. Engine: stories for the Sky (2.2), migration 3.** Files: `db.py`, `library.py`, `server.py`; tests. Verify: engine checks.

**5. Demo library and fake model.** `engine/evals/demo.py`:
- **`build [--db ../.dev/demo.db] [--model-url …]`**
  - Rebuilds deterministically through the real code paths (`library.*`, `turns.turn`, `extract.run_due`, `chat.set_presence`).
  - Uses an in-process scripted `httpx2.MockTransport` (a copy of the test FakeBackend), `embed.builtin = lambda: None` and `get_key=lambda _: None`.
- **Library:** personas Aren and Sable; friends Mira (every field from the brief), Tobin, Ilsa, Master Oren, Wren (partial); places The Gull, The Lighthouse, Harbour Market; plots "The Missing Ledger" and "Frost on the Pass".
- **"The Third Floorboard"** (pinned; as Aren at The Gull; epoch 1140), following the brief's sample conversation:
  - Mira greets; Tobin joins; Aren asks Tobin to fetch a round; Tobin is sent away; the secret at 19:12.
  - Mira at 19:14 says "ledger", so the recall after the skip is certain.
  - Run 1 files the memories:
    - the arrival (importance 4); the green apron (2); sent to the bar (3); the secret (9)
    - the ledger as an item
    - edges Tobin→Aren "resents" and Mira→Aren "trusts"
    - Mira's holding/wearing flags
  - "Six years later"; Mira at Year 7 19:18 (run 2 reads the past first); the lie at 19:20; Mira at 19:22; run 3 files the claim with a doubted contradiction.
- **Other stories:** "Frost on the Pass" (Ilsa, as Sable, epoch 1840), "The Clockmaker's Debt" (Oren, as Aren), "Letters for the Guild" (Mira, as Sable).
- **`check()`** exits non-zero, naming what is missing:
  - the clock reads Year 7, Day 1, 19:22; 3 ok runs
  - Mira knows the secret and Tobin doesn't
  - the 19:18 context_log rendered the ledger memory
  - the skip marker is at Year 7, Day 1, 19:16
- **`serve-model [--port 8099] [--delay 0.08] [--think]`:** a stdlib `ThreadingHTTPServer` with `/v1/models` (`fake`) and `/v1/chat/completions`.
  - Streaming: optional `reasoning_content`, then canned lines word by word.
  - Non-streaming: `"{}"`.
- **Electron:** `KATAKI_DB` overrides the dev database. README: demo commands.
- Verify: engine checks (ruff covers `evals/`); two `build` runs print identical summaries; `curl` streams from the fake model.

**6. Sky shell and Friends.** Files: `App.tsx`, `hooks.tsx` (LibraryContext), `art.tsx` (palettes, pronouns, initials, Avatar, AvatarStack, Portrait, Orb), `sky/Friends.tsx`, `app.css`.
- Shell: `.k-sky` with static clouds; `.k-rail` with logo, the items that exist so far, Settings, and the orb "Dive in" (latest story; classic for now).
- `#/friends` candy filters: All, Favourites, In a story, New (≤ 7 days), Groups (a story with ≥ 2 AI characters).
- Friend cards: portrait, heart (`data.favourite`), name, tagline (the description's first line, else "Just added. Finish their profile."), status ("At The Gull · Year 7" / "Left The Gull · Day 1" / "Not in a story yet").
- Verify: standard app check; shot vs the Friends section of `Sky-Home.html` (1440×1190); walk: filters and heart persist.

**7. Chats.** Files: `sky/Chats.tsx`; `art.tsx` gains `Room`, `Figure`, `SunArc`.
- Thread list:
  - filters: All / One-to-one / Groups; sections Pinned and All stories
  - each row: stacked avatars, title, pin, story clock, last line, "as Aren"
  - row menu: Pin/Unpin, Delete (confirm dialog)
- Preview: a Room + Figure last-moment composition, the Dive in orb, "In this story" (On stage / Away), and "Start a fresh story with X".
- Verify: standard app check; shot vs `Sky-Chats.html`; walk: select, pin, delete.

**8. New chat dialog.** `sky/NewChat.tsx`:
- Fields: friends (one, or several for a group scene), place, plot, time of day, "You play" (defaults to `settings.persona`; "No one: I direct the story"), title (default "Mira at The Gull" or the plot name).
- Presets come from callers. `POST /stories`, then dive in.
- Entry points: Chats "New chat" / "New group scene", "Start a fresh story".
- Verify: standard app check; walk: create a story and it opens.

**9. Add a friend / edit.** `sky/Editor.tsx`:
- Six `.k-step` steps, saved as you go:
  1. name and portrait (upload), pronouns, favourite, "This is me" (persona)
  2. who they are
  3. their secret
  4. how they talk
  5. how they say hi
  6. other names and tags
- "Stuck? Start from" prompt chips per step.
- A live profile card with a completeness ring (filled steps ÷ 6) and a nudge ("Add a secret to make Wren more real").
- The palette is auto-assigned. Delete (confirm; safe delete).
- Routes: `#/friends/new`, `#/friend/:id/edit`, `#/you/new`. The "Add a friend" button and card appear from here on.
- Verify: standard app check; shot vs `Sky-AddFriend.html`; walk: create Wren, upload a PNG, step through, reload and it persists.

**10. Friend profile (static parts).** `sky/Profile.tsx` (`#/friend/:id`):
- Big portrait with name plate, status and tags.
- Actions: "Message Mira" (latest story with her, else New chat preset), "Start a new story", "Start a group scene", "Edit profile".
- Stat tile: "N stories together".
- Cards: About, Also known as, How she talks (bubbles from example dialogue), How she says hi, Secret (blurred, "Reveal as author"), Stories together.
- Verify: standard app check; shot vs `Sky-Profile-Mira.html` (1440×1500).

**11. Home and persona switcher.** `sky/Home.tsx`:
- Header:
  - greeting by local time ("Good evening, Aren")
  - avatar opening the switcher popover: personas with a tick, "Director · Play no one", "+ New persona", and the footnote "Each chat keeps the persona it started with…"; writes `settings.persona`
  - search that filters friends, chats and places
  - "Add a friend"
- Continue card: Room + Figure, scrim, title, place · clock · persona, last line, orb "Dive back in".
- The Friends grid (bell and activity arrive in task 31).
- Verify: standard app check; shot vs `Sky-Home.html` (1440×1190); walk: switch persona, and New chat defaults to it.

**12. Places and Plots.** `sky/Places.tsx`:
- Place cards: image or Room at dusk; "Start a scene here".
- Plot cards: premise and opening narration; "Start this plot".
- Add and edit dialogs:
  - place: name, description, other names, tags, image
  - plot: name, premise ("every character knows this"), opening narration, tags
- Verify: standard app check; walk: add a place with an image and start a scene there.

**13. You.** `sky/You.tsx`:
- "You are playing": the persona profile with a "Played by you" badge, Edit, and that persona's chats.
- "Who are you in new chats?" list: switcher semantics, Director, New persona.
- "Who knows Aren" arrives in task 34.
- Verify: standard app check; shot vs `Sky-You.html`.

**14. Settings: Models and About.** `sky/Settings.tsx` ports every field of `classic/Models.tsx`:
- Subnav: Models, About.
- Server cards:
  - candy tile, host in mono
  - status from an auto-test on mount: "connected"/"unreachable", "{model} loaded", "key stored"
  - Test, Remove (confirm)
  - "Change key" via the existing `PATCH /providers/{id}`
- "Look for model servers on this computer" (detected rows disappear once added); "Add an API" dialog with presets.
- Job cards: collapsed ("Same as Characters" / model + detail line), or expanded with every field (server, model, context size, thinking, room to think, effort, kind, Detect now, sampler presets, JSON box). The embed row keeps "Built-in".
- About: "engine ok · v · schema".
- Verify: standard app check; shot vs `Sky-Models.html` (1440×1000); walk: add the fake provider, set Characters, Detect now.

**15. First run, flip, dive.** Files: `sky/FirstRun.tsx`, `App.tsx`, `app.css`, `electron/main.ts`.
- `#/welcome`, in three steps:
  1. Connect a model: detect, "Use this" (adds the provider and sets `rp`), "Look again", "Add an API".
  2. Make yourself: name, portrait, one line (creates a persona and sets it current).
  3. Add your first friend: the compact editor, then New chat, then dive.
- Privacy line: "Everything runs on your computer. Text only leaves it for the models you connect."
- Gate. `#/` becomes Home (classic at `#/classic`).
- Dive overlay (1.7) on every Dive in (classic story for now).
- Electron window 1440×900 capped to the work area, `backgroundColor '#c3dafc'`.
- Verify: standard app check (a fresh `.dev` library shows welcome); shot vs `Sky-FirstRun.html`; walk the whole Sky on the demo library.

### Pass 2: Scene and Backstage
**16. Engine: audience and hearing (2.3), migration 4.** Verify: engine checks. Run `live_eval` only if llama-server is already up.

**17. Engine: lines, pass time, meta (2.4).** Also switch `demo.py` to `turns.say` for the six-years marker. Verify: engine checks; `demo.py build`.

**18. Engine: scene support (2.5), migration 5.** Verify: engine checks.

**19. Scene frame (read-only).** `scene/Scene.tsx`, `Stage.tsx`, `Lines.tsx`, `app.css`; `#/story/:id`.
- **Stage:**
  - Room or place image by time of day
  - up to 3 Figures: one-to-one large (about 44vw); the speaker lit in front, others `.is-softened`; an avatar row beyond 3
  - vignette
- **Top bar:** cloud (floats up to the last Sky route); title + "with Mira · as Aren"; place + clock pill with SunArc; menu with "Open in classic view" (temporary).
- **Conversation (`.k-convo`):**
  - Lines: speaker ink, HH:MM stamp (full label on a new day or year), Prose, marks (edited, stopped, "whispered to Mira", "thought").
  - Title cards: the opening "The Gull · Day 1, 19:00", scene markers, and skips as "{duration} later · Year 7" with Undo (`PATCH skip_minutes: 0`; skip-only markers are also hidden).
  - System notes from `cast.changes`.
- `refreshAll()`, version polling, line deep links.
- Verify: standard app check; shot of the demo story vs `Scene-OneToOne.html`; walk a deep link.

**20. Composer and streaming.** `scene/Composer.tsx`; the lifecycle in 1.6.
- **Row 1:**
  - who hears: avatars + "Only Mira will hear this" / "Mira and Tobin will hear this"; a greyed "Tobin is away"
  - Whisper → a picker of who hears; Think → "No one will hear this"
  - on the right: Pass time menu (a few hours, next morning, a week, "N years"), shown as a pending chip and sent as `skip`; Continue
- **Textarea:** Newsreader 18; "Speak or act as Aren…" / "Direct the story…"; Enter sends, Shift+Enter adds a new line.
- **Modes:**
  - Say
  - Do (wraps in `*…*`)
  - Whisper (`audience`)
  - Think (`POST /line` with `audience: []`, no reply)
- **Send / Stop**, plus "Stopping keeps what Mira has written so far."
- **Who answers:** Whoever fits, one chip per present character, Narrator.
- **Token meter:** `--used` from `meta.context`, initial value from `GET /context`. Its tooltip and aria-label give "~7,300 / 16,384 tokens · 3 memories recalled".
- **Live states:**
  - "Mira is thinking…" (dots) + "Her notes stay backstage · read them"
  - "Mira is trying to remember…" when `strained`
  - streaming text with `.k-caret` and the stamp "writing…"
  - a "Thought for N s" chip that opens the notes
- The optimistic line appears instantly. Every Dive in now goes to `#/story/:id`.
- Verify:
  - Standard app check.
  - Demo with `serve-model --think --delay 0.15`.
  - Walk: send, Stop mid-reply (the partial is kept), Continue, Whisper, Think (no model request), pass time "6 years".
  - Shots vs `Scene-Reply-Thinking.html` and `Scene-Reply-Streaming.html`.

**21. Line tools, story menu, reading mode.**
- Tools pill (`.k-line__tools`, on hover and focus-within):
  - takes `‹ i/n ›`; the last arrow on the newest reply makes a new take via `/regenerate`
  - inline Edit
  - Hide/Unhide (`.is-hidden`)
- Story menu: rename, minutes per turn, pin, delete story (confirm).
- Reading mode: `.k-scene.is-reading` (tray and top bar fade; the column widens over a statically blurred stage).
- Verify: standard app check; walk: swipe both ways (the header clock and cast update), edit, hide, delete.

**22. Presence and new scene.**
- **Tray "Nearby":**
  - away story characters ("away · since Day 1") and library friends not in the story ("could join")
  - "Bring someone in"
  - drag onto or off the stage (HTML5 DnD), with button equivalents
- **Arrival:** figure `.is-entering` + a name card for 3 s ("Tobin joins", tagline).
- **Notes:**
  - "Tobin joins · Brought in by you · he hears everything from here on · Undo"
  - "Tobin left. He won't hear what's said now." (greyscale avatar)
  - reader-found changes also get Undo (`DELETE /presence`)
- **New scene dialog:** "Where to?" filmstrip of story and library places, who is there, title, optional "later" skip; cut through black (600 ms).
- Verify: standard app check; shots vs `Scene-Group-Joins.html` and `Scene-Group-Secret.html`; walk: bring Tobin in, send him away, Undo, cut to The Lighthouse.

**23. Backstage lens.** `scene/Backstage.tsx`: the top-bar `.k-switch` swaps the stage, conversation and composer for `.k-backstage` panels (Memory about 820 px on the left; Prompt, Cast and Reading stacked on the right).
- **Memory:**
  - character tabs; tier filters with counts
  - `.k-bs-row` columns:
    - tier
    - text + story time (hazy rows add the struck "was sharp: …")
    - how learned + "doubted" + recall A
    - `.k-importance`
    - Pin/Hide
  - footer "Pinned facts sit in every prompt"; the Write a memory form
- **Prompt:**
  - "~7,300 / 16,384 tokens", counted tokens and cache reuse
  - `.k-tokenbar` with a legend of each part against its limit
  - recalled memories with scores, what was cut, and a "full prompt" dialog
- **Cast:** kind, current flags, "found", aliases, merge.
- **Reading:**
  - runs with status dot, trigger, job + model, attempts, filed/skipped counts, stale, errors
  - "Read what is waiting now", "Read again carefully"
- Verify: standard app check; shot vs `Scene-Backstage.html`; walk: pin, write a memory, merge, read now.

**24. Retire classic.** Walk every line of the brief's "Reference: what the app does today" in the new UI and record the result in the Progress note. Then delete `classic/`, its routes and links. Verify: standard app check.

### Pass 3: memory signals
**25. Engine: exact line and clarity (2.6), migration 6.** Update the Backstage note copy. Verify: engine checks; `demo.py build`.

**26. Engine: signals I (receipts, recall, route; 2.7).** Verify: engine checks.

**27. Engine: signals II (callouts, skip reports; 2.7).** Extend `demo.check()`:
- the secret line has the memory callout
- 19:08 has "Tobin didn't like that"
- 19:20 has "Mira has her doubts"
- 19:18 has the spark
- the skip report exists

Verify: engine checks; the demo check passes.

**28. UI: receipts, callouts, spark.** `scene/Lines.tsx`:
- **Receipts:**
  - the `.k-receipts` row with the engine's summary
  - 16 px faces `.k-receipt.is-heard|is-sharp|is-hazy|is-absent`; forgotten faces fade out and are removed; pending dots
  - `.k-receipt-chip` chips on hover
  - instant `heard` for the optimistic line
  - transitions: 600 ms to sharp, 1.2 s to hazy
- **Callouts:** `.k-callout` (`--feeling`, `--belief`, `.is-faded`) with the reason below.
- **Spark:** `.k-spark`; on hover or focus, the `.k-recall` card with `.k-clarity[data-level]` and "hazy · witnessed Day 1, 19:12 · once sharp: “…”".
- Refetch on version change.
- Verify: standard app check; shots vs `Scene-Group-Secret.html` and `Scene-AfterSkip.html`; walk: a new line goes from heard (dots) to lit once `v` changes.

**29. UI: time-skip sequence.**
- Trigger: `meta.skip ≥ 1440`, or `done.skip_minutes`.
- The `.k-timeskip` overlay (≥ 1800 ms):
  - "Six years later" (Newsreader italic 76)
  - the old clock struck through → the new clock
  - the report pill ("12 of Mira's memories are going hazy. 3 are fading out.")
  - "Undo the time skip"
- Then: the clock rolls, the Room relights by crossfade, and receipts animate on refetch. Reduced motion: a crossfade.
- Verify: standard app check; shots vs `Scene-TimeSkip.html` and `Scene-AfterSkip.html` (fake model, pass time "6 years").

**30. Engine: activity (2.8).** The demo marks the story seen after run 1, so "new" events exist. Verify: engine checks; the demo check passes.

**31. UI: Activity and badges.**
- `sky/Activity.tsx` (`#/activity`; the rail item is added):
  - groups by story and year ("THE THIRD FLOORBOARD · YEAR 7"), kind filters, `.k-event--memory|feeling|belief|time`
  - an item expands to the quoted line and "Open the line" (deep link)
  - side cards: "Still being read" (`waiting`, Read now) and "How receipts fade"
- Home: activity preview (3), bell `.k-badge-count`, the Continue chip "N new memory events".
- Chats: memory badge and "New since you left".
- The Scene posts `/seen` on mount and unmount.
- Verify: standard app check; shots vs `Sky-Activity.html`, `Sky-Home.html`, `Sky-Chats.html`.

**32. Engine: people and profiles (2.9).** Verify: engine checks.

**33. UI: peek card and "In this story".**
- Clicking a figure or avatar opens `.k-peek`:
  - avatar, name, "role · present"
  - Right now: Holding, Wearing, Where, Injury, other flags
  - On her mind (tier + text)
  - What she knows about you (count, 2 samples with tiers, a link to Backstage Memory)
  - relationship chips; the secret with Reveal
- Actions: "Let her answer next" (sets Who answers), "Send away" / "Bring back", "Edit".
- No expression chip (M3).
- Chats "In this story": "On stage · remembers 38 things about you".
- Verify: standard app check; shot vs `Scene-Peek.html`.

**34. UI: living profile and "Who knows you".**
- Profile stat tiles:
  - "N stories together" / "as Aren and as Sable"
  - "Remembers N things" / "about Aren"
  - "Last seen: The Gull" / "Year 7, Day 1, 19:22"
- "Right now" with the "In {story} ▾" selector:
  - rows: Last seen, Holding, Wearing, Feels about you
  - memory bar: sharp solid, hazy striped, forgotten as the remainder
- Also: Relationships per story, Stories together, Places she's been.
- You: "Who knows Aren" (per character per story, with the hazy count).
- Verify: standard app check; shots vs `Sky-Profile-Mira.html` and `Sky-You.html`.

### Pass 4: polish
**35. Responsive and motion.**
- Shots of every screen at 1280×800, 1440×900 and 1920×1080.
- At 1280 the figure shrinks and the column moves left. At 1920 the stage grows and the column stays ≤ 600 px.
- Reduced-motion audit (headless Chrome `--force-prefers-reduced-motion`). Audit the GPU rules (1.7).

**36. Accessibility and keyboard.**
- Real buttons, links and labels; visible focus in all three worlds; 44 px targets.
- `aria-label` on icon buttons; `aria-current` on the rail and steps; `aria-pressed` on chips and segmented controls; `role=tablist` for Backstage tabs; `aria-live=polite` on the streaming line.
- Esc/Enter in dialogs. Walk the whole app by keyboard.

**37. Empty and error states** (the design leaves these open; use its language):
- no friends yet (an invitation to "Add a friend")
- a story not started: "The story has not started. Say something, or press Continue."
- model server unreachable: an inline card with "Check Models"
- engine unreachable: a full-screen glass card with Retry
- a shimmer only for loads over 300 ms

**38. Cleanup, docs, final verification.** Remove the kit route, dead code and unused `app.css`. Update the README (screens, demo, fake model, dev URL) and the Progress sections of both specs. Then run the final verification in section 6.

---

## 4. Loop protocol (one task per iteration)

**Tools and servers**
```
UV=C:/Users/user/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe/uv.exe
PY=D:/OpenRolePlayAI/engine/.venv/Scripts/python.exe
engine checks:  cd D:/OpenRolePlayAI/engine && "$UV" run ruff check . && "$UV" run ruff format --check . && "$UV" run pytest -q
demo:           cd D:/OpenRolePlayAI/engine && "$UV" run python evals/demo.py build --db ../.dev/demo.db
background (run_in_background, stop with TaskStop when done):
  "$PY" D:/OpenRolePlayAI/engine/evals/demo.py serve-model --port 8099
  KATAKI_TOKEN=dev KATAKI_HOME=D:/OpenRolePlayAI/.dev "$PY" -m kataki serve --db D:/OpenRolePlayAI/.dev/demo.db --port 8765
  corepack pnpm -C D:/OpenRolePlayAI/app exec vite --port 5173 --strictPort
screenshot:     "C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --hide-scrollbars --window-size=1440,900 --virtual-time-budget=5000 --screenshot=D:/OpenRolePlayAI/.dev/shots/<name>.png "http://localhost:5173/?port=8765&token=dev#/<route>"
mockups:        file:///D:/OpenRolePlayAI/docs/kataki-design/kataki-design/screens/html/<Name>.html
```

**Each iteration**
1. **Orient.** Run `git status --short` and `git log --oneline -5`, and read Progress, Blocked and the notes.
   - Uncommitted changes that belong to the next task: continue that task.
   - Anything else unexpected: stop and report.
   - Never `reset --hard` or `checkout --` work you did not make.
2. **Pick** the first unchecked task whose dependencies are done. If it will clearly exceed about 800 changed lines (excluding vendored, binary and deleted files), split it into a/b in Progress and do only a.
3. **Read** the task, its mockup (HTML text plus a shot), the relevant `DESIGN-SYSTEM.md` section, and the code it touches.
4. **Build.**
   - Engine: failing test first, then the code.
   - App: build on the design classes; new classes go only in `app.css` (`ka-`).
   - Use the Edit/Write tools for any text containing backslashes (Bash heredocs here collapse them).
   - Use `corepack pnpm`, never bare `pnpm`.
5. **Verify** exactly as the task says, and fix until green.
   - Never weaken a test to pass.
   - If an existing test asserts old buggy behaviour, change it and explain in the commit.
   - Keep the effect-cleanup rule: never return `scrollIntoView()` from an effect.
6. **Record:** tick the box and add the note line, in the same commit.
7. **Commit locally.**
   - `git add <paths>`. Never `-A`, and never anything from `.dev/`, `dist/` or `blobs/`.
   - Message: `feat(app|engine): …`, a 2-5 line body, and the final line `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
   - Never push, amend, or use `--no-verify`.
8. **Clean up:** stop every background process this iteration started.
9. **Report** in three lines: the task, how it was verified, the next task.

**Blockers.**
- After two honest attempts at the same failure, mark the task `[!] blocked: …` under Blocked and continue with the next task that doesn't depend on it.
- If this plan doesn't answer a product question, take the simplest option consistent with `DESIGN-SYSTEM.md` and note it.
- If the answer would change memory, presence or story semantics, stop and ask the user.

**Stop** when task 38's final verification passes. Also stop if every remaining task depends on a blocked one; report the blocker and the question for the user.

---

## 5. Risks and containment
| Risk | Containment |
|---|---|
| The app breaks mid-rebuild | Classic stays whole (its CSS scoped under `.classic`) until task 24's parity walk. Every task ends with the standard app check green. |
| Scope creep in the Scene | The cut list in Context. One concern per task, capped at about 800 lines. New ideas go under "Later". |
| The GPU is shared with the model | The rules in 1.7. Polling is one cheap SQL query every 3 s, only while the Scene is visible. Audited in task 35. |
| The smoke check is flaky | It watches the `data-engine` attribute, not visible text. |
| Hearing changes cause memory regressions | Tests first. The rule lives in `chat.heard_by` for every caller. The full suite runs each time. |
| Signal wording and cost | The engine writes the sentences, so pytest pins them. Recomputed only when the version changes; 150 ms budget. |
| Migrations on real libraries | Additive `ALTER`s plus one backfill, each tested. The loop only opens `.dev/*.db`. The backup is `.dev/library.pre-ui.db`. |
| Tokens in URLs | Only the dev query fallback and `GET /media`. The engine binds 127.0.0.1. |
| The design's fixed 1440 px layout | Vendored files stay untouched and `app.css` overrides them. Checked at 1440 every task, and at three widths in task 35. |

## 6. Final verification (task 38)
1. Engine checks (ruff, format, pytest) and `demo.py build` with `check()`.
2. The standard app check, plus `corepack pnpm check` at the root.
3. Shots of all 17 mockup states against the demo library, with differences reviewed.
4. A full walk through the brief's sample story, driven by the fake model:
   - Tobin joins, gets sent to the bar, the secret, the whisper and the thought
   - the six-year skip plays and receipts fade
   - the lie is doubted
   - peek, Backstage, Activity "Open the line", the profile's "Right now", "Who knows Aren"
5. A keyboard-only pass.
6. After the smoke test, `tasklist` shows no stray `python.exe` or `electron.exe`.
7. Optional, only if llama-server is already running on :8080: one short real-model session through the Electron app with `KATAKI_DB` pointing at the demo library.
