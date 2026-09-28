# Routes and navigation

## The model

- **Route**: a path in a memory router. Changing it is navigation: it goes into history, Alt ← goes back.
- **State**: data or a mode on the current route (`HomeEmpty`, `SceneReading`, Backstage). Held in the route’s store. Not in history.
- **Overlay**: a dialog, sheet, popover or menu. Held in a global overlay stack. Never in the URL, never in history. Alt ← with an overlay open closes the overlay instead of navigating.
- **Takeover**: replaces the window content regardless of route (`DiskFull`, `AlreadyOpen`). Clears when its condition clears.

Two worlds share one router:

- **The Sky** — every route except `/story/:id`. Rail on the inline-start edge, the Sky background, the Night/Day theme.
- **The Scene** — `/story/:id`. No rail. The place art behind, always the warm “golden hour” scene palette whatever the Sky theme.

Moving from the Sky into a story plays the cloud-parting transition (600 ms; 150 ms crossfade with reduced motion). Leaving a story (the cloud button, Esc with nothing open, Alt ←) plays it in reverse.

## The route table

| Path | Boards | Rail item | Title bar text |
|---|---|---|---|
| `/opening` | A1, A2 | none (no rail) | Kataki |
| `/welcome` | B1 | none | Kataki · first run |
| `/welcome/download` | B2 | none | Kataki · first run |
| `/welcome/server` | B3 | none | Kataki · first run |
| `/welcome/online` | B4 | none | Kataki · first run |
| `/welcome/who` | B5 (B6 over it) | none | Kataki · first run |
| `/home` | C1, C2, C3 | Home | Kataki |
| `/search?q={query}` | C8, C9 | none | Search · Kataki |
| `/characters` | D1, D2, D3 | Characters | Characters · Kataki |
| `/characters/new` | F1, F2, F3 | Characters | New character · Kataki |
| `/characters/:id?tab=story\|profile` | E1, E2 | Characters | {name} · Kataki |
| `/characters/:id/edit` | F6 | Characters | Edit {name} · Kataki |
| `/stories?by=story\|character` | H1, H2, H3 | Stories | Stories · Kataki |
| `/stories/new` | G1, G2, G4 | Stories | New story · Kataki |
| `/story/:id` | P1–P21, Q1–Q5 | none (Scene) | {story name} · Kataki |
| `/world` | I1, I2 | World | World · Kataki |
| `/you` | J1 | You | You · Kataki |
| `/settings/general` | K1 | Settings | Settings · Kataki |
| `/settings/appearance` | K2 | Settings | Settings · Kataki |
| `/settings/language` | K3 | Settings | Settings · Kataki |
| `/settings/models` | K4, K5, K6 | Settings | Settings · Kataki |
| `/settings/memory` | K9 | Settings | Settings · Kataki |
| `/settings/data` | K10 | Settings | Settings · Kataki |
| `/settings/shortcuts` | K14, K15 | Settings | Settings · Kataki |
| `/settings/about` | K16, K17 | Settings | Settings · Kataki |
| `/status/model` | N1 | Home | Nobody is answering · Kataki |

26 paths. `?tab` and `?by` default to `story` when absent.

## Where the app starts

```
launch
 ├─ second instance? ── focus the first window, quit. If the first doesn’t answer in 3 s → AlreadyOpen (N3) in this window.
 └─ /opening (A1) — read library · rebuild memory index · reach a model
     ├─ library unreadable / newer / migration failed → A2 (stays on /opening)
     ├─ no library yet → /welcome (B1)
     ├─ last run crashed → /home + CrashRecovered (A3)
     └─ otherwise → Settings › General › “When Kataki opens”:
          Home (default) → /home
          The last scene → /story/{lastStoryId}   (falls back to /home if that story is gone)
```

`/opening` never shows for less than 400 ms or more than it must; if the model step is slow (>3 s) it continues to Home and the model keeps connecting in the background (Home shows C3’s status line if it then fails).

## First run flow

```
/welcome (B1) — three doors
  Start now ─────────→ /welcome/download (B2) ── “Meanwhile, pick who you’ll meet” → /welcome/who (B5)
  Use a model server ─→ /welcome/server (B3) ── Use this server → /welcome/who
  Use an online model → /welcome/online (B4) ── Test and continue → /welcome/who
  Import cards ───────→ ImportCards (D4) over /welcome, then → /welcome/who
  Skip for now ───────→ /welcome/who (no model yet; the first reply waits and Home shows the banner until one is added)
/welcome/who (B5) — pick one of six · “And you are · Change” opens B6
  Start with {name} → create story → /story/:id (P20, SceneFirst)
  Skip and go to an empty library → /home (C2)
```

The download continues in the background from B2 onwards. If the user reaches a story before it finishes, the composer is enabled, Send queues the line, and the first reply arrives when the model is ready (the widget for the character shows `thinking…`).

## Global navigation

| From | Action | Goes to |
|---|---|---|
| Rail | Home / Stories / Characters / World / You | the route |
| Rail | New character | `/characters/new` |
| Rail | Settings | `/settings/general` (or the last settings panel visited this session) |
| Rail | Feedback | opens Feedback (L1) over the current route |
| Rail | Day / Night | flips the Sky theme immediately; stored in Settings › Appearance |
| Top bar | persona switch | PersonaMenu (C4) |
| Top bar | search field, Ctrl K | Palette (C5) |
| Palette | Enter on “See all results” | `/search?q=` |
| Any character name or portrait | click | `/characters/:id` |
| Any story card / Continue | click | `/story/:id` |
| Scene | cloud button, Alt ←, Esc with nothing open | back to where the user came from, else `/home` |

Keyboard “go to” sequences (G then H, G then S, G then C, G then W, G then Y) are in `KEYBOARD.md`.

## History

- Back and forward: Alt ← / Alt →, the mouse back/forward buttons, and the Scene’s cloud button (back only).
- Replacing, not pushing: tab and grouping changes (`?tab`, `?by`), the `/opening` → first route hop, and `/welcome/*` → `/home`.
- Leaving a route with unsaved edits (`/characters/new`, `/characters/:id/edit`, a dirty dialog) opens DiscardChanges (F7) first. Navigation waits for the answer.

## Deep links

`kataki://story/{id}`, `kataki://character/{id}` and `kataki://settings/{panel}` are registered as a protocol and open the route in the running window. Nothing else is deep-linkable. Unknown ids go to the parent list with a toast (`toast.notFound`: “That {thing} isn’t in your library any more”).

## Window

- Default size 1440 × 900, remembered per display. Minimum 1024 × 700.
- The window title is the “Title bar text” column above.
- Closing the window: Settings › General › “Closing the window”: Quits Kataki (default) or Keeps it in the tray. The tray menu: Open Kataki, Continue {last story}, Quit.
- Zoom (text size): Ctrl + / Ctrl − / Ctrl 0; see `ACCESSIBILITY-AND-MOTION.md` for the cap.
- Language change restarts the renderer (K3 says so) and restores the route, scroll and composer draft.

## Layout breakpoints (CSS px after zoom)

| Width | Sky | Scene |
|---|---|---|
| ≥ 1280 | Full rail (200 px), content as boards | Chat 800 at inline-start 320; widgets column 272 at inline-end; clock and music bottom inline-start |
| 1024–1279 | Compact rail (72 px), rows wrap (R1) | Chat fills to 684; clock and music join the widgets column (R1) |
| 640–1023 | Compact rail, single column (R4) | Chat full width; widgets fold into a “Here” button that opens them as a sheet (R4) |
| < 640 | not allowed: zoom is capped so the page is never narrower | — |
