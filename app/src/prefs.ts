// Settings the app itself reads, loaded once from the engine's settings table and saved on
// every change ("Every change applies immediately and saves itself", SCREENS.md › K).
import { useSyncExternalStore } from 'react'
import { api } from './api'

export type Prefs = Record<string, unknown>
let prefs: Prefs = {}
let loaded = false
const subs = new Set<() => void>()
const emit = () => subs.forEach((f) => f())

export function loadPrefs() {
  return api<Prefs>('/settings').then((p) => { prefs = p; loaded = true; apply(); emit() }, () => {})
}
export function setPref(key: string, value: unknown) {
  prefs = { ...prefs, [key]: value }
  apply()
  emit()
  return api('/settings', 'PUT', { [key]: value }).catch(() => {})
}
export function usePrefs(): [Prefs, boolean] {
  const p = useSyncExternalStore((f) => (subs.add(f), () => subs.delete(f)), () => prefs)
  return [p, loaded]
}
export const pref = <T,>(key: string, fallback: T): T => (prefs[key] as T) ?? fallback

/** What Appearance changes, applied to the page itself. */
function apply() {
  const root = document.documentElement
  const size = Number(prefs['appearance.textSize'] ?? 100)
  root.style.zoom = size === 100 ? '' : String(size / 100)
  const motion = prefs['appearance.motion'] ?? 'system'
  root.dataset.motion = motion === 'reduce' || (motion === 'system' && matchMedia('(prefers-reduced-motion: reduce)').matches) ? 'reduce' : 'full'
  const face = prefs['appearance.storyFont'] as string | undefined
  root.style.setProperty('--font-story', face === 'figtree' ? 'Figtree, system-ui, sans-serif' : face === 'atkinson' ? "'Atkinson Hyperlegible', Figtree, sans-serif" : '')
  if (!face || face === 'newsreader') root.style.removeProperty('--font-story')
  root.dataset.contrast = prefs['appearance.contrast'] ? 'more' : ''
}
/** Night or Day for the Sky, following the system when asked. */
export function skyTheme(p: Prefs): 'night' | 'day' {
  const t = p['appearance.theme'] ?? 'night'
  return t === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'day' : 'night') : (t as 'night' | 'day')
}
