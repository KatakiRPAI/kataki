# Screens

## Sky v2 · the direction to build

29 screens: every destination, every settings panel, every menu, the states, and four v2.1 proof boards. Written up in `../research/SKY-V2.md` (v2.1 at the end). Every Sky v2 and Scene screen passes WCAG AA text contrast against its rendered pixels — 2,354 text runs, 0 failures.

| # | File | Screen |
|---|---|---|
| 1 | `Sky2-Home.html` | Home |
| 2 | `Sky2-Profile.html` | Mike’s profile |
| 3 | `Sky2-Stories.html` | Stories |
| 4 | `Sky2-World.html` | World · places and plots |
| 5 | `Sky2-FirstRun.html` | First run · step 1 |
| 6 | `Sky2-Characters.html` | Characters |
| 7 | `Sky2-You.html` | You · personas |
| 8 | `Sky2-AddCharacter.html` | New character |
| 9 | `Sky2-NewStory.html` | New story |
| 10 | `Sky2-FirstRun2.html` | First run · step 2 |
| 11 | `Sky2-Palette.html` | Command palette |
| 12 | `Sky2-Search.html` | Search results |
| 13 | `Sky2-Menus.html` | Every menu |
| 14 | `Sky2-Empty.html` | Empty · day one |
| 15 | `Sky2-Error.html` | The model server went away |
| 16 | `Sky2-Feedback.html` | Feedback and bug report |
| 17 | `Sky2-Loading.html` | Opening |
| 18 | `Sky2-Set-General.html` | Settings · General |
| 19 | `Sky2-Set-Appearance.html` | Settings · Appearance |
| 20 | `Sky2-Set-Language.html` | Settings · Language |
| 21 | `Sky2-Set-Models.html` | Settings · Models |
| 22 | `Sky2-Set-Memory.html` | Settings · Memory and thinking |
| 23 | `Sky2-Set-Data.html` | Settings · Data and privacy |
| 24 | `Sky2-Set-Shortcuts.html` | Settings · Shortcuts |
| 25 | `Sky2-Set-About.html` | Settings · About and feedback |
| 26 | `Sky2-Home-Day.html` | **Proof · Day.** The same Home in the second theme: its own palette, a daylight sky with sun and cloud. Same token names. |
| 27 | `Sky2-Home-Compact.html` | **Proof · 1024 wide.** The rail folds to 72px icons (labels kept for screen readers), four characters instead of five, the still narrows to 360. |
| 28 | `Sky2-Home-Arabic.html` | **Proof · Arabic, right to left.** Mirrored by logical properties alone; Baloo Bhaijaan 2 / IBM Plex Sans Arabic / Noto Naskh Arabic; no tracking or italics; one English story left in on purpose, isolated with `<bdi>`. |
| 29 | `Sky2-Access.html` | **Proof · Accessibility, measured.** Audit totals, the contrast matrix for both themes computed from the tokens, the focus ring, Home's keyboard order, reduced-motion substitutions, text at 200%, target sizes. |

The five core screens are 1–5; 6–10 are the making flows and the rest of first run; 11–15 are finding things and every menu; 16–17 the feedback dialog and cold start; 18–25 are Settings; 26–29 are the v2.1 proof boards.

---


There are 71 screens: the 29 of **Sky v2** (the chosen direction — start with those), 27 of the original design, and 15 style studies. Most are 1440×900 desktop, except Home (1440×1190), Mike's profile (1440×1500), Places and Plots (1440×1400) and Models (1440×1000), which scroll. Each has a static page in `html/` and a screenshot in `png/`. Links between pages work: the orb, cards, menu items and "Open the line".

Sample content throughout is the world in `sample-world/`: you play **Liv**, the queen's step-sister's daughter, in **"Two Sugars, No Title"** with **Mike**, whose mother does the queen's hair. **Theo**, **Nico**, **Jae** and the half-finished **Dani** fill the rest. The story runs from **Halcyon Coffee** on the evening it rained to **Corvel Palace** three weeks later.

## The Scene (inside a story)

> **v2.1:** the Scene now uses the Sky's surfaces — navy glass over the painted place, `#eef2ff` ink, a flat blue Send, amber kept for memory. The descriptions below still hold for layout and behaviour; where they mention colour, the screenshots win.

The chat runs the full height of the window, in the middle (800 wide). Everything else is a **widget**: by default Mike's character widget on the right, and the story clock and music at the bottom left. The user can move, pin, remove and add widgets from ⋯ → Edit widgets. The chat shows how characters feel; who-heard-what and who-answers live behind the composer's **Advanced** toggle.

| # | File | What it demonstrates |
|---|---|---|
| 1 | `Scene-OneToOne.html` | **The default.** The full-height chat with a title card ("Halcyon Coffee · the evening it rained") and two lines. The hovered line shows its tools pill, and the time tooltip reads "19:02 · 24 May · the evening it rained". Widgets: Mike (pinned, "calm", status `Here · fond of you`), Theo as a compact row ("Out back · could join"), the story clock (7:04 pm, "The evening it rained") and music. The composer is Simple: text, Simple/Advanced, Continue, **Auto**, Send. |
| 2 | `Scene-Menu.html` | The ⋯ story menu open: **Edit widgets**, Reading mode, Scene and place, Story settings, Export story, Delete story. |
| 3 | `Scene-EditWidgets.html` | **Editing widgets.** A dot grid over a dimmed scene, and a top bar ("Drag anywhere · pinned ones stay visible, unpinned ones appear when something happens", Reset layout, Done). Each widget has a dashed outline, a drag handle, Pin and Remove. Theo's widget is mid-drag over the chat, with its empty slot left behind. The **Add widget** list is open: Character (with "Character widget for…" Mike / Theo / Nico / Jae), Story clock, Music, Place, Cast, Notes. |
| 4 | `Scene-Group-Joins.html` | **Theo joins.** A story note "Theo joins." and the reaction "Mike is wary of Theo". Two character widgets: Mike ("wary") and Theo, who has just appeared with a "Joined" badge and is unpinned. |
| 5 | `Scene-Group-Secret.html` | **Feelings, not hearing.** "Theo didn't like that", "Theo is suspicious of you", "Theo went out to the back", then Liv's secret — her mother is the queen's step-sister — with "Mike will remember this" and "Mike trusts you a little more", then "Mike is worried for you". No receipts anywhere. Mike's widget: "uneasy", status `Here · trust +6 this scene`. |
| 6 | `Scene-Advanced.html` | **Advanced composer.** "Only Mike will hear this · Theo is away", Answers (Whoever fits, Mike, Narrator), Pass time, a token count and meter. The hovered line shows "Mike heard it" / "Theo wasn't there"; these chips only appear in Advanced. |
| 7 | `Scene-ModePicker.html` | **Auto and the mode menu.** The user has typed `*leans over the counter* Then don't tell anyone you saw me here.` and the chip reads "Auto · Do + Say". The menu is open: Auto, Say, Do, Whisper, Think, Narrate, each with its syntax. |
| 8 | `Scene-EditLine.html` | **Editing a line** five messages back. The line becomes an editor with the warning "Regenerating from here rewrites the 5 messages after this one…", Cancel, **Save edit** (only changes what the model reads next), and **Save and regenerate from here**. The lines that would be rewritten are dimmed. |
| 9 | `Scene-Reply.html` | **A reply arriving.** Mike's line streams with an amber caret ("writing…", "Thought for 4 s"). His widget shows "thinking…". The composer shows Stop. |
| 10 | `Scene-TimeSkip.html` | **The time skip, readable.** A night veil and rolling moonlit cloud cover everything (widgets included), and a solid navy card holds the text: "Three weeks later", "The evening it rained → Three weeks later · the gala", "Mike's memory of that evening is going hazy.", Undo. |
| 11 | `Scene-AfterSkip.html` | **Three weeks later, at the gala.** The place has crossfaded to Corvel Palace at night. A "Three weeks later · Corvel Palace" title card with Undo. Mike's 7:18 pm line has a time tooltip ("19:18 · three weeks after the café · the night of the gala"), the recall box "Mike remembered, vaguely — she didn't want to be on the gala list · sharp 3 weeks ago · hazy now", and "Mike is glad to see you". His 7:22 pm line has "Mike has his doubts". Widgets: Mike "doubtful", Theo "Not invited · three weeks", the clock with its 24-hour hover. |
| 12 | `Scene-MusicPicker.html` | **Choosing music**, opened from the music widget: "Match the scene", the matched track, ambience and music, a user upload, **Upload a track…** (mp3, ogg, wav), and volume. |
| 13 | `Scene-Peek.html` | **Mike's card**, opened from his widget: Right now (where, scene, here since), How he feels about you (warmth, trust, doubt), Holding onto (a stored memory, doubted), relationships, the Secret, and actions. **Add as widget** in the header. |
| 14 | `Scene-Backstage.html` | **Backstage · the mind.** The Mind graph for Mike's last reply: IN (heard, saw, place, time) → SENSE (perception, attention) → INSIDE (recall, feeling, belief, goals, persona) → DECIDE (intent, expression), with the winning path in gold. Also "Spoke", and "How he feels about Liv, across the story". On the right: Prompt, Cast, and Engine · this turn. Memory is one node plus a "Memory · 41" link. |

## The original Sky (superseded by Sky v2 — reference only)

The rail reads Home · **Characters** · Chats · **Places & Plots** · Activity · You. Outside a story, times are real-world ("Played 2 hours ago"); story dates only appear as the second line, with the exact count on hover.

| # | File | What it demonstrates |
|---|---|---|
| 15 | `Sky-Home.html` | The greeting "Good evening, Liv" with your avatar (with a switch badge, opens the persona switcher). Search, the Activity bell (4), "Add a character". **Continue card** (the last scene still, Mike's last line, "3 new memory events", orb "Dive back in"). An Activity preview. **Characters** with candy filters (All, Favourites, In a story, New, Groups), 5 cards showing when you last played with each ("Played 2 hours ago", Dani "Never played" with a 60% ring) and an Add card. **Moments** (2 composed stills). |
| 16 | `Sky-Profile-Mike.html` | **Profile before messaging.** A big portrait with name plate, "Played 2 hours ago" and tags. A "Last played 2 hours ago" tile (hover: "Today, 7:12 pm · Halcyon Coffee"), while in-story rows read "three weeks later" with the Year/Day count on hover. "Message Mike" (continues the latest story, with orb), "Start a new story", "Start a group scene", "Edit profile". 3 stat tiles. A **Right now** living-profile card with a story selector and memory bar. About (plus "Also known as"). How he talks and How he says hi as bubbles. The Secret. Relationships, Stories together, Places she's been, Moments. |
| 17 | `Sky-AddCharacter.html` | **Add a character**, step 3 of 6 ("Their secret") for Dani: stepper, big textarea, "Stuck? Start from" prompt chips, Back / Skip / Next. A live profile card filling in on the right, with a 60% ring: "Add a secret to make Dani more real". |
| 18 | `Sky-Chats.html` | Thread list: New chat, New group scene, filter chips, a Pinned thread (stacked avatars, "2 h ago", "as Liv · three weeks later", memory badge 3), and 3 othis stories, each with the real time since you played. The selected thread's preview: the last-moment still, Dive in orb, In this story (who's there, what they know), and New since you left. |
| 19 | `Sky-Library.html` | **Places and Plots.** One tab for both. The filter panel: Everything, BOOKS as a tree (Close to the Crown → its two stories, The Flat on Ardenne → Three in the Morning), "Not in a book", and character chips (Mike selected). Tabs All · Places · Plots, sorted by Recently used. Cards grouped by book: Halcyon Coffee and Harbour Market (each with a dawn/day/dusk/night strip, link chips and the faces of who knows them), The Missing Ledger and Frost on the Pass as plots, and The Lighthouse unlinked with the **Link to…** dialog open (Book, Stories, Characters who know it). |
| 20 | `Sky-You.html` | The **persona switcher** open (Liv ✓, Cas, Director · play no one, New persona, and a footnote). **Your profile**: "Played by you" badge, Who knows Liv (per character, per story), Liv's chats. |
| 21 | `Sky-Activity.html` | Activity grouped by when you played (Today, Yesterday) and story, with kind filters. Items carry the story date and the real time. One item is expanded to show the quoted line with "Open the line". Side cards: "Still being read" (with Read now) and a "How receipts fade" legend. |
| 22 | `Sky-FirstRun.html` | "They'll remember this." over clouds, and the promise line. Three steps: **Connect a model** (active; found llama.cpp on this computer, Use this, Look again, or add an online API), Make yourself, Add your first friend. A privacy line and Continue. |
| 23 | `Sky-Models.html` | Settings subnav. Models with "engine ok". Servers and APIs (llama.cpp connected with qwen3.5-9b loaded; OpenRouter with "key stored"; Test and Remove). "Look for model servers on this computer", "Add an API". Jobs: Characters expanded with every field; Narrator, Memory reader, Reasoning and Recall by meaning collapsed. |

## The original Sky · dark (superseded)

The same four screens in dark mode, to show the theme across a page of glass, a page of art, a list and a grid. Every other Sky screen themes from the same tokens.

| # | File | What it demonstrates |
|---|---|---|
| 24 | `Sky-Home-Dark.html` | Night above the clouds: stars, moonlight from the top right, moonlit clouds. The Continue card and character art are untouched; the candy filters and the orb still carry the colour. "Add a character" is now a filled blue pill. |
| 25 | `Sky-Profile-Mike-Dark.html` | A page that is mostly art and cards: portrait plate, stat tiles, the memory bar, and the secret card (which was already dark and now sits with everything else). |
| 26 | `Sky-Chats-Dark.html` | A list: the selected thread uses the solid card colour rather than white, and the story preview keeps its full-colour still. |
| 27 | `Sky-Library-Dark.html` | A grid: place cards with their dawn/day/dusk/night strips, plot cards, the filter tree, and the Link dialog. |

## Interaction notes per screen

- **Every Sky screen:** the rail's orb and the Continue card dive into `Scene-OneToOne` (the last scene). Friend cards open the profile, and Activity items open the line.
- **Every Scene screen:** the cloud button (top left) floats back up to the Sky. The Backstage switch toggles the lens in place. Clicking a character widget opens that character's card.
- **One screen, many states:** widgets appearing, the composer toggle, the menus, editing, the reply and the time skip are all states of one Scene screen, not separate pages. Animate between them; don't navigate.
- **Dark mode** is a token flip (`data-theme="dark"`), not a separate layout. Only the Sky has two themes.
- **Widget layout** is saved per story. New stories start from the default: characters on the right, clock and music at the bottom left.

## Five style directions (proposals, not the current design)

Fifteen screens — five directions × Home, Mike's profile, First run — set out in `../research/STYLE-DIRECTIONS.md`. They all carry the same information architecture, which comes from `../research/UX-STUDY.md`: Home led by the continue block, a five-item rail with Feedback in the footer, no Activity destination, `Ctrl K` search, no glass on page chrome, no stat tiles, and a first run whose first door needs no configuration.

| # | Files | Direction |
|---|---|---|
| 28–30 | `Style-A-Home.html` · `Style-A-Profile.html` · `Style-A-FirstRun.html` | **Paper & Ink** — editorial. Warm paper, hairlines, Fraunces, oxblood, no shadow. |
| 31–33 | `Style-B-*.html` | **Night Theatre** — dark-first. Warm near-black surface ladder, amber lamplight, character key art, Instrument Serif. |
| 34–36 | `Style-C-*.html` | **Daylight** — calm modern. Opaque white cards, a sky band instead of a wash, sea-green accent, Bricolage Grotesque. |
| 37–39 | `Style-D-*.html` | **Storybook** — illustrated. Painted card stock, a deck of angled character cards, taped stills with captions, Young Serif. |
| 40–42 | `Style-E-*.html` | **Night Storybook** — the mix. The night sky as the ground (stars, moonlight, moonlit cloud), with Storybook's angled deck and taped stills in dark card stock whose top edges catch the lamplight, and Night Theatre's discipline: lamplight amber accent, no glass, contained portraits. |

These screens use webfonts from Google Fonts as a fallback; the local files in `../assets/fonts/` only cover the current design's four faces. Whichever direction is chosen, its faces have to be vendored locally before shipping — the app is local-first.
