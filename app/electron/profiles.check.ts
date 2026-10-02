// Run with: node app/electron/profiles.check.ts (Node 24 strips the types). Fails loudly if the profile list breaks.
import assert from 'node:assert/strict'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { add, cleanName, current, forget, kind, load, lost, rename, save, synced } from './profiles.ts'

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

console.log('profiles: ok')
