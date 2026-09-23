// Run: node app/checks/auto.check.ts (Node 24 strips the types)
import assert from 'node:assert/strict'
import { readLine } from '../src/scene/auto.ts'

const people = [{ id: 1, name: 'Mira' }, { id: 2, name: 'Master Oren' }]
const read = (line: string) => readLine(line, people)

assert.deepEqual(read('Evening, Mira.'), { mode: 'say', text: 'Evening, Mira.', label: 'Say' })
assert.equal(read('*leans closer* Then we meet at the lighthouse.').label, 'Do + Say')
assert.equal(read('*sits down*').label, 'Do')
assert.deepEqual(read('(I don’t trust him.)'), { mode: 'think', text: 'I don’t trust him.', label: 'Think' })
assert.deepEqual(read('>> Thunder rolls over the harbour.'), { mode: 'narrate', text: 'Thunder rolls over the harbour.', label: 'Narrate' })
assert.deepEqual(read('@mira, the ledger is safe.'), { mode: 'whisper', text: 'the ledger is safe.', to: 1, label: 'Whisper to Mira' })
assert.equal(read('@Master Oren listen').to, 2)
assert.equal(read('@Miranda hi').mode, 'say') // not someone here
assert.equal(read('@Tobin psst').mode, 'say') // not present: said aloud rather than lost
console.log('auto: ok')
