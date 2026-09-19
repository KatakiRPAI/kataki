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
