# Five style directions

Fifteen hi-fi artboards on the canvas: five directions × three screens (**Home**, **Mike's profile**, **First run**). Those three were chosen because between them they answer nine of the eleven open questions from `AUDIT.md` §11 — Home settles browse and hierarchy, the profile settles art-led detail, first run settles the highest-stakes moment in the product.

Every direction carries the **same content and the same information architecture**, because the UX work in `UX-STUDY.md` is settled and is not up for a vote. All four therefore already include:

- Home led by the **continue block**, not by a browse grid.
- A **five-item rail** (Home · Stories · Characters · World · You) with Settings, **Feedback** and the theme switch in the footer. Activity is gone as a destination.
- `Ctrl K` search that goes somewhere.
- **No glass on page chrome**, no coloured glow, no candy hues on the filters, no stat tiles, no completeness ring, no bell.
- A first run with **three doors** where door one needs no configuration, the privacy promise at full size, and six characters shipped.
- Feelings language in place of memory telemetry ("Mike is turning that over", "going hazy") and a one-sentence relationship summary in place of the three-tile dashboard.

So what differs between the four is genuinely **material, type, colour, rhythm and crop** — not the product.

---

## A · Paper & Ink

> Editorial. Warm paper, ink rules, a serif that behaves like a book.

**The idea.** Kataki is a place where writing happens, so the app is made of paper. There are no cards floating over anything: there are ruled columns, plates with a 12px mount, and a hairline that means "new section". The one accent is oxblood, used for the primary action, the quote rule and the active rail marker — nowhere else.

**Type.** Fraunces 800 for display (a real editorial serif with optical sizing), Instrument Sans for UI, Newsreader for anything a character said. The type contrast is the widest of the four: 62px name against 11px small caps.

**Material.** Opaque warm paper (`#f3eee4`), cards one step lighter (`#fffdf8`), a 1px `#ded3c0` rule and **no shadow at all** except on floating layers. Radii are 3–6px, so nothing looks like a pill except the one thing that is.

**What it answers.** The character grid is one featured plate and a ruled list — the most asymmetric of the four, and the furthest from a repeating card unit. The clouds survive as a 96px band behind the header and nowhere else. First run is three ruled columns with no card at all.

**Good at:** looking like nothing else in this category; typographic authority; ageing well; reading beautifully at 200% text size.
**Risks:** can read as austere or "serious literary tool" rather than something playful; the painted art has to do all the warming, and on a screen with few portraits (Settings, an empty World) it may feel cold.

---

## B · Night Theatre

> Dark-first. The art is the only light in the room.

**The idea.** Dark is the default, not a variant. The frame is a warm near-black (`#121010`, never pure black) and every saturated colour in the app comes from a painting. One amber accent (`#e8a54b`) stands for lamplight and ties the Sky to the Scene's lit places.

**Type.** Instrument Serif for display — high-contrast, cinematic, set large (74px on the profile) — with Inter Tight for UI and Newsreader for speech.

**Material.** A four-step surface ladder (`#121010 / #1a1716 / #1c1917 / #24201d`), hairlines at 10% white, and one real shadow reserved for things that float.

**What it answers.** The character grid is **key art**: five posters in a row, the one you played last wider than the others, name and state set over a scrim. Mike's profile is a darkened, blurred place photograph with a contained portrait plate at the right — cinematic without the crop problem a full-bleed portrait creates. First run puts the art on the left half and stacks the three doors as rows on the right, so the recommended one reads first.

**Good at:** making the art look expensive; long evening sessions; the dive into the Scene becomes almost seamless; the least "AI product" of the four by a distance.
**Risks:** a dark-only app excludes people who want a bright one, so a light theme still has to be designed and will be the harder one; and dark UI with painted art is easy to make muddy — every portrait needs a checked scrim.

---

## C · Daylight

> Calm modern. The current Sky, fixed.

**The idea.** Keep the optimism of the existing design — above the clouds, bright, friendly — and fix everything the audit found. Glass becomes opaque white. The sky becomes a 148px band at the top with the clouds in it, rather than a wash under the whole page. The indigo accent becomes a deep sea green (`#146b60`), which is off the axis the research names as the loudest AI tell.

**Type.** Bricolage Grotesque for display (tight, slightly odd, deliberately not Inter), Plus Jakarta Sans for UI, Newsreader for speech.

**Material.** `#f1f4f6` ground, white cards, a 1px `#dfe5ea` border, one very light shadow, radii 6/10/16 and pills reserved for the primary action and status.

**What it answers.** The grid is one large card and four smaller ones — asymmetric, but gently. Everything is legible, everything is conventional in the good sense, and a new user has nothing to learn.

**Good at:** the lowest-risk direction; approachable to the Character.AI escapee; the easiest to build and to keep consistent; the safest under accessibility review.
**Risks:** it is the most *ordinary* of the four. It would pass every checklist in `DESIGN-RESEARCH.md` and still not be memorable. If the answer to "what could no competitor have made?" is only "the orb and the painted art", this direction is doing the least work.

---

## D · Storybook

> Illustrated. Painted card stock, hand-set labels, a deck you can hold.

**The idea.** The app is an object. Characters are cards in a deck, sitting at slightly different angles. Places are photographs taped into an album with a caption written under them. Status is a sticker set at an angle, not a pill. The ground is painted card (`#ece0c9`) with a 2px border on everything and a 3px hard offset instead of a blur — the shadow of something physically sitting on something else.

**Type.** Young Serif for display (chunky, warm, confident), Nunito Sans for UI, Newsreader for speech. Bottle green accent with a marigold second for stickers and rules.

**What it answers.** This is the boldest position on "what could no competitor have made?" — the deck, the taped polaroid, the caption under the still. It is also the only direction where the completeness of a character is expressed physically (a draft card has a sticker, not a ring).

**Good at:** memorable in one screenshot; makes the sample world feel like a *world*; the one direction people would post.
**Risks:** twee is one degree away. Rotations, tape and stickers have to be rationed hard or the app becomes a scrapbook toy; and the decorative angles need a `prefers-reduced-motion`-style opt-out for anyone who finds them noisy. It is also the hardest of the four to keep consistent across a hundred screens.

---

## E · Night Storybook — *the mix*

> The old night sky, with a deck of lit cards laid on it. Lamplight for the accent.

**The idea.** Take the night sky from the dark mode you liked and keep it as the *ground* — a real sky, with stars, moonlight coming in from the top right and moonlit cloud at the very top. Then stop putting glass panels on it. Everything on top of it is a physical object: cards, framed photographs, a panel of dark board. Everything stays dark: the cards are dark card stock (`#221f36`) with a warm hairline and a 1px lamplight catch along the top edge, sitting on a deep shadow. Nothing on the page is a pale plate — the object-ness comes from the edge and the shadow, not from a light panel. From B it takes the discipline — art is the only saturated colour, one warm accent, no glass, contained portraits rather than full-bleed crops. From D it takes the physicality — the angled deck, the tape, the caption hand-set under a photograph. From the old dark mode it takes the sky itself, and the orb, which finally has a night to sit in.

**Type.** Young Serif for display, Nunito Sans for UI, Newsreader for speech — D's voices, which suit the object-ness.

**Colour.** Ground is a night gradient that drifts from midnight blue into a warm plum at the bottom (`#0b1026 → #131a3a → #1b1b3c → #241a2e`), so the sky gets warmer as it comes down toward the lamplight. Panels are `#1b1930`, card stock `#221f36`, one step up `#241f38`. The accent is lamplight amber `#efb35c`, which also tints the tape; a moon blue `#9fb8ff` does the quiet second job (the rail mark, starlight). Nothing else is saturated — the portraits are the only colour on the page.

**What it answers.** The character grid is the deck, angled, in dark frames lit along the top edge — the single most distinctive grid of the five. The continue block is a taped photograph with "the gala, three weeks later" written under it. Mike's profile is a framed picture propped on a night sky. First run is the sky itself, full bleed, with three dark doors on it.

**Good at:** it is the only direction that keeps what you already liked and still passes the whole slop checklist. Dark-first with warmth, which is the hardest thing to get right and the thing most competitors do badly. Memorable in one screenshot. The dive into the Scene is now a descent out of a real sky.
**Risks:** two personalities in one room — the sky wants to be atmospheric and the deck wants to be tactile, and if either gets louder the other stops working. A light theme for this is a genuine second design, not a token flip: the sky becomes day and the whole surface ladder inverts.

---

## Side by side

| | A · Paper & Ink | B · Night Theatre | C · Daylight | D · Storybook | **E · Night Storybook** |
|---|---|---|---|---|---|
| Material | Paper, hairlines, no shadow | Warm-black surface ladder | White cards, light shadow | Painted stock, hard offset | Night sky + dark card stock, lit edges |
| Accent | Oxblood `#8f3020` | Amber `#e8a54b` | Sea green `#146b60` | Bottle green + marigold | Lamplight `#efb35c` + moon blue |
| Display face | Fraunces 800 | Instrument Serif | Bricolage Grotesque | Young Serif | Young Serif |
| UI face | Instrument Sans | Inter Tight | Plus Jakarta Sans | Nunito Sans | Nunito Sans |
| Radius | 3 / 4 / 6 | 4 / 8 / 12 | 6 / 10 / 16 | 4 / 10 / 14 | 4 / 10 / 14 |
| The sky | 96px band | A dark horizon | 148px band, visible | 120px band, painted | **the whole ground — stars, moonlight, cloud** |
| Grid | Feature plate + ruled list | Five posters, first wider | Big card + four | A deck, angled | A deck, angled, edges catching the light |
| Default theme | Light | **Dark** | Light | Light | **Dark** |
| Reads as | A literary journal | A cinema | A good modern app | A handmade object | A night desk with photographs on it |
| Slop risk | Very low | Very low | Moderate | Very low | Very low |
| Build cost | Low | Medium | Low | High | High |
| a11y risk | Low | Medium (contrast over art) | Low | Medium (angles, texture) | Medium (dark-on-dark edges, angles) |

---

## What I would pick, and why

**E · Night Storybook**, now that it exists. It is the only one of the five that keeps the night sky you already liked, and it gets there without any of the things the research says to avoid — no glass, no glow, no violet gradient under flat chrome, no repeating identical cards. The lit card edges do the job the glass panels used to do — separate an object from the sky — with none of the legibility cost, and the deck is the answer to "what could no competitor have made?".

Its light theme should be designed from **C**'s surfaces, not flipped from E's tokens — that is the mistake the current Sky makes.

*(Previous recommendation, before E: B · Night Theatre as the spine, with C's discipline and D's one gesture.)*

The reasoning: the app's only irreplaceable asset is the painted art, and B is the direction that makes the art the brightest thing on the screen. It is also the direction that best matches what the product actually *is* — an evening activity, in a lamplit place, with the Scene already dark. The dive from a dark Sky into a dark Scene stops being a jump and becomes a focus pull.

C's contribution is the light theme: rather than inventing a second dark palette from a light design (the mistake the current Sky makes, which is why it needs a `polish()` pass), build B properly and let C's surfaces be the light theme's spec.

D's contribution is one gesture, kept: **the caption under the still**. "the gala, three weeks later", set in the display face under a photograph, is the single most Kataki-feeling detail in all twelve boards and it costs nothing.

A is the direction I'd keep in the drawer. If the product ever turns toward writers rather than players — Noor rather than Sam — A is already most of the answer.

---

## What happens after you pick

1. Lock the chosen direction's tokens and rebuild `tokens.json` / `tokens.css` from it, with light and dark as two first-class palettes rather than a flip plus a patch.
2. Redraw the other six Sky screens in the chosen direction, plus the states that do not exist yet: empty Sky, empty World, search results, the model server going away, a slow generation, and the feedback / bug / suggestion flow.
3. Then the component library — reviewing an existing one first, as you asked — and then the implementation plan.

Nothing in this document is built yet. Say which one, or which parts of which, and I'll take it from there.
