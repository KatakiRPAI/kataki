import type * as React from 'react';
type ReactNode = React.ReactNode;
export type IconName = "alert" | "arrow" | "bell" | "book" | "chat" | "check" | "clock" | "cloud" | "cog" | "cpu" | "crown" | "dots" | "down" | "download" | "drag" | "ear" | "edit" | "eye" | "eyeoff" | "feather" | "ff" | "film" | "filter" | "flame" | "globe" | "grid" | "hand" | "heart" | "help" | "home" | "image" | "key" | "layers" | "left" | "link" | "lock" | "map" | "map-pin" | "merge" | "mic" | "moon" | "mute" | "pause" | "pin" | "play" | "plus" | "pushpin" | "quill" | "quote" | "refresh" | "right" | "search" | "send" | "server" | "settings" | "shield" | "spark" | "star" | "stop" | "sun" | "swap" | "thought" | "trash" | "undo" | "up" | "user" | "users" | "volume" | "wind" | "x";
export type Who = string;
export type Place = string;
/** One of 70 line icons on a 24px grid, 1.8px stroke, round caps, drawn in currentColor. */
export declare function Icon(props: { name: IconName; size?: number; stroke?: number; color?: string; label?: string; flip?: boolean }): React.ReactElement;
/** A round crop of a character portrait, centred on the face, with an optional ring, presence dot, or the initial when there is no portrait. */
export declare function Avatar(props: { who?: Who; src?: string; name?: string; size?: number; alt?: string; ring?: "accent" | "warm"; status?: "present" | "away" | "thinking"; away?: boolean; focus?: string }): React.ReactElement;
/** Several characters in one overlapping row, with a +N count past `max`. */
export declare function AvatarStack(props: { people: { who?: Who; src?: string; name?: string; alt?: string }[]; size?: number; max?: number; label?: string }): React.ReactElement;
/** A surface on the ladder: panel by default, raise for nested, pop for anything floating. */
export declare function Panel(props: { level?: "raise" | "pop"; flush?: boolean; as?: string; label?: string; style?: object; children?: ReactNode }): React.ReactElement;
/** A hairline between groups, optionally with a small label. */
export declare function Divider(props: { label?: string; strong?: boolean }): React.ReactElement;
/** The night sky behind every Sky page: gradient, stars, one crescent moon, a moonlit cloud bank. By day it becomes a daylight sky. */
export declare function Sky(props: { stars?: number; clouds?: boolean; cloudsSrc?: string }): React.ReactElement;
/** The small label above a section. Uppercase and tracked in Latin; plain and larger in Arabic. */
export declare function Eyebrow(props: { tone?: "mid" | "warm" | "accent"; children: ReactNode }): React.ReactElement;
/** Any name from the story world, set in Newsreader: stories, characters, places, books. */
export declare function StoryName(props: { size?: "hero" | "title" | "lg" | "card" | "row"; as?: string; children: ReactNode }): React.ReactElement;
/** Running text in one of the system's voices: body, label, meta, caption, prose, quote, memory, mono. */
export declare function Text(props: { variant?: "body" | "label" | "meta" | "caption" | "prose" | "quote" | "memory" | "mono"; tone?: string; as?: string; children: ReactNode }): React.ReactElement;
/** One key cap. */
export declare function Kbd(props: { children: ReactNode }): React.ReactElement;
/** A key combination. The word "then" in the list makes a sequence (G then H). */
export declare function Shortcut(props: { keys: string[] }): React.ReactElement;
/** Primary, secondary, ghost, danger and link buttons, pill-shaped. Primary is flat blue, at most once per view. */
export declare function Button(props: { variant?: "primary" | "secondary" | "ghost" | "danger" | "link"; size?: "sm" | "lg"; icon?: IconName; iconEnd?: IconName; loading?: boolean; disabled?: boolean; full?: boolean; href?: string; onClick?: () => void; children: ReactNode }): React.ReactElement;
/** A round icon-only button. `label` is required: it becomes the aria-label and tooltip. */
export declare function IconButton(props: { icon: IconName; label: string; variant?: "plain" | "solid" | "glass"; size?: "sm" | "lg"; pressed?: boolean; disabled?: boolean; href?: string; onClick?: () => void }): React.ReactElement;
/** Lays buttons out in a row with the standard gap; `align` end or between. */
export declare function ButtonGroup(props: { align?: "end" | "between"; children: ReactNode }): React.ReactElement;
/** An inline link in accent-text, optionally with an icon; `quiet` for secondary links. */
export declare function TextLink(props: { href?: string; icon?: IconName; quiet?: boolean; children: ReactNode }): React.ReactElement;
/** A small busy indicator. Give it a `label` when it stands alone. */
export declare function Spinner(props: { size?: number; label?: string }): React.ReactElement;
/** The label, hint and error wrapper every form control uses. Use it to wrap a custom control. */
export declare function Field(props: { label?: string; hint?: string; error?: string; required?: boolean; optional?: boolean; disabled?: boolean; htmlFor?: string; children: ReactNode }): React.ReactElement;
/** A one-line input with label, hint, error, icon, character count and suffix. `story` sets the value in Newsreader. */
export declare function TextField(props: { label?: string; value?: string; defaultValue?: string; onChange?: (v: string) => void; placeholder?: string; hint?: string; error?: string; icon?: IconName; story?: boolean; max?: number; suffix?: string; required?: boolean; optional?: boolean; disabled?: boolean; type?: string; id?: string }): React.ReactElement;
/** A multi-line field; Newsreader by default because most long fields are story text. */
export declare function TextArea(props: { label?: string; value?: string; defaultValue?: string; onChange?: (v: string) => void; placeholder?: string; rows?: number; story?: boolean; hint?: string; error?: string; required?: boolean; optional?: boolean; disabled?: boolean; id?: string }): React.ReactElement;
/** A native select styled as a field, with a chevron. */
export declare function Select(props: { label?: string; options: string[]; value?: string; defaultValue?: string; onChange?: (v: string) => void; icon?: IconName; hint?: string; error?: string; optional?: boolean; disabled?: boolean; id?: string }): React.ReactElement;
/** The search field with its Ctrl K hint. `size="lg"` for the search page. */
export declare function SearchField(props: { placeholder?: string; value?: string; onChange?: (v: string) => void; label?: string; shortcut?: string | false; size?: "lg" }): React.ReactElement;
/** A checkbox with a label and optional description. For independent yes/no choices in a list. */
export declare function Checkbox(props: { label: string; description?: string; checked?: boolean; defaultChecked?: boolean; onChange?: (v: boolean) => void; disabled?: boolean }): React.ReactElement;
/** One choice from a short list, each with an optional description. */
export declare function RadioGroup(props: { label?: string; options: { value: string; label: string; description?: string; disabled?: boolean }[]; value?: string; defaultValue?: string; onChange?: (v: string) => void }): React.ReactElement;
/** A switch for a setting that applies immediately. Always has a label, visible nearby or as `label`. */
export declare function Toggle(props: { on?: boolean; defaultOn?: boolean; onToggle?: (v: boolean) => void; onClick?: () => void; label: string; disabled?: boolean }): React.ReactElement;
/** Two to four mutually exclusive views or values: By story / By character, Simple / Advanced, 100% / 125% / 150%. */
export declare function Segmented(props: { options: string[]; value?: string; defaultValue?: string; onChange?: (v: string) => void; label: string; size?: "sm"; tone?: "scene" }): React.ReactElement;
/** A continuous value with its label, readout and optional end labels. */
export declare function Slider(props: { label?: string; value?: number; defaultValue?: number; onChange?: (v: number) => void; min?: number; max?: number; step?: number; valueText?: string; ends?: [string, string]; disabled?: boolean; id?: string }): React.ReactElement;
/** A filter chip with an optional count, icon, avatar or remove mark. Pressed fills with ink, never a hue. */
export declare function Chip(props: { pressed?: boolean; defaultPressed?: boolean; onPress?: (v: boolean) => void; onClick?: () => void; toggle?: boolean; count?: number; icon?: IconName; who?: Who; src?: string; removable?: boolean; size?: "sm"; disabled?: boolean; children: ReactNode }): React.ReactElement;
/** Suggestions the player can take with one click, drawn dashed so they read as offers, not filters. */
export declare function ChoiceChips(props: { label?: string; options: string[]; onPick?: (v: string) => void }): React.ReactElement;
/** A place to drop or pick an image, with the empty portrait beside the instructions. */
export declare function DropZone(props: { title?: string; description?: string; icon?: IconName; empty?: string; active?: boolean; children?: ReactNode }): React.ReactElement;
/** A numbered step label for multi-part forms such as New story. */
export declare function StepHeader(props: { n: number | string; title: string; optional?: boolean }): React.ReactElement;
/** The five-item navigation: Home, Stories, Characters, World, You; New character under a rule; Settings, Feedback and the Day/Night switch in the foot. */
export declare function Rail(props: { active?: "Home" | "Stories" | "Characters" | "World" | "You"; compact?: boolean; theme?: "night" | "day"; hrefs?: Record<string, string>; onNavigate?: (to: string) => void; settingsDot?: boolean; height?: number }): React.ReactElement;
/** Who you are playing as, top left of every Sky page. Opens the persona menu. */
export declare function PersonaSwitch(props: { who?: Who; src?: string; name?: string; open?: boolean }): React.ReactElement;
/** The strip above page content: persona switch (or a back link) on one side, search on the other. */
export declare function TopBar(props: { who?: Who; src?: string; name?: string; back?: string; backHref?: string; children?: ReactNode }): React.ReactElement;
/** Switches between views of the same thing: Story / Profile on a character, Everything / Places / Plots. */
export declare function Tabs(props: { tabs: string[]; value?: string; defaultValue?: string; onChange?: (v: string) => void; counts?: Record<string, number>; size?: "sm"; label?: string }): React.ReactElement;
/** The section list on Settings and World: icon, label, optional count, current item raised. */
export declare function SideNav(props: { items: { label: string; icon?: IconName; count?: number; href?: string }[]; active?: string; label?: string; footer?: ReactNode }): React.ReactElement;
/** Where a nested item sits: World › Close to the Crown › Halcyon Coffee. The chevrons mirror in right-to-left. */
export declare function Breadcrumbs(props: { items: string[] }): React.ReactElement;
/** Reveals the rest of a list in place: "7 older stories". */
export declare function ShowMore(props: { children: ReactNode }): React.ReactElement;
/** A floating list of actions or choices: items with icon or avatar, detail line, count, shortcut, check, danger; sections, dividers and a footnote. */
export declare function Menu(props: { title?: string; label?: string; width?: number; footer?: ReactNode; items: { onSelect?: () => void; label?: string; detail?: string; icon?: IconName; who?: Who; src?: string; meta?: string; count?: number; shortcut?: string[]; checked?: boolean; danger?: boolean; disabled?: boolean; active?: boolean; divider?: boolean; section?: string }[] }): React.ReactElement;
/** A short label or exact value on hover and focus. `open` pins it for docs. */
export declare function Tooltip(props: { text?: ReactNode; title?: string; placement?: "top" | "bottom" | "start"; open?: boolean; children: ReactNode }): React.ReactElement;
/** A small floating panel with a title, a few fields and actions, anchored to what opened it. */
export declare function Popover(props: { title?: string; description?: string; width?: number; onClose?: false | (() => void); actions?: ReactNode; children: ReactNode }): React.ReactElement;
/** A modal for a task that needs full attention: an icon, title, description, body, a note and actions. */
export declare function Dialog(props: { title: string; description?: string; icon?: IconName; tone?: "bad" | "warm"; size?: "sm" | "lg"; note?: string; actions?: ReactNode; backdrop?: boolean; onClose?: () => void; children?: ReactNode }): React.ReactElement;
/** A side panel that slides over the page: a character's card from the chat, a place, details that do not deserve a page. */
export declare function Sheet(props: { onClose?: () => void; title: string; tone?: "scene"; headerAction?: ReactNode; children: ReactNode }): React.ReactElement;
/** A short confirmation at the bottom of the window, with an optional undo. Intentional addition: deletes and forgets need a way back. */
export declare function Toast(props: { icon?: IconName; tone?: "bad"; action?: string; onAction?: () => void; onDismiss?: () => void; children: ReactNode }): React.ReactElement;
/** Ctrl K over anything: jump to a story, character or place, find a line, or run a command. */
export declare function CommandPalette(props: { query?: string; groups: { title: string; items: { label: string; icon?: IconName; who?: Who; src?: string; meta?: string; shortcut?: string[]; story?: boolean; active?: boolean }[] }[] }): React.ReactElement;
/** A short note inside a page: info, privacy, warm (worth knowing), ok, bad. Icon plus text; no coloured side stripe. */
export declare function Callout(props: { tone?: "info" | "privacy" | "warm" | "ok" | "bad"; icon?: IconName; title?: string; action?: ReactNode; children?: ReactNode }): React.ReactElement;
/** A page-level problem: what happened in plain words, the technical code small, and the fixes as buttons. */
export declare function Alert(props: { title: string; code?: string; icon?: IconName; actions?: ReactNode; children: ReactNode }): React.ReactElement;
/** What a list or page looks like with nothing in it yet, with the next step as an action. */
export declare function EmptyState(props: { title: string; icon?: IconName; eyebrow?: string; compact?: boolean; actions?: ReactNode; children?: ReactNode }): React.ReactElement;
/** Progress with a label and value; indeterminate when the end is unknown. */
export declare function ProgressBar(props: { value?: number; label?: string; valueText?: string; indeterminate?: boolean }): React.ReactElement;
/** Grey placeholders while local data loads. Kataki is local, so these should almost never show. */
export declare function Skeleton(props: { width?: number | string; height?: number; radius?: number; round?: boolean; lines?: number }): React.ReactElement;
/** Real steps of a long operation with done, doing, waiting and failed states: the cold start. */
export declare function StepList(props: { steps: { label: string; detail?: string; state?: "done" | "doing" | "wait" | "failed" }[] }): React.ReactElement;
/** A single line of system health with a dot, detail and one action: the top of Models settings. */
export declare function StatusLine(props: { title: string; tone?: "ok" | "warm" | "bad"; action?: ReactNode; children?: ReactNode }): React.ReactElement;
/** A value from a fixed vocabulary the engine sets: a mood, a memory state, a connection. Never free text. */
export declare function StatePill(props: { tone?: "warm" | "ok" | "bad" | "muted" | "accent"; icon?: IconName; children: ReactNode }): React.ReactElement;
/** A short authored trait on a profile: Barista, Steady, Private. Up to three. */
export declare function Tag(props: { tone?: "accent" | "warm"; children: ReactNode }): React.ReactElement;
/** A count or a dot. The warm dot is the only "something new" signal in the app (What's new). */
export declare function Badge(props: { count?: number; tone?: "accent" | "warm" | "muted"; dot?: boolean; label?: string; children?: ReactNode }): React.ReactElement;
/** A stored 0–100 score (warmth, trust, doubt) with its label and number, or a word instead of the number. */
export declare function Meter(props: { label?: string; value: number; word?: string; tone?: "accent" | "ok" | "warm" | "muted" | "bad" }): React.ReactElement;
/** One memory a character holds: the stored line in Newsreader, its state as a word, and how sharp it is as a bar. */
export declare function MemoryRow(props: { word: string; value: number; tone?: "muted" | "warm" | "ok" | "bad"; meta?: string; children: ReactNode }): React.ReactElement;
/** A computed value and its noun: 4 stories. Tabular numbers. */
export declare function Stat(props: { value: ReactNode; label: string }): React.ReactElement;
/** A line of computed values: 4 stories · 412 lines · 2 places · together since 24 May. */
export declare function StatRow(props: { stats: [string, string][]; children?: ReactNode }): React.ReactElement;
/** A labelled fact in a card: Right now, Here since, Heard it. */
export declare function KeyValue(props: { icon?: IconName; label: string; children: ReactNode }): React.ReactElement;
/** A row in a list: avatar or icon, a title (StoryName when `story`), subtitle and meta on the end. `href` makes the whole row a link. */
export declare function ListRow(props: { name?: string; title: ReactNode; subtitle?: ReactNode; meta?: ReactNode; who?: Who; src?: string; icon?: IconName; avatarSize?: number; story?: boolean; href?: string; children?: ReactNode }): React.ReactElement;
/** Dawn, day, dusk, night for a place; the current one filled. The label on the filled segment picks its colour by contrast. */
export declare function TimeStrip(props: { value: "dawn" | "day" | "dusk" | "night" }): React.ReactElement;
/** A relative or story time with the exact value on hover and focus. */
export declare function Stamp(props: { exact?: string; detail?: string; open?: boolean; placement?: "top" | "bottom" | "start"; tone?: "scene"; children: ReactNode }): React.ReactElement;
/** What changed, newest first: version, when, one line each. Nothing is ever removed. */
export declare function Changelog(props: { items: { version: string; when: string; text: string }[] }): React.ReactElement;
/** A sample line in a speech bubble: How he talks. *Actions* render italic. */
export declare function Bubble(props: { indent?: boolean; children: string }): React.ReactElement;
/** A character's secret, on its own dark card with a lock and a warm label. */
export declare function SecretCard(props: { name?: string; title?: string; children: ReactNode }): React.ReactElement;
/** A framed moment from a story: a place at a time, with a caption on the scrim. The one framed image on Home. */
export declare function Still(props: { place?: Place; src?: string; caption?: string; height?: number; alt?: string; position?: string }): React.ReactElement;
/** The top of Home: where you were, back in one click. Sits on the sky, no panel. */
export declare function ContinueHero(props: { title: string; book: string; lastLine: string; who?: Who; avatarSrc?: string; avatarName?: string; mood?: string; stats: string; where: string; place: Place; placeSrc?: string; caption?: string; placeAlt?: string; continueHref?: string; newHref?: string; onContinue?: () => void }): React.ReactElement;
/** One row of "Since you last played": who, an event type from a fixed set, the stored memory line, computed metadata. */
export declare function EventCard(props: { who?: Who; avatarSrc?: string; name: string; event: string; tone?: "warm" | "ok" | "muted"; memory: string; meta: string }): React.ReactElement;
/** A character in a grid. The one you played last is `featured` (324px); the rest 168px. Hover shows Continue and ···. */
export declare function CharacterCard(props: { who?: Who; src?: string; name: string; when: string; line?: string; stories?: number; featured?: boolean; badge?: string; badgeTone?: "warm"; hover?: boolean; alt?: string; focus?: string; continueHref?: string; continueLabel?: string; onMore?: () => void }): React.ReactElement;
/** The dashed "add one" tile at the end of a grid. */
export declare function AddCard(props: { onClick?: () => void; href?: string; icon?: IconName; sub?: string; wide?: boolean; children?: ReactNode }): React.ReactElement;
/** Someone you can play as: portrait, name, one line, Default tag. The Director has an icon instead of a face. */
export declare function PersonaCard(props: { who?: Who; src?: string; icon?: IconName; name: string; line: string; isDefault?: boolean; selected?: boolean }): React.ReactElement;
/** A story thread: faces, title, book, the last stored line (two lines, clamped), real time and story time. */
export declare function StoryCard(props: { who?: Who; avatarSrc?: string; people?: { who?: Who; src?: string; name?: string }[]; title: string; book: string; quote: string; when: string; storyTime?: string; selected?: boolean; pinned?: boolean; compact?: boolean }): React.ReactElement;
/** The right-hand pane on Stories: the place, title, story time, Continue, who is here with their memory counts. */
export declare function StoryPreview(props: { title: string; meta: string; lastPlayed: string; place?: Place; placeSrc?: string; placeAlt?: string; continueHref?: string; cast?: { who?: Who; src?: string; name: string; memories: string; pill?: string; tone?: string }[]; children?: ReactNode }): React.ReactElement;
/** Who a character knows and how, from the relationship enum: wary of him, fond of her, never met. */
export declare function RelationshipCard(props: { who?: Who; src?: string; name: string; how: string }): React.ReactElement;
/** A place in the World: art with its name, the authored description, the time strip, who knows it and where it is filed. */
export declare function PlaceCard(props: { place?: Place; src?: string; name: string; blurb?: string; time?: "dawn" | "day" | "dusk" | "night"; people?: { who?: Who; src?: string; name?: string }[]; links?: string; selected?: boolean; alt?: string }): React.ReactElement;
/** A plot: the opening line in Newsreader italic, how it starts, who is in it, the book. */
export declare function PlotCard(props: { quote: string; opening: string; people?: { who?: Who; src?: string; name?: string }[]; book: string }): React.ReactElement;
/** One of the three ways to start on first run. `recommended` is the one that needs no setup. */
export declare function DoorCard(props: { icon?: IconName; eyebrow: string; title: string; recommended?: boolean; actions?: ReactNode; children: ReactNode }): React.ReactElement;
/** One hit on the search page: kind icon, title, where it lives, the matching excerpt, the character, and Open. */
export declare function SearchResult(props: { icon?: IconName; title: string; story?: boolean; meta?: string; excerpt?: ReactNode; who?: Who; src?: string; action?: string }): React.ReactElement;
/** A choice of theme with a swatch: Night, Day, Follow the system. */
export declare function ThemeTile(props: { name: string; note?: string; variant?: "night" | "day" | "system"; selected?: boolean; onClick?: () => void }): React.ReactElement;
/** An interface language with its own name, how complete it is, and an RTL mark. */
export declare function LanguageTile(props: { [extra: string]: any; name: string; status: string; lang?: string; rtl?: boolean; selected?: boolean }): React.ReactElement;
/** A titled group of settings rows on one panel, with a one-line note. */
export declare function SettingsSection(props: { title: string; note?: string; children: ReactNode }): React.ReactElement;
/** Title, a one-line description of what happens, and the control on the end. */
export declare function SettingsRow(props: { title: string; description?: string; children: ReactNode }): React.ReactElement;
/** A model connection: kind icon, name, status word, the address or where the key lives, Test and Remove. */
export declare function ConnectionRow(props: { [extra: string]: any; icon?: IconName; name: string; status?: "connected" | "ready" | "fallback" | "offline"; detail: string }): React.ReactElement;
/** One job the engine does and which model does it: Characters, Narrator, Memory reader, Reasoning, Recall by meaning. */
export declare function JobRow(props: { [extra: string]: any; icon?: IconName; name: string; description: string; model: string; open?: boolean }): React.ReactElement;
/** Where a kind of data lives on disk, its size, and Open folder. */
export declare function FolderRow(props: { [extra: string]: any; icon?: IconName; label: string; path: string; size: string }): React.ReactElement;
/** One shortcut: what it does and its keys. Every shortcut is remappable. */
export declare function ShortcutRow(props: { [extra: string]: any; label: string; keys: string[] }): React.ReactElement;
/** The ground of a story: the place art, blurred and dimmed, under the golden-hour tint and glow. Everything in a story sits on it. */
export declare function SceneStage(props: { place?: Place; src?: string; alt?: string; height?: number; children?: ReactNode }): React.ReactElement;
/** The round glass button in a story's corners: back to the Sky, the story menu, Continue the story. */
export declare function SceneButton(props: { [extra: string]: any; icon: IconName; label: string; href?: string; pressed?: boolean; iconSize?: number; onClick?: (e: { currentTarget: Element }) => void }): React.ReactElement;
/** Top left of a story: back to the Sky, the story title in Newsreader italic, who you are playing and the book. */
export declare function SceneHeader(props: { title: string; subtitle: string; backHref?: string }): React.ReactElement;
/** Top right of a story: turns Backstage on and off in place. */
export declare function BackstageToggle(props: { on?: boolean; defaultOn?: boolean; onToggle?: (v: boolean) => void }): React.ReactElement;
/** The full-height chat column, 800px wide, lines bottom-aligned above the composer. */
export declare function ChatPanel(props: { label?: string; height?: number; composer?: ReactNode; children: ReactNode }): React.ReactElement;
/** One line in a story: speaker in their colour, story time (exact on hover), the prose with *actions* in italics, reactions under it. */
export declare function ChatLine(props: { [extra: string]: any; speaker: string; color?: string; name: string; time: string; exact?: string; timeDetail?: string; timeOpen?: boolean; text: string; dim?: boolean; hover?: boolean; take?: string; writing?: boolean; recalled?: boolean; thought?: string; children?: ReactNode }): React.ReactElement;
/** The tools that appear on a hovered line: previous and next take, Edit, Hide. */
export declare function LineTools(props: { [extra: string]: any; take?: string }): React.ReactElement;
/** A place and time heading inside the chat: "Three weeks later · Corvel Palace", with Undo right after a skip. */
export declare function TitleCard(props: { [extra: string]: any; undo?: boolean; children: ReactNode }): React.ReactElement;
/** A quiet line when someone comes or goes: "Theo went out to the back." `away` greys the face. */
export declare function StoryNote(props: { [extra: string]: any; who?: Who; src?: string; away?: boolean; children: ReactNode }): React.ReactElement;
/** When a character draws on a memory: the stored line, how sharp it is now, how they know it. */
export declare function RecallBox(props: { title?: string; memory: string; meta?: string }): React.ReactElement;
/** How a character took a line, in feelings language, from a fixed set: memory, feeling, warm, belief, mood. */
export declare function Reaction(props: { [extra: string]: any; kind: "memory" | "feeling" | "warm" | "belief" | "mood"; who?: Who; avatarSrc?: string; soft?: boolean; children: ReactNode }): React.ReactElement;
/** How your line will be read. Auto shows what it detected: "Auto · Do + Say". */
export declare function ModeChip(props: { [extra: string]: any; value?: string; detected?: string; open?: boolean }): React.ReactElement;
/** The six ways a line can be read, each with its syntax, and a note that Auto works it out. */
export declare function ModeMenu(props: { [extra: string]: any; value?: "Auto" | "Say" | "Do" | "Whisper" | "Think" | "Narrate" }): React.ReactElement;
/** Where the player writes. Simple by default; Advanced adds who will hear it, who answers, Pass time and a token count. Send is golden; while a reply streams it becomes Stop. */
export declare function Composer(props: { [extra: string]: any; value?: string; defaultValue?: string; onChange?: (v: string) => void; onSend?: (v: string) => void; placeholder?: string; mode?: string; detected?: string; modeOpen?: boolean; advanced?: boolean; defaultAdvanced?: boolean; onAdvanced?: (v: boolean) => void; streaming?: boolean; hearing?: { who?: Who; src?: string }[]; hearingText?: string; away?: string; tokens?: string; meter?: number; onStop?: () => void; onContinue?: () => void; onPassTime?: () => void; answers?: { id: string; label: string; who?: Who; src?: string; icon?: IconName }[]; answer?: string; onAnswer?: (id: string) => void }): React.ReactElement;
/** A line opened for editing, with the warning about what regenerating rewrites, and three ways out. */
export declare function EditLine(props: { [extra: string]: any; speaker: string; name: string; time: string; text: string; after?: number }): React.ReactElement;
/** The frame every widget sits in. `edit` shows the drag handle, pin and remove; `dragging` tilts it. */
export declare function Widget(props: { [extra: string]: any; label: string; width?: number; edit?: boolean; pinned?: boolean; dragging?: boolean; children: ReactNode }): React.ReactElement;
/** A character in the scene: portrait, name, mood pill, status line. Flags: thinking, a Joined badge, away. */
export declare function CharacterWidget(props: { [extra: string]: any; who?: Who; src?: string; name: string; mood?: string; status?: string; thinking?: boolean; badge?: string; away?: boolean; pinned?: boolean; edit?: boolean; dragging?: boolean; width?: number; alt?: string }): React.ReactElement;
/** The compact form of a character widget for people in the scene but not in focus. */
export declare function CharacterRowWidget(props: { [extra: string]: any; who?: Who; src?: string; name: string; status: string; away?: boolean; edit?: boolean; width?: number }): React.ReactElement;
/** The story clock: story time large, the day arc, what the time means, the place, Pass time. Exact date on hover. */
export declare function ClockWidget(props: { [extra: string]: any; time: string; rel: string; place: string; exact?: string; detail?: string; open?: boolean; kind?: "dusk" | "night"; edit?: boolean; width?: number }): React.ReactElement;
/** What is playing, where it came from, play or pause, volume. Opens the music picker. */
export declare function MusicWidget(props: { [extra: string]: any; track: string; source?: string; playing?: boolean; edit?: boolean; width?: number }): React.ReactElement;
/** The card over the rolling clouds when time passes: the jump, from and to, what it did to memory, Undo. */
export declare function TimeSkipCard(props: { [extra: string]: any; story: string; from: string; to: string; note?: string; confirm?: string; children?: ReactNode }): React.ReactElement;
/** A Backstage panel: mono title, dashed rule, one action or a status. The one blueprint surface in the app. */
export declare function BackstagePanel(props: { onAction?: () => void; title: string; action?: string; actionIcon?: IconName; status?: string; width?: number; children: ReactNode }): React.ReactElement;
/** One node of the mind graph: stage label, activation, what it held. `hot` for the path that won. */
export declare function MindNode(props: { kind: string; value: number; hot?: boolean; children: ReactNode }): React.ReactElement;
/** One job in this turn: state dot, job, model, time and detail, in mono. */
export declare function EngineRow(props: { job: string; model: string; stat: string; detail?: string; state?: "ok" | "wait" | "idle" | "bad" }): React.ReactElement;
/** How the prompt was spent: one bar in segments (rules, cards, mind, examples, history, tail) with each against its limit. */
export declare function PromptBar(props: { label: string; meta?: string; total?: number; segments: { name: string; value: number; limit: number }[] }): React.ReactElement;
declare global { interface Window { Kataki: { Icon: typeof Icon; Avatar: typeof Avatar; AvatarStack: typeof AvatarStack; Panel: typeof Panel; Divider: typeof Divider; Sky: typeof Sky; Eyebrow: typeof Eyebrow; StoryName: typeof StoryName; Text: typeof Text; Kbd: typeof Kbd; Shortcut: typeof Shortcut; Button: typeof Button; IconButton: typeof IconButton; ButtonGroup: typeof ButtonGroup; TextLink: typeof TextLink; Spinner: typeof Spinner; Field: typeof Field; TextField: typeof TextField; TextArea: typeof TextArea; Select: typeof Select; SearchField: typeof SearchField; Checkbox: typeof Checkbox; RadioGroup: typeof RadioGroup; Toggle: typeof Toggle; Segmented: typeof Segmented; Slider: typeof Slider; Chip: typeof Chip; ChoiceChips: typeof ChoiceChips; DropZone: typeof DropZone; StepHeader: typeof StepHeader; Rail: typeof Rail; PersonaSwitch: typeof PersonaSwitch; TopBar: typeof TopBar; Tabs: typeof Tabs; SideNav: typeof SideNav; Breadcrumbs: typeof Breadcrumbs; ShowMore: typeof ShowMore; Menu: typeof Menu; Tooltip: typeof Tooltip; Popover: typeof Popover; Dialog: typeof Dialog; Sheet: typeof Sheet; Toast: typeof Toast; CommandPalette: typeof CommandPalette; Callout: typeof Callout; Alert: typeof Alert; EmptyState: typeof EmptyState; ProgressBar: typeof ProgressBar; Skeleton: typeof Skeleton; StepList: typeof StepList; StatusLine: typeof StatusLine; StatePill: typeof StatePill; Tag: typeof Tag; Badge: typeof Badge; Meter: typeof Meter; MemoryRow: typeof MemoryRow; Stat: typeof Stat; StatRow: typeof StatRow; KeyValue: typeof KeyValue; ListRow: typeof ListRow; TimeStrip: typeof TimeStrip; Stamp: typeof Stamp; Changelog: typeof Changelog; Bubble: typeof Bubble; SecretCard: typeof SecretCard; Still: typeof Still; ContinueHero: typeof ContinueHero; EventCard: typeof EventCard; CharacterCard: typeof CharacterCard; AddCard: typeof AddCard; PersonaCard: typeof PersonaCard; StoryCard: typeof StoryCard; StoryPreview: typeof StoryPreview; RelationshipCard: typeof RelationshipCard; PlaceCard: typeof PlaceCard; PlotCard: typeof PlotCard; DoorCard: typeof DoorCard; SearchResult: typeof SearchResult; ThemeTile: typeof ThemeTile; LanguageTile: typeof LanguageTile; SettingsSection: typeof SettingsSection; SettingsRow: typeof SettingsRow; ConnectionRow: typeof ConnectionRow; JobRow: typeof JobRow; FolderRow: typeof FolderRow; ShortcutRow: typeof ShortcutRow; SceneStage: typeof SceneStage; SceneButton: typeof SceneButton; SceneHeader: typeof SceneHeader; BackstageToggle: typeof BackstageToggle; ChatPanel: typeof ChatPanel; ChatLine: typeof ChatLine; LineTools: typeof LineTools; TitleCard: typeof TitleCard; StoryNote: typeof StoryNote; RecallBox: typeof RecallBox; Reaction: typeof Reaction; ModeChip: typeof ModeChip; ModeMenu: typeof ModeMenu; Composer: typeof Composer; EditLine: typeof EditLine; Widget: typeof Widget; CharacterWidget: typeof CharacterWidget; CharacterRowWidget: typeof CharacterRowWidget; ClockWidget: typeof ClockWidget; MusicWidget: typeof MusicWidget; TimeSkipCard: typeof TimeSkipCard; BackstagePanel: typeof BackstagePanel; MindNode: typeof MindNode; EngineRow: typeof EngineRow; PromptBar: typeof PromptBar; ICONS: Record<IconName, string>; ART: Record<string, { src?: string; focus?: string }> } } }
