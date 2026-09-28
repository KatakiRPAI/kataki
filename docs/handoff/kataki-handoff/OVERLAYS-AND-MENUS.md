# Overlays and menus

Every dialog, sheet, popover, menu, toast and tooltip in Kataki. Boards are referenced by code; `SCREENS.md` and `SCENE.md` describe their contents in context.

## The overlay system

- One **overlay stack** in the renderer store: `{ id, type, props, openerId }[]`. Opening pushes; closing pops and moves focus back to the element with `openerId`. Overlays never touch the URL or history.
- **Types and layers** (z-order, low to high): tooltip < menu / popover < sheet < dialog < toast < takeover. A dialog may open one confirm dialog above itself; nothing deeper.
- **Dim**: dialogs and sheets dim the page (`.ov__dim`, `--dim`; in a story `rgba(20,12,6,.55)`). Menus, popovers and toasts don’t.
- **Focus**: dialogs and sheets trap focus (`aria-modal="true"`), move focus to the first field, or to the least destructive button when there is no field. Menus move focus to the first enabled item. Popovers move focus inside and close when focus leaves them.
- **Closing**:
  - Esc closes the top overlay. If it has unsaved input, Esc and clicking the dim ask first (DiscardChanges F7 wording, scoped: “Close without saving?”).
  - Clicking the dim closes sheets and non-destructive dialogs. It never closes a confirm-delete dialog or a running process (ExportAll, import).
  - Every dialog and sheet has a ✕ (`IconButton` “Close”).
- **Scroll**: the page under a dialog or sheet doesn’t scroll. Long dialog bodies scroll inside `.dlg__body` with the head and foot fixed.
- **Sizes**: `.dlg` 560 · `.dlg--sm` 440 · `.dlg--lg` 760 · `.dlg--xl` 960; `max-width: calc(100% - 48px)`. Side sheets are 560 wide, inset 20 (Sky) or 460 (Scene story settings); the character card `Sheet` is 420. Dialogs centre in the window (`.ov__win`); the palette sits 96 from the top (`.ov__win--top`); popovers anchor to their trigger (`.ov__at`).
- **Buttons**: at most one primary per overlay, at the inline-end of the footer. Destructive primaries use the danger variant. Cancel is always the first button in the footer group. The footer note sits at inline-start.
- **Motion**: dialogs fade and rise 8 px over 160 ms; sheets slide from the inline-end over 220 ms; menus fade over 100 ms. Reduced motion: fade only, 100 ms.

## Catalogue

`D` dialog · `S` sheet · `P` popover · `M` menu · `C` command surface · `T` takeover. “Writes” is what confirming changes in the library.

### Sky

| # | Overlay | Type | Board | Opened by | Primary | Writes |
|---|---|---|---|---|---|---|
| 1 | Crash recovered | D | A3 | launch after an unclean exit | Continue the story | `general.askAfterCrash` |
| 2 | Start with an empty library | D sm | A2 | “Start with an empty library” | Start empty | new library; old one untouched |
| 3 | You are (first-run persona) | D | B6 | Change on B5 | Save | default persona |
| 4 | Stop downloading? | D sm | B2 | Cancel on B2 | Stop | — (partial kept) |
| 5 | Playing as | M | C4 | persona switch, Ctrl P | — | default persona / story persona |
| 6 | Command palette | C | C5–C7 | Ctrl K, top-bar search | the highlighted item | — |
| 7 | Import cards | D lg | D4 | Import cards, file drop | Import {n} | characters, places, plots |
| 8 | New group | D | D5 | New group | Make the group | group |
| 9 | Every memory | S | E3 | All {n} memories | — | — |
| 10 | Make {name} forget | D lg | E4 | Make him forget, MemoryMenu › Forget | Forget {n} | memory.forgottenAt |
| 11 | Delete {name}? | D | E5 | CharacterMenu › Delete | Delete {name} | soft delete (and optionally their stories), purged after the Undo toast |
| 12 | Kataki’s portraits | D xl | F4 | Pick from Kataki’s set | Use this one | portrait |
| 13 | Crop and focus | D xl | F5 | after choosing a file · Crop and focus | Use it | portrait file, focus, alt |
| 14 | Leave without saving? | D sm | F7 | leaving a dirty form | Save and leave (Discard changes is danger) | the form, or nothing |
| 15 | Who is in it | D | G3 | Find on New story | Done | — (selection) |
| 16 | Rename | P | H4 | StoryMenu › Rename, F2 | Rename | story.name |
| 17 | Delete “{story}”? | D | H5 | StoryMenu › Delete | Delete story | soft delete + optional forget |
| 18 | Export “{story}” | D | H6 | StoryMenu › Export, Scene menu | Export | files outside the library |
| 19 | A place | S | I3 | a place card | New story here | — |
| 20 | A plot | S | I4 | a plot card | New story from this plot | — |
| 21 | New place | D lg | I5 | New place, “New place” anywhere | Make the place | place |
| 22 | New plot | D lg | I6 | New plot | Make the plot | plot |
| 23 | New book | D | I7 | New book, “New book…” in selects | Make the book | book, moves items into it |
| 24 | File a place | P | I8 | File it | File it | place.bookId / storyId |
| 25 | Edit persona / New persona | D lg | J2 | Edit persona, New persona | Save | persona |
| 26 | Delete a persona | D | J3 | Delete this persona | Delete the persona | persona deleted, optional forget |
| 27 | Add an online model | D lg | K7 | Add an online model | Add it | connection + key in keychain |
| 28 | Servers on this computer | D lg | K8 | Look for servers | Done | connections |
| 29 | Exporting everything | D | K11 | Export everything | Open the folder (when done) | files outside the library |
| 30 | Backups | D lg | K12 | Automatic backups › Change | Save | backup settings; Restore replaces the library after backing it up |
| 31 | Delete something | D lg | K13 | Delete something | Delete everything / the chosen item’s dialog | everything or one item |
| 32 | Licences | D lg | K18 | Licences | Close | — |
| 33 | Tell us something (Feedback · Bug · Suggestion · results) | D lg | L1–L4 | Rail Feedback, Ctrl Shift F, About, BugReport links | Send | Outbox (only if offline) |

### In a story

| # | Overlay | Type | Board | Opened by | Primary | Writes |
|---|---|---|---|---|---|---|
| 34 | Story menu | M | P2 | ··· in the header | — | — |
| 35 | Editing widgets (+ Add widget menu) | mode + M | P3 | Ctrl E, Story menu | Done | story.widgetLayout |
| 36 | How your line is read | M | P7 | the mode chip | — | the line’s mode |
| 37 | Pass time | P | P11 | clock, Advanced composer, Story menu, Ctrl Enter | Pass time | story clock, presence, fade (one transaction) |
| 38 | The time skip | full-scene status | P12 | Pass time confirmed | — (Undo) | — |
| 39 | Music and ambience | P | P14 | music widget | — | story music, uploads |
| 40 | A character’s card | S | P15 | a character widget | Let him answer next | presence / next speaker |
| 41 | Scene and place | D | P17 | Story menu › Scene and place | Change the scene | place, time of day, weather, presence |
| 42 | Story settings | S | P18 | Story menu › Story settings | — (saves as it changes) | story settings |
| 43 | Find in this story | P | M2 | search button, Ctrl F | — | — |
| 44 | Rewind to here? | D sm | — | LineMenu › Rewind to here… | Rewind | lines removed (kept in edit history) |
| 45 | Delete this line? | D sm | — | LineMenu › Delete this line… | Delete | line removed |
| 46 | Backstage | mode | Q1–Q5 | toggle, Ctrl B | — | — (run this stage again is an explicit model call) |

### Takeovers

| # | Takeover | Board | When |
|---|---|---|---|
| 47 | Disk full / read-only | N2 | a write fails with ENOSPC / EROFS / EACCES |
| 48 | Already open | N3 | the single-instance handoff times out |

**48 overlays** in all, plus the 22 menus below (which include #5, #34 and #36).

## Menus

All menus are the DS `Menu` (Sky) or `.k-menu--scene` (Scene). Items: icon or avatar, label, optional detail line, optional shortcut, optional check. Danger items are last, after a divider. Disabled items stay visible with the reason as their detail. `role="menu"`, items `menuitem` or `menuitemradio`. ↑ ↓ Home End move, type-ahead jumps, Enter/Space picks, Esc and Tab close.

**Placement**: below the trigger, aligned to its start; flips above when there isn’t room; 8 px from the trigger, 16 px from the window edge. Context menus open at the pointer.

### Sky (M1)

| Menu | Where | Items, in order |
|---|---|---|
| PersonaMenu | top-bar persona switch · Ctrl P | title “Playing as” · each persona (avatar; meta “default” on the default; ✓ current) · Director · play no one · — · New persona · Manage personas · footer “Switching changes who you are in new lines. Stories you already started keep their persona.” |
| StoryMenu | StoryCard ··· / right-click (Home, Stories, Search) | Continue · Rename (F2) · Pin to Home / Unpin · Move to a book… · Branch a copy · Export… · — · Delete story… (Del) |
| CharacterMenu | CharacterCard ··· / right-click, profile header | Continue (“the last story with {name}”) · New story with {name} · Edit · Favourite / Unfavourite · Duplicate · Export card… (“PNG with the card inside, or JSON”) · — · Delete {name}… |
| GroupMenu | group row ··· (Characters › Groups) | New story with this group · Edit group · Duplicate · — · Delete group… (“the characters stay”) |
| SortMenu | Sort on Stories (Characters and World sort with the same pattern and their own lists, `SCREENS.md`) | title “Sort by” · Recently played ✓ · Recently written · Story time · Name, A to Z |
| FilterMenu | Characters filter chips as a menu below 1280 wide · one at a time | title “Show” · All {n} · In a story {n} · Favourites {n} · Drafts {n} · Also a persona {n} |
| PlaceMenu | PlaceCard ··· / I3 | New story here · Edit · Change the picture… · Duplicate · — · Delete place… (“stories keep their copy”) |
| PlotMenu | PlotCard ··· / I4 | Drop into a story… · Edit · Duplicate · — · Delete plot… |
| BookMenu | a book in World’s book list (··· or right-click) | Rename book · Change the cover… · New story in this book · — · Delete book… (“its stories stay, unbooked”) |
| MemoryMenu | MemoryRow ··· (E3, Q4) | Edit the wording · Make it sharp again · Keep it from fading · — · Forget this… |
| PersonaCardMenu | PersonaCard ··· (You) | Play as {name} · Edit · Duplicate · — · Delete persona… (disabled for the default: “pick another default first”) |
| ConnectionMenu | ConnectionRow ··· (Models) | Use for everything · Test again · Edit address or key · Use for one job… (disabled unless Advanced: “turn on Advanced first”) · — · Remove connection… |
| TextMenu | right-click in any text field or line, Sky and Scene | section Spelling · up to 3 suggestions · Add to dictionary · — · Cut (Ctrl X) · Copy (Ctrl C) · Paste (Ctrl V) · Select all (Ctrl A). Electron has no default context menu: build it with `webContents` `context-menu` + the spell-checker API. |

### In a story (M2)

| Menu | Where | Items, in order |
|---|---|---|
| SceneStoryMenu | ··· in the header | Edit widgets (“Move, pin, remove or add”, Ctrl E) · Reading mode (“Just the story”, Ctrl Shift R) · Scene and place (“Where, when, who is here”) · Pass time (“Skip ahead in the story”) · Drop in a plot… (“Start something from World”) · Backstage (“How replies are made”, Ctrl B) · Story settings (“Persona, book, models, memory”) · — · Export story… · Pin to Home · Tell us something (Ctrl Shift F) · — · Delete story… |
| LineMenu | right-click a line / ··· in LineTools | Copy the line · Edit (↑ for your last line) · New take (Ctrl R, replies only) · Hide from the story · Branch a new story from here · — · Rewind to here… (“removes the {n} lines after it”) · Delete this line… |
| CharacterWidgetMenu | right-click a character widget | Open {name}’s card · Let {him/her/them} answer next · Send {him/her/them} away · Pin / Unpin (“shows only when {he} acts”) · — · Remove widget |
| WhoAnswersMenu | Advanced composer, ··· after the Answers chips | title “Who answers next” · Whoever fits (“Kataki decides”) · each present character · away characters disabled (“away · send for {him} first”) · The narrator · Nobody (“I’ll keep going”) |
| WidgetMenu | right-click any other widget | Unpin · Duplicate · Move (Space) · — · Remove widget · Edit all widgets (Ctrl E) |
| ClockMenu | right-click the clock | Pass time… · Show the real date (“{date}, by the story’s calendar”) · Set the time… · — · Remove widget |
| MusicMenu | right-click the music widget | Pause · Next track · Match the scene ✓ · Choose… · Mute (Ctrl M) · — · Remove widget |
| AddWidgetMenu | Add widget in edit mode | Character (“Pick who. As many as you like.” + avatar chips) · Story clock · Music · Place · Cast · Notes |
| ModeMenu | the composer mode chip | Auto · Say · Do · Whisper · Think · Narrate (radio; each with its syntax); foot: “Auto works it out from how you write. Pick a mode to override it for this line.” |

### FindInStory (M2)

Popover under the header search button, Ctrl F. Search field; results as rows `{speaker} · {time} · {scene}` + the line with the match marked; `{i} of {n}` and “Esc to close”. Enter jumps to the next match (the line flashes), Shift Enter to the previous. Searches the whole story, not just loaded lines.

## Toasts (M3)

`Toast` component. Sky: bottom centre, 24 from the bottom. Scene: centred above the composer. One at a time; newer replace older, which go to a queue if they carry an action. `role="status"` (polite); `tone="bad"` toasts use `role="alert"`.

| Kind | Duration | Rule |
|---|---|---|
| With Undo | 10 s | Ctrl Z also undoes while it shows. Paused on hover and focus. The action is soft until the toast expires. |
| Done | 6 s | No action, or one that opens the result. |
| Background / problem | 6 s, or until dismissed when it has an action | A problem toast never carries the only copy of an error: the error also shows in its own place. |

| id | Icon | Text | Action |
|---|---|---|---|
| toast.story.deleted | trash | {story} was deleted | Undo |
| toast.character.deleted | trash | {name} was deleted · {his} {n} stories kept {him} as {he} was | Undo |
| toast.memory.forgotten | eyeoff | {name} forgot {n, plural, one {one memory} other {# memories}} | Undo |
| toast.story.moved | book | Moved to {book} | Undo |
| toast.story.pinned | pushpin | Pinned to Home | Undo |
| toast.line.hidden | eyeoff | Line hidden from the story | Undo |
| toast.shortcut.changed | key | {action} is now {keys} | Undo |
| toast.story.renamed | check | Renamed to {story} | — |
| toast.export.done | download | Saved to {folder} as {file} | Show |
| toast.import.done | download | Imported {n} characters · {skipped} skipped | See why |
| toast.backup.done | shield | Backup made · {time} | — |
| toast.copied | check | Copied | — |
| toast.feedback.sent | check | Sent. Thank you. | — |
| toast.persona.switched | user | Playing as {name} from the next line | — |
| toast.model.back | check | The model is back · {n} replies caught up | — |
| toast.download.done | check | Kataki’s own model is ready | — |
| toast.update.ready | download | {version} installs when you close Kataki | Restart now |
| toast.feedback.queued | cloud | You’re offline · it sends when you’re back · FEEDBACK_OFFLINE | — |
| toast.music.unsupported | volume | That file won’t play · mp3, ogg or wav · MUSIC_UNSUPPORTED | Choose another |
| toast.narrator.failed | feather | The narrator couldn’t add a line · NARRATOR_FAILED | Try again |
| toast.export.failed | alert | Couldn’t save to that folder · EXPORT_WRITE_FAILED | Choose a folder |
| toast.renderer.fallback | alert | The graphics driver restarted · RENDERER_FALLBACK | Restart |
| toast.notFound | alert | That {thing} isn’t in your library any more | — |
| toast.zoom.cap | eye | Make the window wider to go past {max}% | — |

## Tooltips

`Tooltip` on every icon-only button (its `label`), on compact-rail items, on truncated names, and on relative times (the exact time via `Stamp`). 500 ms delay on hover, immediate on keyboard focus, hides on Esc. Never holds information that isn’t also available another way.
