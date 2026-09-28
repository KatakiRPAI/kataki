# Keyboard

“Every one of these can be changed: click it and press the new keys. Nothing in Kataki needs a mouse.” (K14). Defaults below; overrides live in `shortcuts` (`DATA.md`). On macOS builds Ctrl reads as ⌘; Windows is the reference.

## Shortcuts

| Action id | Label (K14) | Default | Where it works |
|---|---|---|---|
| `search` | Search everything | Ctrl K | anywhere |
| `newStory` | New story | Ctrl N | anywhere |
| `newCharacter` | New character | Ctrl Shift N | anywhere |
| `persona` | Switch persona | Ctrl P | anywhere |
| `settings` | Settings | Ctrl , | anywhere |
| `focusSearch` | Focus the search on a page | / | Sky pages (opens the palette where the page has no search) |
| `feedback` | Tell us something | Ctrl Shift F | anywhere |
| `close` | Close whatever is open | Esc | anywhere |
| `goHome` | Go to Home | G then H | Sky, not in a text field |
| `goStories` | Go to Stories | G then S | Sky |
| `goCharacters` | Go to Characters | G then C | Sky |
| `goWorld` | Go to World | G then W | Sky |
| `goYou` | Go to You | G then Y | Sky |
| `next` | Next control | Tab | anywhere |
| `send` | Send | Enter | composer |
| `newLine` | New line | Shift Enter | composer |
| `sendPass` | Send and pass time | Ctrl Enter | composer |
| `editLast` | Edit your last line | ↑ | composer, when empty |
| `regenerate` | Regenerate the last reply | Ctrl R | story |
| `stop` | Stop a reply | Esc | story, while a reply streams |
| `takes` | Previous · next take | Alt ← / Alt → | story, on a focused line or the last reply |
| `continue` | Continue the story | Ctrl J | story |
| `backstage` | Backstage | Ctrl B | story |
| `find` | Find in this story | Ctrl F | story |
| `mute` | Mute the music | Ctrl M | story |
| `widgets` | Edit widgets | Ctrl E | story |
| `reading` | Reading mode | Ctrl Shift R | story |
| `moveWidget` | Pick up a widget · move it | Space then arrows | story, widget focused |

System keys not listed in K14 and not remappable: Alt ← / Alt → (history back/forward outside a story line), Ctrl + / Ctrl − / Ctrl 0 (zoom), F2 (rename the focused story), Del (delete the focused item, opens its confirm), Shift F10 and the Menu key (context menu), F6 (next region), Ctrl Z (undo while an Undo toast shows), Ctrl C / X / V / A in text.

**Conflicts by design**: Alt ← is “previous take” when a line or the last reply has focus in a story, and “back” everywhere else. Esc closes the top overlay first; with none open it stops a streaming reply; with neither it leaves reading mode / Backstage / widget edit; with nothing at all it leaves the story.

**Sequences** (G then H): the second key within 1 s; ignored while focus is in a text field.

## Remapping (K15)

1. Click a row or press Enter on it → the row shows “Press the new keys…” and Cancel.
2. The first non-modifier key, with the modifiers held, is the new combination. Esc cancels.
3. Taken by another action → SHORTCUT_TAKEN inline with **Use it here** (unassigns the other, which shows “Not set”) · **Pick other keys**. Reserved (Alt F4, Ctrl Alt Del, Win + any, Alt Tab, F11, Ctrl + / − / 0) → SHORTCUT_RESERVED.
4. Saved at once; toast `toast.shortcut.changed` with Undo. **Reset all** restores the defaults after a confirm.

## Focus order

### Sky pages
Skip link → Rail (one tab stop; ↑ ↓ move between items, Enter goes) → New character → the page’s top bar (persona, search) → page content in reading order → page footer links. Card grids and story lists are one tab stop each with arrow-key movement inside (roving tabindex); Enter opens, the Menu key opens the item’s menu. Settings: Rail → SideNav (one stop, ↑ ↓) → panel rows in order.

### Dialogs and sheets
First field (or least destructive button) → body in order → footer buttons (Cancel first) → ✕. Tab wraps inside. Esc closes (asking first if dirty).

### The Scene
Landing on `/story/:id` focuses the composer. **F6** cycles regions: header (cloud, name, Backstage, Search, ···) → story (the lines; ↑ ↓ move line to line, each line focusable, Enter opens its tools) → composer → widgets (one stop, arrows between widgets, Enter opens the card, Space picks up in edit mode). Tab follows the same order.

## What the keyboard must reach that the mouse reaches by hover

- Character card quick actions (Continue, ···): shown when the card has focus.
- Line tools: shown when the line has focus.
- Stamps (exact times): shown on focus.
- Widget pin/remove: in edit mode, on focus.
- Focus circle in F5: arrow keys (1%), Shift arrows (10%).
