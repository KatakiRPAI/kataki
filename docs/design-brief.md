# Kataki RPAI: UI design brief

## What to design

Design the screens of Kataki RPAI, a desktop app for AI role-play with characters who remember. The deliverable is the list under "Screens to produce". Start with the one-to-one Scene and Home.

The app has two worlds, each with its own mood:

- **The Sky** is everything outside a story: a social app where your characters are friends with profiles, and starting a role-play feels like messaging one of them. Cloudy and fun.
- **The Scene** is inside a story: an intimate, cinematic room where you are with the character. The place is lit, the character is there, the atmosphere is real.

Design the full vision. Generated images, music and some of the features below are still being built. Today's app is plain and text-only, so everything visual is open, and every feature under "Reference: what the app does today" stays reachable somewhere.

An attached mood image, if there is one, inspires the Sky only: take its vibe, not its layout.

## The product in one paragraph

Kataki RPAI is a local-first desktop app for AI role-play. You add characters the way you add friends, filling in their profile: who they are, how they talk, a secret only they know. Then you message one, and the conversation opens as a scene: the place around you, the character in front of you, and a story you write together. Others join and leave as the story goes. What sets Kataki apart is memory: each character remembers only what they saw or were told, memories fade with story time from sharp to hazy to forgotten, and a character who is told a lie challenges it if they remember clearly. The app ships no AI model; users connect a model server on their own computer or an online API.

## Two worlds

### The Sky (outside a story)

A bright day above the clouds. Soft sky-blue to periwinkle gradients, drifting clouds, frosted-glass cards with thin white borders and soft shadows, generous rounded corners, pill-shaped chips and tabs, glossy candy-coloured 3D icons, and bubbly hand-lettered display type for big moments. Friendly greetings ("Good evening, Aren"). Playful motion: things float, bounce and settle. Characters appear as big, bright portrait art.

Areas (names are suggestions): Home; Friends (your characters); Chats (your stories, one thread each, one-to-one or group); Places and Plots; You (your profile and the characters you play); Activity; Settings, including Models. A glowing orb, always within reach, dives back into your last scene.

### The Scene (inside a story)

Evening in a real place, with someone you know. The place fills the window, lit by the story's time of day. The character stands in it, with an expression that changes as they talk. Warm low light, a soft vignette, a little film grain, and book-quality type for the story. Controls appear when needed and fade while you read.

### The dive

Opening a chat dives down through the clouds: they part, and the scene fades in. Leaving floats back up, and the thread keeps a still frame of the last moment as its cover. This crossing is the app's signature transition.

## Signature features

No other role-play app does these, so make them unmistakable.

1. **Living profiles.** A character's profile fills itself in from your stories: where they were last seen, what they are holding or wearing, who they trust, how much they remember about you, and the moments you shared.
2. **Memory receipts.** Read receipts from messaging apps, reinvented. Every line carries small avatars of who heard it, and absent characters show as "wasn't there". Once the memory reader has filed the line, the avatars of those who will remember it light up. As story time passes they fade with the memory: solid when sharp, soft when hazy, gone when forgotten.
3. **Callouts and reactions.** When a moment matters, the character says so, like a message reaction. Memory: "Mira will remember this". Feelings: "Tobin didn't like that", "Mira trusts you a little more", "Tobin is suspicious of you". Beliefs, when you tell them something: "Mira knows that's not true" (she remembers clearly), "Mira has her doubts" (her memory is hazy), "Mira believed you" (she has no memory of it).
4. **A living stage.** The place is lit by the story clock (dawn, day, dusk, night) and moves a little: rain on the windows, lamplight flicker, drifting smoke, slow parallax. Characters change expression. The speaker comes into focus while the others soften. Ambient sound and music follow the scene.
5. **Arrivals and departures.** Only the people in the scene are on stage. A one-to-one chat shows just that character, up close. When someone joins, whether you bring them in or the story introduces them, they step onto the stage and the layout makes room. They stay until they leave, then step off with a note that they won't hear what is said now.
6. **Who can hear you.** The composer shows who will hear your line. You can whisper to one character, or think without anyone hearing.
7. **Time you can feel.** A time skip plays as a transition ("Six years later"): the light changes, the clock rolls forward, and receipts across the conversation fade. You watch characters forget.
8. **The backstage lens.** For tinkerers, one toggle shows the scene from backstage: everything the engine knows, including memory, the prompt, the token budget and the memory reader's log.

## What the design depends on

- **Memory.** Every few turns, a background memory reader goes through the new lines and files what happened: people, places, items, events, and who witnessed or heard each one. Each memory has an importance from 1 to 10. For each character a memory is sharp (they recall the detail), hazy (only the gist, and they can be talked out of it) or forgotten. Memories fade with story time, important ones slower, and retelling refreshes them. Each records how the character learned it: witnessed, told by someone, overheard, rumor or inferred.
- **Presence.** A character who isn't in the scene hears nothing said there. This is how secrets work.
- **Story clock.** In-story time: "Day 3, 14:20", or "Year 7, Day 1, 09:30" after the first year. Each turn moves it two minutes by default; narration like "six years later" skips it, with undo.
- **You.** You play a persona (a character of your own) or direct the story as its author, playing no one.
- **Takes.** Any reply can be re-rolled into a new take, and you flip between takes. Choosing an earlier take switches the story's branch, and memory follows it.
- **Stories and chats.** A chat thread is one continuing story, so the character keeps their memories every time you come back. You can also start a fresh story with the same character; it becomes a separate thread.
- **Models.** Users connect model servers or APIs and choose a model for each job: Characters, Narrator, Memory reader, Reasoning, Recall by meaning. One model is enough to start.

### When the signals arrive

Some signals are instant. Others land a few turns later, when the memory reader has run. Design for both.

- **Instant:** who is present and hears a line; what the speaking character recalled for this reply, and how clearly; a character straining to remember; time skips; someone you bring in.
- **A few turns later:** "will remember" receipts and callouts, reactions (feelings, relationships, whether a lie was believed), arrivals and departures described in the story text, and newly met characters. These fill in quietly on the lines they belong to, like read receipts arriving, and also appear in Activity.

## The Sky, screen by screen

### First run

A welcome over clouds in big lettering, for example "They'll remember this.", with one line under it: "Characters who see, hear, remember and forget, like people do." Then three steps: connect a model (look for a model server on this computer, or add an API), make yourself (your first persona's profile), and add your first friend. It ends by opening a chat with them.

### Home

- A greeting with your avatar: "Good evening, Aren". Tapping the avatar switches who you are.
- The Continue card: a still of your last scene with the character in it, their last line, and the orb to dive back in.
- Friends: portrait cards with name, a one-line tagline and a status ("At The Gull · Year 7", "Not in a story yet"). Filter chips with 3D icons: All, Favourites, In a story, New, Groups.
- Moments: pictures of important scenes from your stories.
- An Activity preview, search, and "+ Add a friend".

### Friend profile (before you message them)

- A big portrait, name, tagline, and tag chips (Courier, Loyal, Wary).
- Stat tiles: "2 stories together", "Remembers 38 things about Aren", "Last seen: The Gull, Year 7".
- About (what anyone can see or know); How they talk (a few of their lines as bubbles); How they say hi (their opening line).
- Secret: a locked, blurred card, "Only Mira knows this", that you as the author can reveal.
- Also known as (other names); Relationships ("Distrusts Tobin", "Trusts Aren"); Places they've been; Moments; Stories together.
- The main action, "Message Mira", continues your latest story with her. Beside it: "Start a new story" and "Start a group scene". Also "Edit profile".

Memories and relationships belong to a story, so a profile shows them story by story.

### Add a friend

Build a character like a social profile, one friendly step at a time, with a live profile card filling in beside the form and a completeness ring ("Add a secret to make Mira more real"). Steps: name and portrait; who they are; their secret; how they talk; how they say hi; other names and tags.

### Chats

One thread per story: avatars (stacked for groups), the story title, the last line, the story clock in place of a real timestamp, the persona you play there ("as Aren"), and a badge for new memory events. Pinned threads sit at the top. "New chat" and "New group scene".

### You and your personas

Tapping your avatar opens a switcher, like switching accounts: your personas, each with portrait and tagline, plus "Director: play no one". The one you pick is who you are in new chats; each thread keeps the persona it started with. Your profile looks like a friend's, with a "Played by you" badge. Characters know each of your personas separately.

### Activity

Notifications from your stories:

- "Mira will remember that you hid the ledger."
- "Tobin didn't like being sent to the bar."
- "Mira has her doubts about the lighthouse."
- "Six years passed in The Third Floorboard. 12 of Mira's memories went hazy."

Tapping one opens the line it came from.

### Places and Plots

- **Places:** image cards that preview dawn, day, dusk and night, who has been there, and the stories set there, with "Start a scene here". An idea to explore: a map of places as islands in the clouds, with friends' avatars on the islands where they were last seen.
- **Plots:** a premise every character knows, plus an opening narration. "Start this plot" picks friends and a place, then dives in.

### Models (in Settings)

Friendly on the surface, exact underneath. Model servers and APIs first, then one card per job with an icon (Characters, Narrator, Memory reader, Reasoning, Recall by meaning), each showing the model it uses or "same as Characters". The fields are in the Reference section.

## The Scene, screen by screen

### The stage

- The place image fills the window, lit for the story's time of day, with light motion (rain, flicker, smoke, parallax) and ambient sound.
- In a one-to-one scene the character is large and close. With two or three present they share the stage; the speaker is lit and the others soften. At most three are drawn; anyone beyond that sits in a row of avatars.
- Expressions change with the conversation: neutral, smiling, wary, surprised, doubtful.
- Tapping a character opens their peek card.
- A tray at the edge holds characters who are away or could join. Drag someone onto the stage to bring them in, or off it to send them away.
- A quiet top bar: back up to the Sky (a cloud), the place and clock with a small sun or moon arc, what is playing ("Rain on the harbour"), the backstage lens, and a menu (story settings, delete story).
- A quieter reading mode, with text over a blurred scene, for long sessions.

### The conversation

- Each line shows the speaker, a story-clock stamp, and prose with *actions* in italics and **emphasis** in bold. Replies run from one line to several paragraphs.
- Memory receipts under lines: quiet by default, fully visible on hover.
- Callouts and reactions attach to the line they are about.
- A small spark marks a reply that drew on memory. Hovering shows what the character recalled and how clearly: "Mira remembered, vaguely: the ledger is somewhere behind the bar."
- On hover: takes (‹ 2/3 ›; the last arrow makes a new take), Edit, and Hide (the line stays in the story but never reaches the AI). Small marks for "stopped" and "edited".
- Scene changes and time skips appear as title cards in the flow.

### The composer

- Who will hear: the present characters' avatars, "Mira and Tobin will hear this", with away characters greyed.
- Modes: Say, Do (an action), Whisper (pick who hears), Think (no one hears).
- Who answers next: tap a character on stage, or leave it to whoever fits. The Narrator has its own button.
- Continue (the story goes on without a line from you), Send, and Stop while a reply is coming. A stopped reply keeps what was written.
- Pass time: a few hours, next morning, a week, years.
- A thin token meter along the composer's edge; the full numbers live backstage.
- Enter sends, Shift+Enter starts a new line. Placeholder: "Speak or act as Aren…", or "Direct the story…" when you play no one.

### A reply arriving

"Mira is thinking…" while a reasoning model works. Its raw notes stay out of the scene and are readable backstage. Then the text arrives word by word and her expression settles. When she strains to recall something, show it: "Mira is trying to remember…".

### Arrivals and departures

Someone you bring in steps onto the stage with a name card: "Tobin joins". Someone who leaves steps off: "Tobin left. He won't hear what's said now." When the story text itself says someone arrived or left, the stage follows once the memory reader notices, with an undo. Newly met people whom the narrator voices, such as a hooded stranger, appear as a lighter silhouette card.

### Time skips and new scenes

- **Time skip:** the view drifts into cloud, a title card reads "Six years later" with undo, the clock rolls forward, the light changes, and receipts across the conversation soften to hazy.
- **New scene:** "Where to?" shows places as a filmstrip, then who is there, then a cut through black to a title card: "The Lighthouse · Year 7, Day 2, dawn".
- **Optional:** time can pass while you are away. Come back after three days and three days have passed in the story: the character notices, and their memories have faded to match. A title card says so on your return.

### Character peek

A glass card over the stage:

- name and current expression
- right now: what they are holding or wearing, where they are, any injury
- on their mind: what they recalled for their last line, sharp or hazy
- what they know about you, linking into their memories
- relationships
- their secret, which only you as the author can reveal

Actions: let them answer next, send them away or bring them back, edit.

### The backstage lens

One toggle shows the set from behind: the same scene in a blueprint style, with four panels. Memory: per character, with tiers and how each was learned; pin, hide, write a memory. Prompt: what the AI was sent, its parts against their limits, recalled memories with their scores, cache reuse. Cast: everything the story knows, found characters, current state, merging duplicates. Reading: the memory reader's log, "read now", "read again carefully". The full fields are in the Reference section.

## Platform

- Desktop app (Electron), Windows first. Design at 1440×900; layouts hold from 1280 to 1920 px. Phone use over the home network is planned, so also design phone versions (390×844) of Home, a profile and the one-to-one scene.
- The AI model often runs on the same graphics card, so keep motion light: layered images, gentle transforms and crossfades, no heavy 3D.
- With reduced motion on, the stage becomes still images with crossfades. Text over images always sits on a scrim that keeps it readable.
- Keyboard-first writing, visible focus rings, and a mute that is always one click away.
- Characters are fictional: use illustrated or painted character art, never photos of real people. Keep mockups general-audience.
- Everything runs on the user's computer. API keys live in the system keychain, and text leaves the machine only for the models the user connects.

## Sample content (use it in every mockup)

**You:** Aren, "A newcomer to the docks." A second persona: Sable, "A retired privateer with a price on her head."

**Friends:**

- **Mira:** "Guild courier. Loyal to friends, wary of everyone else." Tags: Courier, Loyal, Wary. Also known as: the courier. Secret: "She reads every letter she carries." How she talks: "Coin first. Questions after." / "*taps the letter* You want it or not?" How she says hi: "*slides a sealed letter across the table* You're late."
- **Tobin:** "Cheerful smuggler. Hears everything eventually." Secret: "He would sell the guild ledger in a heartbeat."
- **Ilsa:** "A mountain guide who never loses a trail."
- **Master Oren:** "A clockmaker who collects debts, and secrets."
- **Wren:** just added; profile 60% complete.

**Places:** The Gull, "A smoky dockside tavern" (at dusk: lamplight, pipe smoke, rain on the windows, a harbour bell far off). The Lighthouse, a windy headland at dawn. Harbour Market, by day.

**Plots:** "The Missing Ledger": "The guild's ledger vanished the night of the storm." "Frost on the Pass": "A blizzard traps three travellers in a mountain hut."

**Chats:** "The Third Floorboard" (Mira and Tobin · as Aren · Year 7, Day 1, 19:22 · "The lighthouse? I could have sworn…"). "Frost on the Pass" (Ilsa · as Sable · Day 2, 06:40). "The Clockmaker's Debt" (Master Oren · as Aren · Day 5, 23:10).

**"The Third Floorboard", at The Gull, dusk, rain:**

> — The Gull · Day 1, 19:00 —
>
> **Aren** (19:02): Evening, Mira. Rough night on the docks?
>
> **Mira** (19:04): *slides a sealed letter across the table* Rough enough. Coin first. Questions after.
>
> *Tobin joins.*
>
> **Tobin** (19:06): *drops into the chair beside her* Did someone say coin?
>
> **Aren** (19:08): Tobin, would you fetch us a round from the bar? *(reaction: "Tobin didn't like that")*
>
> **Tobin** (19:10): *pushes back his chair, grinning* Anything for a paying customer.
>
> *Tobin left. He won't hear what's said now.*
>
> **Aren** (19:12): Quickly, while he's gone. I hid the guild ledger under the third floorboard behind the bar. Tell no one, least of all Tobin. *(receipts: heard by Mira; Tobin wasn't there. Callout: "Mira will remember this")*
>
> **Mira** (19:14): *her eyes flick to the bar and back* Then stop saying it so loud.
>
> — Six years later · Year 7 —
>
> **Mira** (Year 7, Day 1, 19:18): Aren? Gods, it's been years. That ledger of yours… behind the bar, wasn't it? Somewhere back there. *(spark: remembered, vaguely)*
>
> **Aren** (19:20): It was never behind the bar. I buried it by the lighthouse, remember?
>
> **Mira** (19:22): *frowns* The lighthouse? I could have sworn… Six years is a long time. *(reaction: "Mira has her doubts")*

**Mira's memories at the end:**

- hazy · witnessed · importance 9: "Aren hid the guild ledger somewhere behind the bar." Six years earlier it was sharp: "Aren hid the guild ledger under the third floorboard behind the bar and asked Mira to keep it from Tobin."
- sharp · told by Aren · doubted · importance 6: "Aren says the ledger is buried by the lighthouse."
- forgotten · witnessed · importance 2: "Tobin wore a green apron."

Tobin remembers nothing about the ledger: he wasn't there.

**Moments:** "A secret at The Gull" (night; Aren and Mira leaning in, Tobin at the bar behind them). "Reunion, six years later".

**Models:** llama.cpp on this computer, running qwen3.5-9b for every job (thinking off for Characters and Memory reader, on for Reasoning), and OpenRouter with a stored key.

## Screens to produce

In priority order:

1. **The Scene, one-to-one:** Mira at The Gull at dusk, a few lines with receipts, and the composer showing "Only Mira will hear this".
2. **The Scene, group:** Tobin stepping in ("Tobin joins"), then the moment he has left and the secret is told ("Tobin wasn't there").
3. **A reply arriving:** "Mira is thinking…", then streaming text, with Stop.
4. **The time skip:** the "Six years later" transition, then the re-lit scene with softened receipts and "Mira has her doubts".
5. **Mira's peek card** on the stage.
6. **The backstage lens:** the Memory panel, plus small versions of Prompt, Cast and Reading.
7. **Home.**
8. **Mira's profile.**
9. **Add a friend.**
10. **Chats.**
11. **The persona switcher** and your own profile.
12. **Activity.**
13. **First run**, and the Models page.
14. **Phone:** Home, Mira's profile, the one-to-one scene.

Optional: Places with the sky-islands map, Plots, a storyboard of the dive, and empty states (no friends yet, a story that hasn't started, the model server unreachable).

## Questions worth exploring

- Where does the conversation sit on the stage: a side column, a box along the bottom, or bubbles near each character?
- How do receipts and reactions stay readable across a long conversation?
- How does the stage grow from one character to three and shrink back?
- How alive can the stage be before it pulls the eye from the text?
- What does the dive through the clouds feel like in each direction?
- How does the Sky stay playful while Models stays trustworthy?

## Reference: what the app does today

All of this stays reachable. Quoted text is the current copy.

- **Library:** characters (name; description, "what anyone in the scene can see or know"; private, "only this character knows it"; example dialogue; opening line; other names; tags), places (name, description, other names, tags) and scenarios (name, premise, "every character knows this"; opening narration; tags). A story copies what it uses, so editing the library never rewrites a story in progress, and deleting an item leaves stories their copy.
- **New story:** a title, the characters the AI plays, who you play ("No one: I direct the story"), where it begins, and an optional scenario.
- **In a story:** send (Enter); continue; pick who replies ("Whoever fits", "The narrator", or a character); stop, keeping the partial reply; takes; edit; hide; time-skip chips with undo; a collapsible thoughts block for reasoning models; a token meter ("~7,300 / 16,384 tokens · 3 memories recalled"); presence toggles ("away: hears nothing said here"); someone joins from the library; cut to a new scene (place, title, who is there); delete the story.
- **Inspector** (becomes the backstage lens):
  - Memory: per character, with tier, how they learned it ("told by Aren"), "doubted", importance and a recall score. Pin ("Pinned facts sit in every prompt"), hide, and "Write a memory" (text, importance 1–10, who knows it or "Everyone knows it", "Keep it in every prompt").
  - Prompt: estimated and counted tokens with cache reuse, the prompt's parts (rules, cards, history, memory, examples, tail) against their limits with anything cut, recalled memories with their scores, and the full prompt.
  - Entities (Cast, backstage): characters, places, items and factions; a "found" badge when the reader discovered them; other names; current state ("location: the bar"); "These two are the same" to merge.
  - Reading: the reader's runs with status, trigger, job and model, attempts, a "stale" badge, errors and skipped items; "Read what is waiting now"; "Read again carefully".
- **Models:**
  - connected servers with Test, Remove and a "key stored" badge
  - "Look for model servers on this computer", and add an API with presets
  - per job: server (or inherit), model, kind (detect automatically, Standard or Reasoning, with "Detect now") and context size
  - reasoning models also get thinking (as the model likes, on or off), room to think and reasoning effort
  - Characters and Narrator also get sampler presets (Balanced, Balanced + DRY, Creative + XTC, Focused) and a JSON box sent with every request
- **Status:** "engine ok", or "engine unreachable".

## Coming later (leave room)

Books → Stories → Chapters, with folders and links between stories (sequels, shared worlds); importing character cards and SillyTavern lore and chats; export; one-click setup with a bundled model server and a model downloader.
