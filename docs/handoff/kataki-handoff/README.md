# Kataki RPAI · implementation handoff

This folder is the complete specification of the Kataki desktop app: every route, overlay, menu, state, toast and error. It is written for an AI coding agent (or a person) who will build the app 1:1 from it.

Two sources, one truth:

- **The canvas** — *Kataki · App screens* in Claude Design. 118 artboards, each a working page built only from the Kataki design system. Every board has a Night/Day tweak. The `.dc.html` sources are in `boards/`.
- **These files** — the words the canvas can't carry: routes, data, behaviour, keyboard, errors, edge cases.

When the two disagree, the board wins for **look and copy**; these files win for **behaviour and data**. Report the mismatch in the PR.

---

## Read in this order

| # | File | What it is |
|---|---|---|
| 1 | `README.md` | This page. Conventions, stack mapping, definition of done. |
| 2 | `ROUTES.md` | The route table, the router model, what is a route and what is state, deep links, window behaviour. |
| 3 | `SCREENS.md` | Every route and its states: purpose, data, layout notes, copy sources, interactions, keyboard, empty / loading / error. |
| 4 | `SCENE.md` | The story screen on its own: the turn pipeline as the UI sees it, streaming, takes, time, widgets, Backstage. |
| 5 | `OVERLAYS-AND-MENUS.md` | Every dialog, sheet, popover and menu: trigger, items, focus, dismissal, what it writes. |
| 6 | `ERRORS.md` | All 62 error codes: surface, exact copy, actions, recovery. Generated from `errors.json`. |
| 7 | `DATA.md` | Entities, fields, enums, derived values and the string templates that read them. |
| 8 | `KEYBOARD.md` | Every shortcut, focus order and the remapping rules. |
| 9 | `ACCESSIBILITY-AND-MOTION.md` | Focus, screen readers, reduced motion, contrast, text size, right-to-left. |
| 10 | `COMPONENT-GAPS.md` | Changes the design system needs before 1:1 is possible (hardcoded English and missing props). |
| — | `manifest.json` | Every board: code, file, route, kind, props, what it imports, what it links to, which components it uses, its canvas position. |
| — | `errors.json` | The error catalogue as data. Import it; don’t retype it. |
| — | `strings.boards.en.json` | Every visible string on every board, extracted, keyed by board. The seed for `strings/en.json`. |
| — | `boards/` | The 118 artboard sources, `canvas.json` (the canvas layout), `app/app.css` and `app/app.js` (page scaffolding the boards share) and a copy of the design system they were built on (`ds/kataki`: tokens, component bundle, `index.d.ts` with every prop). They are for reading; they run inside the Claude Design canvas, whose runtime isn’t included. |

## Board codes

Every board has a code. `SCREENS.md`, `OVERLAYS-AND-MENUS.md` and `ERRORS.md` refer to boards by code, the canvas shows the code in each board’s title, and the map board (`00`) links to all of them.

| Letter | Area | Letter | Area |
|---|---|---|---|
| A | Opening, crash | J | You and personas |
| B | First run | K | Settings |
| C | Home, palette, search | L | Feedback |
| D | Characters | M | Menus, toasts, errors (reference boards) |
| E | A character’s profile | N | System takeovers |
| F | Making and editing a character | P | The Scene (a story) |
| G | New story | Q | Backstage |
| H | Stories | R | Proofs: size, language, access, Day |
| I | World | 00 | The map |

## Kinds of board

`manifest.json` gives each board a `kind`:

| kind | Count | Meaning |
|---|---|---|
| `route` | 28 | A URL (26 paths; two use a query to pick a tab or grouping). |
| `state` | 37 | The same route with different data or mode. No URL change. |
| `overlay` | 39 | A dialog, sheet, popover or menu over a route. Never changes the URL. |
| `takeover` | 2 | Replaces the whole window: disk full, already open. |
| `reference` | 6 | Catalogue boards: the map, every menu, every toast, every error, update states. |
| `proof` | 6 | The same design at 1024 wide, in Arabic, at 200% text, for access, and by day. |

## Stack mapping

The boards are HTML that uses the design system’s React components by name (`Kataki.Button`, `Kataki.ChatLine`…). In the app:

- **Shell**: Electron, one `BrowserWindow`, `minWidth 1024`, `minHeight 700`, frameless is **not** required. Single-instance lock (`app.requestSingleInstanceLock`).
- **Renderer**: React + the Kataki design system package (the same components the boards use, same names, same props). No other UI library.
- **Routing**: a memory router (`createMemoryRouter`) with the paths in `ROUTES.md`. Overlays are UI state in a store, not routes.
- **Styles**: the design system’s `tokens.css` and `bundle.css`, plus the page scaffolding in `boards/app/app.css` (`.app`, `.pg-head`, `.set`, `.ov`, `.dlg`, `.scene*`…). Logical CSS properties only.
- **Data**: a local library (see `DATA.md`) owned by the main process. The renderer talks to it over a typed IPC API; it never opens files itself.
- **Models**: OpenAI-style chat API over HTTP to whichever connection answers (`SetModels`), plus Kataki’s own bundled model.
- **Secrets**: API keys via Electron `safeStorage` (Windows Credential Manager on Windows). Never in the library, logs or exports.
- **Strings**: `strings/<lang>.json`, ICU MessageFormat. Seed `en` from `strings.boards.en.json`. No string in a component.

## Copy rules (non-negotiable)

1. **No string is written by a model at render time.** Every visible string is one of: static (in the strings file), typed by the user, computed from data (counts, dates, durations), or a row the engine stored during a turn. The one model call that writes user-visible text outside a reply is the memory reader, and it runs inside a turn.
2. **Every board renders with the model server stopped.** That is a test (see “Definition of done”).
3. **Sentences over data are templates** in the strings file with ICU plurals and selects: `{name} trusts you {size, select, s {a little more} m {more} other {much more}}`. `DATA.md` lists them.
4. Resume is **Continue**, everywhere. Opening the new-story flow is **New story**, everywhere. The button that commits a new story names what it starts: “Start the scene” (G1), “Start with {name}” (B5), “Say hello” (C2). No other verbs for these actions.
5. Error messages say what happened, what is safe, and what to do, in that order, and end with the code in small mono. See `ERRORS.md`.
6. Placeholders in square brackets (`[UPDATE HOST]`, `[MODEL HOST]`, `[FEEDBACK HOST]`, `[KATAKI LICENCE]`, `[MODEL LICENCE]`, `[ART LICENCE]`, `[FIRST LINE OF ITS RELEASE NOTES]`) are facts the product owner must supply. Do not invent them. Ship with a build-time check that fails if any remain.

## The sample world

The boards use the sample world that ships with Kataki: Liv (the default persona), Mike, Theo, Nico, Jae, Cas, Dani (a draft); Halcyon Coffee, Corvel Palace, the flat on Ardenne; the book *Close to the Crown*; the plot *The Invitation*. Names, lines and numbers on the boards are sample data, not copy. Anything in `{braces}` in these files is data.

## Definition of done

A route or overlay is done when:

- [ ] It matches its board(s) at 1440 × 900 in Night and Day, pixel for pixel within the design system’s own rendering.
- [ ] It holds at 1024 × 700 (R1), in Arabic right-to-left (R2, R3), and at 200% zoom on a 1440 window (R4).
- [ ] Every state listed for it in `SCREENS.md` is reachable and matches its board.
- [ ] Every string comes from the strings file or data. `grep` for English in components finds nothing.
- [ ] It works with the keyboard alone, in the order in `KEYBOARD.md`; focus is visible; Esc does what it says.
- [ ] It renders with the model server stopped and no network.
- [ ] Every error it can raise uses the code, surface and copy in `errors.json`.
- [ ] No file on the user’s disk outside the library is deleted or overwritten without the user choosing it in a dialog.

## Out of scope for this handoff

Account systems, sync, telemetry (there is none, by design), mobile, and a web build. The engine’s internals (prompting, memory decay maths) are specified only as far as the UI reads them.
