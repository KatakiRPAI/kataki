# Accessibility, motion, text size, right to left

Proof boards: R1 (1024 wide), R2 and R3 (Arabic), R4 (200%), R5 (keyboard, focus, motion, contrast), R6 (Day).

## Focus

- `:focus-visible` only. `--focus-ring`: 2 px of the ground colour, then 2 px of accent. In a story: the scene primary.
- Never removed, never clipped. Scrolling containers get 4 px inner padding so rings aren’t cut.
- Focus returns to the opener when any overlay closes, and to the list position after a delete.

## Names, roles, live regions

- Every icon-only button has `label` (DS `IconButton` requires it) and a tooltip with the same text.
- Landmarks: Rail `nav` “Main”; page `main` with the page title as its label; the chat `section` “The story”; Backstage `region` “Backstage”; widgets `region` “Widgets”.
- Headings in order: one `h1` per page (`.pg-title`, the story name in a story), `h2` per section, `h3` inside cards.
- The chat lines container is **not** `aria-live` during streaming. When a reply finishes, a hidden polite live region announces `{speaker}: {text}`, then its reactions in one message (“Mike will remember this. Mike trusts you a little more.”). Joins, leaves and time skips are announced as their note/card text.
- Errors on the `line`, `page`, `dialog` and bad-`toast` surfaces are `role="alert"`; statuslines and callouts are `role="status"`.
- Images: portraits use the character’s `alt` (set in F5, default `{name}, portrait`); place stills use the place’s alt; decorative art (the Sky, clouds, the blurred scene background) is `alt=""`.
- Meters announce `{label} {value} of 100`; `MemoryRow` reads `{text}, {sharpness word}, {source}`.
- Language: `lang` on the root follows the UI language; story text written by the user keeps `dir="auto"` so mixed-language lines render correctly.

## Reduced motion

Setting: Follow Windows (default, `prefers-reduced-motion`) · Always reduce · Never reduce. Applied as a root class so both CSS and JS read it.

| Motion | Normal | Reduced |
|---|---|---|
| Entering / leaving a story | clouds part, 600 ms | crossfade, 150 ms |
| Changing place | clouds close and part, 900 ms | crossfade, 200 ms |
| Time skip | clouds sweep, card rises | card appears |
| A reply arriving | words stream, caret blinks | words stream, caret steady |
| Widgets appearing / fading | slide and fade, 220 ms | fade, 120 ms |
| Dialogs, sheets, menus | rise/slide + fade, 100–220 ms | fade, 100 ms |
| Toasts | rise and fade | fade |
| The Sky | stars twinkle | stars still |
| Reactions under a reply | one by one, 150 ms apart | all at once |

Nothing flashes more than three times a second. No parallax.

## Contrast

- Body text meets WCAG 2.2 AA on every surface in both Sky themes and the Scene (the DS tokens are built for it; don’t lighten `--muted` or `--faint`).
- **High contrast** (Appearance): raises `--border` and `--hairline`, lifts `--muted`/`--faint`/`--mid` toward ink, dims the Sky to 25%, and drops the scene art behind the chat to 30% brightness. Colours of meaning (warm, ok, bad) don’t change.
- Windows high-contrast (`forced-colors: active`) is respected: no information by colour alone; states also have an icon or a word (pills carry words; the ok/wait/bad dots in Backstage sit next to words).

## Text size (R4)

- Implemented as Electron zoom (`webContents.setZoomFactor`). Appearance offers 100 / 125 / 150%; Ctrl + continues to 200%; Ctrl 0 resets to the Appearance value.
- The page’s CSS width is `windowWidth / zoom`. Layout breakpoints (`ROUTES.md`) use it.
- **Cap**: zoom never makes the page narrower than 640 CSS px. On a 1024 window the maximum is 150%; Ctrl + beyond it does nothing except show the toast `toast.zoom.cap`: “Make the window wider to go past {max}%”.
- The story text scales with everything else. Nothing truncates that the user must read: names in cards may ellipsize with the full name in a tooltip; lines, messages and errors wrap.

## Right to left (R2, R3)

- `dir="rtl"` on the root when the UI language is right-to-left (Settings › Language › Mirror the layout: Automatic). Everything is built with logical properties, so the layout mirrors by itself: the Rail moves to the right, the chat sits on the right with widgets on the left, arrows and the send icon flip (`Icon flip`), progress fills from the right.
- **Doesn’t mirror**: the clock face, media controls, the brand wordmark (stays Latin “Kataki”), code and file paths (isolated with `dir="ltr"`).
- Fonts: Baloo Bhaijaan 2 (display), IBM Plex Sans Arabic (UI), Noto Naskh Arabic (story) — already the fallbacks in the DS font stacks; ship them with the app.
- Arabic text is never slanted: `*actions*` keep the action colour but `font-style: normal` under `[dir="rtl"]`. Uppercase and letter-spacing are removed for eyebrows, pills and field labels (the DS does this).
- Digits: Western by default; Eastern Arabic (٠١٢٣) when chosen in Language. Times use `م` / `ص` from ICU, not hand-written suffixes.
- Every component string must come through props or the strings file for this to work: see `COMPONENT-GAPS.md`.

## Day theme (R6)

The Sky has two palettes (`data-theme="night|day"`), both first-class; Day is not an inversion. The Scene doesn’t change with the theme. The Rail’s last item switches it (Day / Night); Appearance offers Follow the system.
