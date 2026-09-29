# Kataki design system · v2 (Sky v2.1)

The contract between the design and the code. Values live in `tokens.json` / `tokens.css`, component styles in `components.css`. The v1 system (light candy Sky, warm Scene, Chewy, the orb) is in `legacy/` for reference only — do not build from it.

Screens that show every rule below: `../screens/html/Sky2-*.html` and `Scene-*.html`. The four proof boards are `Sky2-Home-Day`, `Sky2-Home-Compact`, `Sky2-Home-Arabic` and `Sky2-Access`.

---

## 1. Principles

1. **One night, two places.** Outside a story you are in the **Sky**: a night above the clouds. Inside a story you are in the **Scene**: the same navy surfaces, translucent over a painted place. Same tokens, same buttons, same type.
2. **The sky shows.** Stars, one crescent moon and a moonlit cloud bank sit behind the top of every Sky page, and content sits *on* it. The ground takes over below the fold, where lists need calm.
3. **The story speaks in Newsreader, the app speaks in Baloo.** Names from the story world — stories, characters, places, books — and all story prose are set in Newsreader. Page and section headings are Baloo 2 800. Everything else is Figtree.
4. **No copy that needs a model to render.** Every string is static copy, authored content, a computed value, or a row a model wrote once at turn time. See `../research/COPY-RULES.md`. The test: every screen renders with the model server stopped.
5. **Measured, not eyeballed.** Every text colour clears 4.5:1 on every surface it sits on, in both themes. The audit in `../source/audit/` proves it against rendered pixels; run it in CI.
6. **Light on the GPU.** The model often shares the graphics card: layered images, opacity, transforms and crossfades only. One `backdrop-filter` per layer at most.

---

## 2. Colour

Two themes share one set of names. Night is the default.

| Token | Night | Day | Use |
|---|---|---|---|
| `ground` | `#0a1028` | `#edf2ff` | page |
| `panel` | `#131b3a` | `#ffffff` | cards, panels |
| `raise` | `#1a2348` | `#f4f7ff` | selected rows, secondary buttons, chips |
| `over` | `#212b57` | `#ffffff` | hovered rows in menus |
| `rail` | `#0d142f` | `#f7f9ff` | the navigation rail |
| `ink` | `#eef2ff` | `#0f1733` | primary text |
| `mid` | `#c6d0ec` | `#2c3860` | secondary text, quotes |
| `muted` | `#aebbdc` | `#46537c` | metadata |
| `faint` | `#95a2cb` | `#5a668d` | eyebrows, hints — still ≥ 4.6:1 everywhere |
| `accent` | `#5b86ff` | `#2f5be0` | fills, bars, selected borders, the focus ring — **never small text** |
| `accent-text` | `#86a6ff` | `#2a52cf` | links and accent words |
| `primary` / hover | `#3558d6` / `#4065e4` | `#2f5be0` / `#274fcc` | the primary button; white label 6.0:1 / 5.7:1 |
| `warm` | `#e7b06a` | `#8a4f0a` | state: feelings, memory, secrets, pinned |
| `ok` / `bad` | `#6fd8a4` / `#ff8fa3` | `#17704a` / `#b4233f` | success / danger |

The full contrast matrix, computed from these values, is on `Sky2-Access`. Lowest cell: 5.4:1 at night, 5.0:1 by day.

**Rules**

- Never set text with `opacity`. Dim with a token.
- Text over a photograph sits on a measured scrim (`.k-still__caption`: 72px, 94% → 78% → 0).
- Filled chips pick their label colour by computed contrast (`best_on()` in the generator), not by eye.
- Amber means *state*. Blue means *action*. Neither is decoration.

## 3. Type

| Role | Family | Arabic | Where |
|---|---|---|---|
| Display | Baloo 2 | Baloo Bhaijaan 2 | page titles (32/800), section heads (24/700), the wordmark |
| Story | Newsreader | Noto Naskh Arabic | story, character, place and book names; prose 19/1.55; quotes; the time-skip card |
| UI | Figtree | IBM Plex Sans Arabic | everything else |
| Mono | JetBrains Mono | — | Backstage, model ids, paths, shortcuts |

Story names scale ×1.06 against the display size and use weight 500 at 22px and up, 600 below. Hero story title 53px; profile name 57px. Eyebrows 10.5/700, +0.15em, uppercase (none of those three in Arabic). All numbers are tabular.

Baloo 2 has **no Arabic**; Baloo Bhaijaan 2 is its Arabic sibling. All fonts are OFL and vendored in `../assets/fonts/` — the app must render offline.

## 4. Shape, space, elevation

- Radii **6 / 10 / 16**, plus a pill for buttons, chips and status pills only.
- Page gutter 40px (28px compact). Rail 200px, folding to 72px icons below 1200px.
- Elevation comes from the surface ladder and a 1px border. One real shadow (`shadow-float`) for things that float: stills, portraits, popovers, dialogs. No coloured glows.
- Minimum target 32px (WCAG 2.2 AA asks for 24).

## 5. Focus and keyboard

- Focus ring: `0 0 0 2px ground, 0 0 0 4px accent` — 5.6:1 on the ground. On everything focusable, via `:focus-visible`.
- Tab order follows reading order; Home's order is drawn on `Sky2-Access`. `Ctrl K` searches from anywhere; `Esc` always goes back one level; every shortcut is remappable (`Sky2-Set-Shortcuts`).
- Icon-only controls carry `aria-label`. The compact rail keeps its labels for screen readers.
- Widget-edit mode makes the chat `inert`, not merely faded.

## 6. Motion

Signature moments: clouds part when you move between places, and roll across for a time skip. With `prefers-reduced-motion` (or the setting in Appearance): clouds → 150ms crossfade, stars still, time skip cuts straight to its card, the caret stops blinking, hover lifts become border changes, widgets move in one step.

## 7. Right to left

Proven on `Sky2-Home-Arabic`.

- Logical properties only (`inset-inline-*`, `margin-inline-*`, `text-align: start/end`). Nothing else is needed to mirror.
- User content is wrapped in `<bdi>` / `dir="auto"` so an English story inside an Arabic UI keeps its own direction and punctuation.
- No letter-spacing, no italics, no uppercase in Arabic; 12px and below +2px, up to 15px +1px; Naskh titles at line-height 1.45.
- Plurals and relative times through ICU MessageFormat (Arabic has six plural forms).
- Western digits by default with `م` for pm; Eastern Arabic digits are a setting.

## 8. Components

Classes in `components.css`: `.k-sky` (+ `__stars`, `__moon`, `__clouds`), `.k-title`, `.k-h2`, `.k-name`, `.k-prose`, `.k-eyebrow`, `.k-meta`, `.k-panel`, `.k-raised`, `.k-pop`, `.k-still`, `.k-btn` (`--primary`, `--secondary`, `--ghost`, `--icon`), `.k-link`, `.k-chip` (+ `__count`), `.k-pill` (`--warm`, `--ok`, `--muted`), `.k-rail` (+ `__item`, `__label`), `.k-meter`, and the Scene: `.k-scene`, `.k-glass`, `.k-chat`, `.k-composer`, `.k-line--dim`, `.k-react--memory|feeling|warm|belief`.

Buttons, by verb: **Continue** resumes a story, **New story** starts one. Nothing else says either.

## 9. The Scene

Same ladder, translucent: glass `rgba(19,27,58,.72)`, chat panel `rgba(10,16,40,.82)`, composer `rgba(22,30,64,.94)`, borders `rgba(168,190,255,.14)`, ink `#eef2ff`, muted `#b3bfdf`. The place art stays warm and painted, under a 22% navy tint. Send is the flat primary blue. Amber is kept for memory. Speaker names use each character's colour (Liv `#a9c8ff`, Mike `#f2b870`, Theo `#e8cc6a`). Backstage keeps its mono blueprint look — it is the one place that is meant to feel like an instrument.
