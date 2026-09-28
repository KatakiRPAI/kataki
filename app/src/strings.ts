// Every visible string comes from strings/<lang>.json as an ICU message (README › Copy rules).
// A language file may be partial: a key it doesn't have reads in English.
import { IntlMessageFormat } from 'intl-messageformat'
import en from './strings/en.json'

export type Key = keyof typeof en
type Strings = Partial<Record<Key, string>>

// every strings/<lang>.json but the error catalogues, found at build time
const files = import.meta.glob<{ default: Strings }>(['./strings/*.json', '!./strings/errors.*.json'], { eager: true })
export const LANGUAGES: Record<string, Strings> = Object.fromEntries(
  Object.entries(files).map(([path, mod]) => [path.replace(/^.*\/(.+)\.json$/, '$1'), mod.default]),
)
export const RTL = new Set(['ar', 'fa', 'he', 'ur'])

/** How much of a language is translated, 0–1 (K3: selectable from 95%). */
export const complete = (lang: string) => Object.keys(LANGUAGES[lang] ?? {}).filter((k) => k in en).length / Object.keys(en).length

// The language is chosen once per window: switching restarts the renderer (K3).
const chosen = (() => {
  try { return localStorage.getItem('kataki.language') ?? 'en' } catch { return 'en' }
})()
export const lang = LANGUAGES[chosen] && complete(chosen) >= 0.95 ? chosen : 'en'
const own = LANGUAGES[lang] ?? {}
const cache = new Map<Key, IntlMessageFormat>()

export function t(key: Key, values?: Record<string, string | number | boolean | Date>): string {
  let m = cache.get(key)
  if (!m) {
    const text = own[key]
    cache.set(key, (m = text ? new IntlMessageFormat(text, lang) : new IntlMessageFormat(en[key], 'en')))
  }
  return String(m.format(values))
}

/** Pick a language: kept in this window's storage and in Settings, then the window restarts. */
export function switchLanguage(to: string) {
  try { localStorage.setItem('kataki.language', to) } catch { /* for this window */ }
  location.reload()
}

/** Relative real time: "2 hours ago", "last week". */
const rtf = new Intl.RelativeTimeFormat(lang, { numeric: 'auto' })
export function relative(ms: number): string {
  const s = (ms - Date.now()) / 1000
  const steps: [Intl.RelativeTimeFormatUnit, number][] = [['second', 60], ['minute', 60], ['hour', 24], ['day', 7], ['week', 4.35], ['month', 12], ['year', Infinity]]
  let v = s
  for (const [unit, size] of steps) {
    if (Math.abs(v) < size) return rtf.format(Math.round(v), unit)
    v /= size
  }
  return ''
}

// The page reads in its language, and right to left where it should. `?dir=rtl` (kept for the
// tab) mirrors the layout in any language, to check R2 without a finished translation.
{
  const asked = new URLSearchParams(location.search).get('dir')
  try { if (asked) sessionStorage.setItem('kataki.dir', asked) } catch { /* this load only */ }
  let dir = RTL.has(lang) ? 'rtl' : 'ltr'
  try { dir = sessionStorage.getItem('kataki.dir') ?? dir } catch { /* as the language says */ }
  document.documentElement.lang = lang
  document.documentElement.dir = dir
}
