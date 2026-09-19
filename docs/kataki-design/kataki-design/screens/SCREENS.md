# Screens

All screens are 1440×900 desktop, except Home (1440×1190), Mira's profile (1440×1500) and Models (1440×1000), which scroll. Each has a static page in `html/` and a screenshot in `png/`. Links between pages work: the orb, cards, menu items and "Open the line".

Sample content throughout is from the brief: you play **Aren**, with **Mira**, **Tobin**, **Ilsa**, **Master Oren** and **Wren**, in the story **"The Third Floorboard"** at **The Gull**.

## The Scene (inside a story)

| # | File | What it demonstrates |
|---|---|---|
| 1 | `Scene-OneToOne.html` | A one-to-one scene: Mira at The Gull at dusk, rain on the windows, table in the foreground. A title card, two lines. The hovered line shows its tools pill and expanded receipts ("Heard by Mira · she'll remember"). The newest line has a pending receipt. The tray shows Tobin (could join), Ilsa, Oren. The composer says "Only Mira will hear this". |
| 2 | `Scene-Group-Joins.html` | **An arrival.** Tobin steps in (motion ghost), lit as the speaker, with a "Tobin joins" name card on stage. Mira softens. A system note with Undo. The composer says "Mira and Tobin will hear this". Tobin is added to Who answers. |
| 3 | `Scene-Group-Secret.html` | **A departure, then the secret.** The reaction "Tobin didn't like that" sits on Aren's 19:08 line. The note "Tobin left. He won't hear what's said now." Tobin's greyed silhouette is at the bar with an "away" tag. The secret line (hovered) shows expanded receipts "Mira heard · will remember" and "Tobin wasn't there", plus the callout "Mira will remember this". The composer shows "Tobin is away". |
| 4 | `Scene-Reply-Thinking.html` | **A reply arriving, part 1.** "Mira is thinking…" with pulsing dots and a link to her notes backstage. Mira's thinking expression. Send has become Stop. The secret line's receipts are still pending: the callout hasn't landed yet. |
| 5 | `Scene-Reply-Streaming.html` | **Part 2.** Text streams word by word with an amber caret, the stamp says "writing…", and there's a "Thought for 4 s" chip. Stop, plus "Stopping keeps what Mira has written so far". |
| 6 | `Scene-TimeSkip.html` | **The time-skip transition.** The stage is blurred under drifting clouds. "Six years later" with the clock "Day 1, 19:14 → Year 7, Day 1, 19:14", "12 of Mira's memories are going hazy. 3 are fading out.", Undo. Behind it, receipts and the callout fade to hazy. |
| 7 | `Scene-AfterSkip.html` | **Re-lit for Year 7.** Night, cooler light, a moon in the window. The older line is dimmed with hazy receipts. A title card "Six years later · Year 7" with Undo. Mira's 19:18 line has a spark and an open recall tooltip ("Mira remembered, vaguely: the ledger is somewhere behind the bar"). Mira's 19:22 line has the belief reaction "Mira has her doubts" with the reason. |
| 8 | `Scene-Peek.html` | **Mira's peek card** over the stage: expression "doubtful", Right now, On her mind (hazy), What she knows about you, Trusts Aren, Distrusts Tobin, a blurred secret with Reveal, and the actions. |
| 9 | `Scene-Backstage.html` | **The backstage lens** (switch on): a blueprint grid. The Memory panel (Mira/Tobin tabs, tier filters, 5 memories covering hazy with the struck "was sharp", sharp and doubted, pinned, and forgotten, plus the Write a memory form). Prompt (token bar and legend against limits, recalled scores, cache reuse). Cast ("found" badges, a merge suggestion). Reading (runs, a stale badge, read-now buttons). |

## The Sky (outside a story)

| # | File | What it demonstrates |
|---|---|---|
| 10 | `Sky-Home.html` | The greeting "Good evening, Aren" with your avatar (with a switch badge, opens the persona switcher). Search, the Activity bell (4), "Add a friend". **Continue card** (the last scene still, Mira's last line, "3 new memory events", orb "Dive back in"). An Activity preview. **Friends** with candy filters (All, Favourites, In a story, New, Groups), 5 friend cards (Wren with a 60% ring) and an Add card. **Moments** (2 composed stills). |
| 11 | `Sky-Profile-Mira.html` | **Profile before messaging.** A big portrait with name plate, status and tags. "Message Mira" (continues the latest story, with orb), "Start a new story", "Start a group scene", "Edit profile". 3 stat tiles. A **Right now** living-profile card with a story selector and memory bar. About (plus "Also known as"). How she talks and How she says hi as bubbles. The Secret. Relationships, Stories together, Places she's been, Moments. |
| 12 | `Sky-AddFriend.html` | **Add a friend**, step 3 of 6 ("Their secret") for Wren: stepper, big textarea, "Stuck? Start from" prompt chips, Back / Skip / Next. A live profile card filling in on the right, with a 60% ring: "Add a secret to make Wren more real". |
| 13 | `Sky-Chats.html` | Thread list: New chat, New group scene, filter chips, a Pinned thread (stacked avatars, story clock, "as Aren", memory badge 3), and 3 other stories. The selected thread's preview: the last-moment still, Dive in orb, In this story (who's there, what they know), and New since you left. |
| 14 | `Sky-You.html` | The **persona switcher** open (Aren ✓, Sable, Director · play no one, New persona, and a footnote). **Your profile**: "Played by you" badge, Who knows Aren (per character, per story), Aren's chats. |
| 15 | `Sky-Activity.html` | Activity grouped by story and story time, with kind filters. One item is expanded to show the quoted line with "Open the line". Side cards: "Still being read" (with Read now) and a "How receipts fade" legend. |
| 16 | `Sky-FirstRun.html` | "They'll remember this." over clouds, and the promise line. Three steps: **Connect a model** (active; found llama.cpp on this computer, Use this, Look again, or add an online API), Make yourself, Add your first friend. A privacy line and Continue. |
| 17 | `Sky-Models.html` | Settings subnav. Models with "engine ok". Servers and APIs (llama.cpp connected with qwen3.5-9b loaded; OpenRouter with "key stored"; Test and Remove). "Look for model servers on this computer", "Add an API". Jobs: Characters expanded with every field; Narrator, Memory reader, Reasoning and Recall by meaning collapsed. |

## Interaction notes per screen

- **Every Sky screen:** the rail's orb and the Continue card dive into `Scene-OneToOne` (the last scene). Friend cards open the profile, and Activity items open the line.
- **Every Scene screen:** the cloud button floats back up to the Sky, returning to the screen you dove from. The Backstage switch toggles the lens in place, with no navigation.
- **Moving between states:** Tobin joining, the reply, and the time skip are states of one screen, not separate pages. Animate between them; don't navigate.
