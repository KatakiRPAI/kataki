// Every visible string comes from strings/<lang>.json as an ICU message (README › Copy rules).
import { IntlMessageFormat } from 'intl-messageformat'
import en from './strings/en.json'

export type Key = keyof typeof en
const lang = 'en'
const cache = new Map<Key, IntlMessageFormat>()

export function t(key: Key, values?: Record<string, string | number | boolean | Date>): string {
  let m = cache.get(key)
  if (!m) cache.set(key, (m = new IntlMessageFormat(en[key], lang)))
  return String(m.format(values))
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
