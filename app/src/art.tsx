import type { CSSProperties, ReactNode } from 'react'
import { mediaUrl, type Item, type Palette, type Pronouns } from './api'

// Art for people and places until generated art arrives (M3): an uploaded image when there is
// one, otherwise a stand-in drawn from the item's palette.

/** The design's backdrop pairs and speaker inks. A new item takes the least-used one. */
export const PALETTES: Palette[] = [
  { bg: ['#c4ece4', '#6fb7c9'], ink: '#f2b870' },
  { bg: ['#ffe3bf', '#f2a468'], ink: '#e8cc6a' },
  { bg: ['#f8d8ec', '#c3a0ea'], ink: '#f0a58a' },
  { bg: ['#dbf2d4', '#8cc79a'], ink: '#e2c48c' },
  { bg: ['#fff3bf', '#f4c35a'], ink: '#f5b98a' },
  { bg: ['#f6ccd2', '#c77886'], ink: '#eeb4a0' },
  { bg: ['#d3e3ff', '#7ea4f0'], ink: '#e9c08f' },
  { bg: ['#e4f0ff', '#b9b3f2'], ink: '#f2c98a' },
]

/** An item's palette; someone with no library item (found by the reader) hashes their name. */
export function paletteOf(item: Item | undefined, name = item?.name ?? ''): Palette {
  if (item?.data.palette) return item.data.palette
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return PALETTES[h % PALETTES.length]
}

export const backdrop = (p: Palette) => `linear-gradient(160deg, ${p.bg[0]}, ${p.bg[1]})`

export const pronounsOf = (item: Item | undefined): Pronouns => item?.data.pronouns ?? 'they'

/** Up to two initials: "Master Oren" -> "MO". */
export const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')

/** A portrait card: the image, or initials on the backdrop; children go on top (name plate). */
export function Portrait({ item, name = item?.name ?? '', className = '', children }: {
  item?: Item
  name?: string
  className?: string
  children?: ReactNode
}) {
  const art = item?.data.portrait
  return (
    <div className={`k-portrait ${className}`} style={{ '--bg': backdrop(paletteOf(item, name)) } as CSSProperties}>
      {art ? <img className="ka-cover" src={mediaUrl(art)} alt="" /> : <span className="ka-initials" aria-hidden="true">{initials(name)}</span>}
      {children}
    </div>
  )
}

/** The brand orb: always means "dive into a scene". Label it where it is used. */
export const Orb = ({ size = 56 }: { size?: number }) => (
  <span className="k-orb" style={{ '--s': `${size}px` } as CSSProperties} aria-hidden="true" />
)

export type TimeOfDay = 'dawn' | 'day' | 'dusk' | 'night'

/** Dawn 05:00–07:59, day 08:00–16:59, dusk 17:00–19:59, night 20:00–04:59. */
export function timeOfDay(minuteOfDay: number): TimeOfDay {
  const h = Math.floor(minuteOfDay / 60) % 24
  return h >= 5 && h < 8 ? 'dawn' : h >= 8 && h < 17 ? 'day' : h >= 17 && h < 20 ? 'dusk' : 'night'
}

/** A round crop of the portrait, or initials, on the backdrop. */
export function Avatar({ item, name = item?.name ?? '', size = 44, className = '' }: {
  item?: Item
  name?: string
  size?: number
  className?: string
}) {
  const art = item?.data.portrait
  const style = { '--s': `${size}px`, '--bg': backdrop(paletteOf(item, name)) } as CSSProperties
  return (
    <span className={`k-avatar ka-avatar ${className}`} style={style} aria-hidden="true">
      {art ? <img className="ka-cover" src={mediaUrl(art)} alt="" /> : initials(name)}
    </span>
  )
}

export function AvatarStack({ people, size = 40 }: { people: { item?: Item; name: string }[]; size?: number }) {
  return (
    <span className="k-avatar-stack">
      {people.map((p, i) => <Avatar key={i} item={p.item} name={p.name} size={size} />)}
    </span>
  )
}

/** A place: its image tinted by the time of day, or a lamplit room whose window follows it. */
export function Room({ item, minute }: { item?: Item; minute: number }) {
  const tod = timeOfDay(minute)
  return (
    <div className="ka-room" data-tod={tod} aria-hidden="true">
      {item?.data.image ? (
        <img className="ka-room__img" src={mediaUrl(item.data.image)} alt="" />
      ) : (
        <>
          <span className="ka-room__window" />
          <span className="ka-room__floor" />
        </>
      )}
      <span className="ka-room__tint" />
    </div>
  )
}

// A head-and-shoulders silhouette in a 400x450 box, the portrait art's frame.
const SILHOUETTE =
  'M200 54C258 54 282 102 282 156C282 214 250 250 200 250C150 250 118 214 118 156C118 102 142 54 200 54Z' +
  'M168 238L168 282C120 292 58 314 36 356C22 384 16 420 14 450L386 450C384 420 378 384 364 356C342 314 280 292 232 282L232 238Z'

/** Someone on the stage: their portrait melting into the room, or a silhouette with a rim light. */
export function Figure({ item, name = item?.name ?? '', className = '' }: { item?: Item; name?: string; className?: string }) {
  const p = paletteOf(item, name)
  if (item?.data.portrait) return <img className={`ka-figure ka-figure--image ${className}`} src={mediaUrl(item.data.portrait)} alt="" />
  const style = { '--ink': p.ink, '--fill': `color-mix(in srgb, ${p.bg[1]} 32%, #120c09)` } as CSSProperties
  return (
    <svg className={`ka-figure ${className}`} viewBox="0 0 400 450" style={style} aria-hidden="true">
      <path d={SILHOUETTE} />
    </svg>
  )
}
