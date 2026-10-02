// The desktop's profiles: a name and the folder that holds its library
// (docs/specs/2026-10-02-profiles-and-accounts.md §2). Node only, no Electron, so
// profiles.check.ts can run it.
import { createHash, randomBytes, scryptSync, timingSafeEqual } from 'node:crypto'
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { basename, dirname, join, resolve } from 'node:path'

export type Pin = { salt: string; hash: string }
// opened: its library has been seen there. pin: asked for before it opens (privacy on this
// computer; nothing is encrypted). movedFrom: where the library was before it was moved.
export type Profile = { id: string; name: string; folder: string; opened?: boolean; pin?: Pin; movedFrom?: string }
// ask: choose a profile each time Kataki starts. move: a library to move before the next start.
export type Profiles = { last: string; profiles: Profile[]; ask?: boolean; move?: { id: string; to: string } }

/** The saved list, or just `first` when there is none to read. */
export function load(file: string, first: Profile): Profiles {
  try {
    const p = JSON.parse(readFileSync(file, 'utf8')) as Profiles
    const ok = Array.isArray(p.profiles) && p.profiles.length > 0 && p.profiles.every((x) => typeof x.id === 'string' && typeof x.name === 'string' && typeof x.folder === 'string')
    if (ok) return { last: String(p.last), profiles: p.profiles, ...(p.ask ? { ask: true } : {}), ...(p.move ? { move: p.move } : {}) }
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

/** A profile whose library should be there and is not: the folder is gone, or it once held a
 *  library and no longer does. A folder that has never held one is a new profile, not a loss. */
export const lost = (p: Profile): boolean => kind(p.folder) === 'missing' || (!!p.opened && kind(p.folder) !== 'library')

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

/** What the page may know of a profile: never the PIN's hash. */
export const shown = (x: Profile) => ({ id: x.id, name: x.name, folder: x.folder, locked: !!x.pin, movedFrom: x.movedFrom })

// A PIN: 4 to 12 digits, kept as a salted scrypt hash. It keeps a profile out of casual reach on
// this computer; the library's files are not encrypted, and the copy on the screen says so.
export const validPin = (pin: unknown): pin is string => typeof pin === 'string' && /^\d{4,12}$/.test(pin)
const hashed = (pin: string, salt: string) => scryptSync(pin, Buffer.from(salt, 'hex'), 32)
export function pinOf(pin: string): Pin {
  const salt = randomBytes(16).toString('hex')
  return { salt, hash: hashed(pin, salt).toString('hex') }
}
/** Does this PIN open the profile? One with no PIN opens for anything. */
export function pinOk(x: Profile, pin: unknown): boolean {
  if (!x.pin) return true
  return typeof pin === 'string' && timingSafeEqual(hashed(pin, x.pin.salt), Buffer.from(x.pin.hash, 'hex'))
}
/** Set, change or (with `next` null) remove a profile's PIN. The one it has, if any, is needed. */
export function setPin(p: Profiles, id: string, was: unknown, next: string | null): Profiles | null {
  const x = p.profiles.find((y) => y.id === id)
  if (!x || !pinOk(x, was) || (next !== null && !validPin(next))) return null
  const { pin: _old, ...rest } = x
  return { ...p, profiles: p.profiles.map((y) => (y.id === id ? (next === null ? rest : { ...rest, pin: pinOf(next) }) : y)) }
}
/** Kataki asks which profile before it opens anything: when told to, or when the last one has a PIN. */
export const needsPicker = (p: Profiles): boolean => (!!p.ask && p.profiles.length > 1) || !!current(p).pin

const sha = (file: string) => createHash('sha256').update(readFileSync(file)).digest('hex')
/** Copy a library to an empty folder and check the copy: Kataki is closed, so the files are
 *  whole. The old folder is left as it is. Throws, removing what it copied, if the copy is not
 *  the same. ponytail: reads library.db twice to compare; fine for a library on one disk. */
export function moveLibrary(from: string, to: string): void {
  if (kind(from) !== 'library') throw new Error('there is no library to move')
  if (kind(to) !== 'empty' && kind(to) !== 'missing') throw new Error('the new folder is not empty')
  mkdirSync(to, { recursive: true })
  try {
    // not the lock, and not downloaded models: those belong to this computer (KATAKI_HOME), not to a library
    cpSync(from, to, { recursive: true, filter: (src) => basename(src) !== 'library.lock' && resolve(src) !== resolve(from, 'models') })
    if (sha(join(from, 'library.db')) !== sha(join(to, 'library.db'))) throw new Error('the copy does not match')
  } catch (e) {
    rmSync(to, { recursive: true, force: true })
    throw e
  }
}

/** Take a profile off the list. Its folder stays where it is. */
export function forget(p: Profiles, id: string): Profiles {
  if (current(p).id === id) throw new Error('the open profile cannot be forgotten')
  return { ...p, profiles: p.profiles.filter((x) => x.id !== id) }
}
