# Kataki RPAI · design handoff

This folder holds the visual design of Kataki RPAI: a design system, 71 desktop screen mockups — 29 of Sky v2 (the direction, including four proof boards), 14 of the Scene, 13 of the original Sky, and 15 style studies — and the illustrations they use. It is written for the engineer (human or AI) who will build the real UI in `app/`.

**Start here: `research/SKY-V2.md`** (read v2.1 at the end first). The chosen direction is the dark Sky, rebuilt on the audit — `screens/html/Sky2-*.html`, 29 screens covering every page, every settings panel, every menu, the states, a Day theme, a 1024-wide layout, Arabic right to left, and an accessibility board. The Scene is on the same surfaces. All of it passes WCAG AA text contrast, measured against rendered pixels (`source/audit/`). The `Style-*` screens and `research/STYLE-DIRECTIONS.md` are the studies that led there; keep them as reference, don't build them. The original Sky screens are kept for reference only.

Start with these files, in this order:

1. `design-system/DESIGN-SYSTEM.md`: v2 — principles, both themes, type, focus, motion, right to left, components. (v1 is in `design-system/legacy/`; don't build from it.)
2. `screens/SCREENS.md`: what each screen shows, which states it demonstrates, and where its parts come from.
3. `design-system/tokens.css` + `components.css`: v2 values and classes, Night and Day, logical properties throughout.
4. `sample-world/WORLD.md`: the cast, places, plots and story the screens are filled with — and the same thing as JSON, if you want it as seed data.

## What's in here

```
design/
├─ README.md                  ← you are here
├─ research/                  the study behind the redesign (read before changing the Sky)
│  ├─ UX-STUDY.md             personas, journeys, a 22-item friction log, newbie/power rules
│  ├─ COMPETITORS.md          SillyTavern, Character.AI, Janitor/Chub, Talkie, Backyard AI — cited
│  ├─ DESIGN-RESEARCH.md      2026 trends, worn-out patterns, a 12-item "AI slop" checklist, craft refs
│  ├─ AUDIT.md                every Sky element: decision → alternative → verdict
│  ├─ SKY-V2.md               ← the chosen direction: what changed from the old Sky, and why
│  ├─ COPY-RULES.md           where every string comes from — no screen may need a model call to render
│  └─ STYLE-DIRECTIONS.md     the five directions and what each one commits to
├─ design-system/
│  ├─ DESIGN-SYSTEM.md        v2: principles, themes, type, focus, motion, RTL, components
│  ├─ tokens.json             v2 source of truth: Night + Day, fonts, radii, layout, the Scene
│  ├─ tokens.css              the same as CSS custom properties (--k-*); data-theme="day"
│  ├─ components.css          v2 component classes (.k-*), framework-agnostic, RTL-safe
│  ├─ legacy/                 v1 system (light candy Sky, warm Scene) — reference only
│  └─ icons/
│     ├─ sprite.svg           66 icons as <symbol id="i-name">
│     └─ icons.json           the same icons as standalone SVG strings
├─ screens/
│  ├─ SCREENS.md              screen-by-screen spec
│  ├─ index.html              clickable index of all screens
│  ├─ html/*.html             each screen as a static page (71), opens offline
│  └─ png/*.png               a screenshot of each screen
├─ sample-world/             the world every screen is filled with
│  ├─ WORLD.md               profiles, secrets, places, plots, books, and the sample transcript
│  ├─ characters.json        personas + characters, ready to seed
│  ├─ places.json  plots.json  books-and-stories.json  transcript.json
├─ assets/
│  ├─ characters/*.png        Liv, Mike, Theo, Jae, Nico, Cas (+ dani.svg, the no-portrait placeholder)
│  ├─ places/*.png            Halcyon Coffee, Corvel Palace, the flat on Ardenne (+ clouds.svg)
│  └─ fonts/                  Baloo 2, Baloo Bhaijaan 2, Figtree, Newsreader, JetBrains Mono, IBM Plex Sans Arabic, Noto Naskh Arabic (OFL) + fonts.css
└─ source/
   ├─ canvas/*.dc.html        the original design-canvas artboards + canvas.json
   ├─ generators/*.py         the Python that produced the artboards (sky2.py, scene3.py)
   └─ audit/                  the WCAG contrast audit: renders each board with real fonts, checks every text run against its pixels
```

## How to use it when building

- **Tokens first.** Import `tokens.css` (or generate your theme from `tokens.json`). Don't hard-code hex values; every colour in the screens has a token.
- **Components are specs, not a library.** `components.css` is plain CSS with BEM-ish class names. Port each component to whatever the app uses (React, Vue, Svelte...), keeping the names, states and values. The screen HTML files use inline styles, because they were exported from a design canvas. **Use them for layout, copy and measurements, not as code to copy.**
- **The screens are 1440 wide.** Layouts must hold from 1024 (see `Sky2-Home-Compact`) to 1920 px. Measurements in the specs are at 1440.
- **Art is placeholder.** The portraits and places are the reference images from the design pass: they set the intended look (painted, character-led, warm) but are not final assets — replace them with generated or licensed art before shipping. Characters are fictional; never use photos of real people.
- **Portraits are cropped, not positioned.** Every portrait fills its box with `object-fit: cover` and a per-character `object-position` focal point (in `sample-world/characters.json` as `face_focus`). That is what keeps a face centred in a 20 px receipt avatar and a 272 px widget alike.
- **Fonts ship locally.** The app is local-first, so load `assets/fonts/fonts.css`, not Google Fonts. The screen files try the local fonts first and fall back to Google Fonts.
- **Accessibility is part of the spec.** Use real `<button>`, `<a>` and `<label>` elements, keep focus rings visible, keep hit targets at least 32 px (buttons are 36–48), make the whole app work from the keyboard, keep mute one click away, and keep text on a scrim over images.

## Two places, one sentence each

- **The Sky** (outside a story): night above the clouds — stars, one moon, moonlit cloud — with your characters, stories and world on calm navy panels. A Day theme is the second option.
- **The Scene** (inside a story): a full-height chat in book type over a dimmed painted place, on the same navy surfaces, with widgets the user arranges around it.

Moving between them: the clouds part and the scene fades in (a crossfade with reduced motion).
