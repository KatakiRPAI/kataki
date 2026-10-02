// The desktop's profiles: a name and the folder that holds its library
// (docs/specs/2026-10-02-profiles-and-accounts.md §2). Node only, no Electron, so
// profiles.check.ts can run it.
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'

export type Profile = { id: string; name: string; folder: string }
export type Profiles = { last: string; profiles: Profile[] }

/** The saved list, or just `first` when there is none to read. */
export function load(file: string, first: Profile): Profiles {
  try {
    const p = JSON.parse(readFileSync(file, 'utf8')) as Profiles
    const ok = Array.isArray(p.profiles) && p.profiles.length > 0 && p.profiles.every((x) => typeof x.id === 'string' && typeof x.name === 'string' && typeof x.folder === 'string')
    if (ok) return { last: String(p.last), profiles: p.profiles }
  } catch { /* none yet, or not ours: start again */ }
  return { last: first.id, profiles: [first] }
}

export function save(file: string, p: Profiles): void {
  mkdirSync(dirname(file), { recursive: true })
  writeFileSync(file, JSON.stringify(p, null, 2))
}

export const current = (p: Profiles): Profile => p.profiles.find((x) => x.id === p.last) ?? p.profiles[0]

/** What a folder is to us: it holds a library, it is empty, it holds something else, or it is not there. */
export function kind(folder: string): 'library' | 'empty' | 'other' | 'missing' {
  if (!existsSync(folder)) return 'missing'
  if (existsSync(join(folder, 'library.db'))) return 'library'
  try { return readdirSync(folder).length ? 'other' : 'empty' } catch { return 'other' } // a file, or not ours to read
}

/** The sync service or network share a folder sits in: SQLite libraries get corrupted there.
 *  ponytail: a guess from the path's words, good for a warning the person can dismiss, no more. */
export function synced(folder: string): string | null {
  if (/^(\\\\|\/\/)/.test(folder)) return 'a network drive'
  const parts = folder.toLowerCase().split(/[\\/]+/)
  const hit = ([['onedrive', 'OneDrive'], ['dropbox', 'Dropbox'], ['icloud', 'iCloud'], ['mobile documents', 'iCloud'], ['google drive', 'Google Drive'], ['googledrive', 'Google Drive'], ['my drive', 'Google Drive']] as const)
    .find(([word]) => parts.some((part) => part.startsWith(word)))
  return hit ? hit[1] : null
}

const same = (a: string, b: string) => (process.platform === 'win32' ? resolve(a).toLowerCase() === resolve(b).toLowerCase() : resolve(a) === resolve(b))

export const cleanName = (name: unknown): string => (typeof name === 'string' ? name.trim().slice(0, 40) : '') || 'Profile'

/** List a folder as a profile. A folder that is already listed is that profile, not a second one. */
export function add(p: Profiles, name: string, folder: string): { profiles: Profiles; profile: Profile; existing: boolean } {
  const found = p.profiles.find((x) => same(x.folder, folder))
  if (found) return { profiles: p, profile: found, existing: true }
  let n = p.profiles.length + 1
  while (p.profiles.some((x) => x.id === `p${n}`)) n++
  const profile = { id: `p${n}`, name: cleanName(name), folder: resolve(folder) }
  return { profiles: { ...p, profiles: [...p.profiles, profile] }, profile, existing: false }
}

export const rename = (p: Profiles, id: string, name: string): Profiles => ({ ...p, profiles: p.profiles.map((x) => (x.id === id ? { ...x, name: cleanName(name) } : x)) })

/** Take a profile off the list. Its folder stays where it is. */
export function forget(p: Profiles, id: string): Profiles {
  if (current(p).id === id) throw new Error('the open profile cannot be forgotten')
  return { ...p, profiles: p.profiles.filter((x) => x.id !== id) }
}
