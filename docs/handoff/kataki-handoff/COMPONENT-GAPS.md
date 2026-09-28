# Design-system changes needed for 1:1

The boards use the Kataki design system as it is today. Building the app 1:1 — in every language, with every state — needs the changes below. Make them in the design system package first, then build screens on it. None of them changes how anything looks.

## 1. Hardcoded English inside components

These components render English text that isn’t a prop. Each needs the text passed in (a `strings` prop, or individual props), defaulting to the English shown so current boards keep rendering. Found by scanning `components/bundle.js`.

| Component | Hardcoded text | Proposed props |
|---|---|---|
| `Rail` | Home, Stories, Characters, World, You, New character, Settings, Feedback, Day, Night, What’s new (dot label) | `labels: Record<item, string>` |
| `PersonaSwitch` / `TopBar` | playing as | `caption` |
| `SearchField` | Search everything, Ctrl K | `placeholder` exists; add `shortcutLabel` |
| `CommandPalette` | Search and commands, Search, or type a command | `label`, `placeholder` |
| `Field` | Required | `requiredLabel` |
| `DropZone` | Drop a file here, No portrait | `title`, `emptyLabel` |
| `Popover`, `Dialog`, `Sheet` | Close | `closeLabel` |
| `Toast` | Dismiss | `dismissLabel` |
| `TimeStrip` | Time of day | `label` |
| `SecretCard` | Only {name} … | `caption` |
| `CharacterCard` | Continue, More for {name} | `continueLabel`, `moreLabel` |
| `ContinueHero` | Continue, Continue · {book}, New story | `continueLabel`, `newLabel` |
| `StoryPreview` | Continue, Who is here | `continueLabel`, `castLabel` |
| `SettingsRow` | Not answering | `errorLabel` |
| `ConnectionRow` | Test, Remove | `testLabel`, `removeLabel` |
| `FolderRow` | Open folder | `openLabel` |
| `SceneHeader` | Back to the Sky | `backLabel` |
| `ChatPanel` | The story | `label` exists; make it required |
| `LineTools` | Line tools, Previous take, New take, Edit, Hide | `labels` |
| `ChatLine` | Drew on memory, writing… | `labels` |
| `TitleCard` | Undo | `undoLabel` |
| `RecallBox` | Remembered (default title) | `title` exists; make it required |
| `ModeChip` | Auto (default), Plain text, Works it out from how you write | `labels` |
| `ModeMenu` | the six modes, their syntax lines, How your line is read, the footer | `modes: {value,label,detail,icon}[]`, `label`, `footer` |
| `Composer` | Your line, Composer detail, Simple, Advanced, Continue the story, Pass time, Answers, Whoever fits, Narrator, Send, Stop, Only Mike will hear this (default), Speak or act as Liv… (default) | `labels`; `answers: {id,label,who?,icon?}[]` instead of the fixed three chips |
| `EditLine` | Edit line, Regenerating from here rewrites the {n} messages…, Save edit, Save and regenerate from here, Cancel | `labels` (ICU message for the count) |
| `Widget` | Drag to move, Remove widget, Pin, Unpin | `labels` |
| `CharacterWidget` | Pin {name}, Unpin {name}, thinking… | `labels` |
| `ClockWidget` | Pass time, Story clock | `labels` |
| `MusicWidget` | Matched to the scene (default source) | `source` required |
| `TimeSkipCard` | Three weeks later (default), Undo | `undoLabel`; children required |
| `BackstageToggle` | Backstage | `label` |

The Arabic proofs (R2, R3) draw the Rail, persona switch, scene header, Backstage toggle and composer with the DS class names and Arabic text to show the target.

## 2. Missing props or behaviour

| Component | Needed | Why |
|---|---|---|
| `Rail` | `compact` exists; add `side`-agnostic tooltips in RTL and a `labels` prop | R1, R2 |
| `Composer` | `queued: number` (“1 waiting”), `disabledReason`, `answers` list, `onModeChange`, `onPassTime`, `onContinue` | SCENE.md › The composer |
| `ChatLine` | `speaker` accepts any id (narrator, any character) with a `color` prop, instead of the fixed liv/mike/theo map | every story with other characters |
| `ChatLine` | `onFocus`-driven tools (show `LineTools` when focused, not only `hover`) | keyboard parity |
| `Reaction` | a `+{n}` overflow chip | more than three reactions |
| `CharacterWidget` | `status` accepts the fixed-format template output; `onOpen` | P15 |
| `Menu` | `tone="scene"` (today the scene menu is hand-built from `.k-menu--scene`) and `anchor`/placement | M2 |
| `Toast` | `onAction`, `onDismiss`, `duration`, pause on hover/focus | M3 |
| `Dialog` | `initialFocus`, `onClose`, `dirty` (ask before closing) | overlay system |
| `CommandPalette` | controlled `query`, `onSelect`, group limits | C5–C7 |
| `Segmented` / `Chip` | `disabled` per option with a reason | K3 incomplete languages |
| `Icon` | `send` flips in RTL automatically (like `left`/`right`) | R3 |
| `renderProse` (inside `ChatLine`) | `[dir=rtl] em { font-style: normal }` | R3 |

## 3. Scaffolding to promote into the design system

`boards/app/app.css` holds page-level classes the boards share (`.app`, `.pg-head`, `.sec`, `.set`, `.ov`, `.dlg*`, `.scene*`, `.bs*`, `.privacy`). They’re stable; promote them to a `layout.css` in the DS so the app doesn’t fork them. `.dlg*` in particular duplicates what `Dialog` renders and should become `Dialog`’s `size="xl"` and a `Dialog.Body/Foot` API.
