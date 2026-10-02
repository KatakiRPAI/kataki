// Run with: node app/electron/profiles.check.ts (Node 24 strips the types). Fails loudly if the profile list breaks.
import assert from 'node:assert/strict'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { add, cleanName, current, forget, kind, load, lost, moveLibrary, needsPicker, pinOk, rename, save, setPin, shown, synced, validPin } from './profiles.ts'
import { existsSync, readFileSync } from 'node:fs'

const tmp = mkdtempSync(join(tmpdir(), 'kataki-profiles-'))
const file = join(tmp, 'userData', 'profiles.json')
const main = { id: 'main', name: 'Main', folder: join(tmp, 'main') }

assert.deepEqual(load(file, main), { last: 'main', profiles: [main] }, 'no file: just the first profile')
mkdirSync(join(tmp, 'userData'))
writeFileSync(file, '{not json')
assert.deepEqual(load(file, main), { last: 'main', profiles: [main] }, 'a broken file: the first profile again')
writeFileSync(file, '{"last":"x","profiles":[]}')
assert.equal(load(file, main).profiles.length, 1, 'an empty list is no list')

assert.equal(kind(join(tmp, 'nowhere')), 'missing')
mkdirSync(main.folder)
assert.equal(kind(main.folder), 'empty')
writeFileSync(join(main.folder, 'notes.txt'), '')
assert.equal(kind(main.folder), 'other')
writeFileSync(join(main.folder, 'library.db'), '')
assert.equal(kind(main.folder), 'library')

assert.equal(lost({ ...main, folder: join(tmp, 'nowhere') }), true, 'the folder is gone')
assert.equal(lost({ ...main, folder: join(tmp, 'fresh') }), true)
mkdirSync(join(tmp, 'fresh'))
assert.equal(lost({ ...main, folder: join(tmp, 'fresh') }), false, 'a new profile: nothing to lose yet')
assert.equal(lost({ ...main, folder: join(tmp, 'fresh'), opened: true }), true, 'it held a library once and does not now')
assert.equal(lost({ ...main, opened: true }), false)

let p = load(file, main)
const second = add(p, '  Second  ', join(tmp, 'second'))
assert.equal(second.existing, false)
assert.equal(second.profile.name, 'Second')
p = second.profiles
const again = add(p, 'Again', join(tmp, 'second', '.'))
assert.equal(again.existing, true, 'one folder, one profile')
assert.equal(again.profiles.profiles.length, 2)

save(file, p)
assert.deepEqual(load(file, main), p, 'what was saved is what loads')
assert.equal(current(p).id, 'main')
assert.equal(current({ ...p, last: 'gone' }).id, 'main', 'a last that is gone falls back to the first')

p = rename(p, second.profile.id, 'x'.repeat(60))
assert.equal(p.profiles[1].name.length, 40)
assert.equal(cleanName('   '), 'Profile')
assert.equal(cleanName(7), 'Profile')

assert.throws(() => forget(p, 'main'), 'the open profile stays')
assert.equal(forget(p, second.profile.id).profiles.length, 1)
const third = add(forget(p, second.profile.id), 'Third', join(tmp, 'third'))
assert.notEqual(third.profile.id, 'main', 'ids never collide')

assert.equal(synced('C:\\Users\\a\\OneDrive\\Kataki'), 'OneDrive')
assert.equal(synced('C:\\Users\\a\\OneDrive - Work\\Kataki'), 'OneDrive')
assert.equal(synced('/Users/a/Library/Mobile Documents/com~apple~CloudDocs/Kataki'), 'iCloud')
assert.equal(synced('/Users/a/Dropbox/Kataki'), 'Dropbox')
assert.equal(synced('G:\\My Drive\\Kataki'), 'Google Drive')
assert.equal(synced('\\\\nas\\share\\Kataki'), 'a network drive')
assert.equal(synced('D:\\Kataki'), null)

// a PIN: digits, hashed, needed to change or remove itself, and never shown to the page
assert.ok(validPin('1234') && validPin('123456789012'))
for (const bad of ['123', '1234567890123', '12a4', '', 1234]) assert.ok(!validPin(bad))
let q = load(file, main)
assert.equal(needsPicker(q), false)
assert.equal(setPin(q, 'main', undefined, '12'), null, 'too short')
q = setPin(q, 'main', undefined, '4821')!
const locked = current(q)
assert.ok(locked.pin && !JSON.stringify(locked.pin).includes('4821'), 'kept as a hash')
assert.equal(pinOk(locked, '4821'), true)
assert.equal(pinOk(locked, '4822'), false)
assert.equal(pinOk(locked, undefined), false)
assert.equal(needsPicker(q), true, 'a locked profile is asked for before it opens')
assert.deepEqual(Object.keys(shown(locked)).sort(), ['folder', 'id', 'locked', 'movedFrom', 'name'])
assert.equal(shown(locked).locked, true)
assert.equal(setPin(q, 'main', '0000', null), null, 'the PIN it has is needed to remove it')
q = setPin(q, 'main', '4821', null)!
assert.equal(current(q).pin, undefined)
assert.equal(needsPicker({ ...q, ask: true }), q.profiles.length > 1)
save(file, { ...q, ask: true, move: { id: 'main', to: join(tmp, 'x') } })
assert.equal(load(file, main).ask, true)
assert.deepEqual(load(file, main).move, { id: 'main', to: join(tmp, 'x') })

// moving a library: an exact copy in an empty folder, the old one untouched, the lock left behind
const from = join(tmp, 'from')
mkdirSync(join(from, 'blobs'), { recursive: true })
writeFileSync(join(from, 'library.db'), 'the library')
writeFileSync(join(from, 'library.lock'), '')
writeFileSync(join(from, 'blobs', 'a.png'), 'a picture')
mkdirSync(join(from, 'models'))
writeFileSync(join(from, 'models', 'big.bin'), 'a downloaded model')
const to = join(tmp, 'to')
moveLibrary(from, to)
assert.equal(readFileSync(join(to, 'library.db'), 'utf8'), 'the library')
assert.equal(readFileSync(join(to, 'blobs', 'a.png'), 'utf8'), 'a picture')
assert.equal(existsSync(join(to, 'library.lock')), false)
assert.equal(existsSync(join(to, 'models')), false, 'downloaded models stay with the computer')
assert.equal(kind(from), 'library', 'the old folder is as it was')
assert.throws(() => moveLibrary(from, to), /not empty/)
assert.throws(() => moveLibrary(join(tmp, 'nowhere'), join(tmp, 'elsewhere')), /no library/)
assert.equal(existsSync(join(tmp, 'elsewhere')), false)

console.log('profiles: ok')
