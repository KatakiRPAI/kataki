# Kataki RPAI · design handoff

This folder holds the visual design of Kataki RPAI: a design system, 17 desktop screen mockups, and the illustrations they use. It is written for the engineer (human or AI) who will build the real UI in `app/`.

Start with these three files, in this order:

1. `design-system/DESIGN-SYSTEM.md`: the principles, the two worlds, tokens, every component and its states, and the rules for memory signals.
2. `screens/SCREENS.md`: what each screen shows, which states it demonstrates, and where its parts come from.
3. `design-system/components.html`: open it in a browser. It's a working gallery of every component, built only from `tokens.css` and `components.css`.

## What's in here

```
design/
├─ README.md                  ← you are here
├─ design-system/
│  ├─ DESIGN-SYSTEM.md        principles, tokens, components, behaviour rules
│  ├─ tokens.json             source of truth for every value (colours, type, radii, spacing, motion, layout)
│  ├─ tokens.css              the same values as CSS custom properties (--k-*)
│  ├─ components.css          reusable component classes (.k-*), framework-agnostic
│  ├─ components.html         live gallery of every component and state
│  └─ icons/
│     ├─ sprite.svg           66 icons as <symbol id="i-name">
│     └─ icons.json           the same icons as standalone SVG strings
├─ screens/
│  ├─ SCREENS.md              screen-by-screen spec
│  ├─ index.html              clickable index of all screens
│  ├─ html/*.html             each screen as a static page, opens offline
│  └─ png/*.png               a screenshot of each screen
├─ assets/
│  ├─ characters/*.svg        placeholder portraits (Mira in 5 expressions, Tobin in 2, Ilsa, Oren, Wren, Aren, Sable)
│  ├─ places/*.svg            The Gull at dusk and night, table foreground layers, lighthouse, market, clouds
│  └─ fonts/                  Chewy, Figtree, Newsreader, JetBrains Mono (OFL) + fonts.css
└─ source/
   ├─ canvas/*.dc.html        the original design-canvas artboards + canvas.json
   └─ generators/*.py         the Python that produced the artboards and illustrations
```

## How to use it when building

- **Tokens first.** Import `tokens.css` (or generate your theme from `tokens.json`). Don't hard-code hex values; every colour in the screens has a token.
- **Components are specs, not a library.** `components.css` is plain CSS with BEM-ish class names. Port each component to whatever the app uses (React, Vue, Svelte...), keeping the names, states and values. The screen HTML files use inline styles, because they were exported from a design canvas. **Use them for layout, copy and measurements, not as code to copy.**
- **The screens are 1440×900.** Layouts must hold from 1280 to 1920 px wide. Measurements in the specs are at 1440.
- **Art is placeholder.** The characters and places are flat SVG illustrations drawn for the mockups. The real app will use generated painted art. Keep the layering the mockups use: place, then characters, then foreground, then vignette. Never use photos of real people.
- **Fonts ship locally.** The app is local-first, so load `assets/fonts/fonts.css`, not Google Fonts. The screen files try the local fonts first and fall back to Google Fonts.
- **Accessibility is part of the spec.** Use real `<button>`, `<a>` and `<label>` elements, keep focus rings visible, keep hit targets at least 44 px, make the whole app work from the keyboard, keep mute one click away, and keep text on a scrim over images.

## Two worlds, one sentence each

- **The Sky** (outside a story): a bright social app above the clouds. Your characters are friends with profiles. Frosted glass, pills, candy icons, bouncy motion.
- **The Scene** (inside a story): an intimate, lamplit room with the character in front of you. The story is set in book type, and the controls fade while you read.

Moving between them is **the dive**: the clouds part and the scene fades in. Leaving floats you back up.
