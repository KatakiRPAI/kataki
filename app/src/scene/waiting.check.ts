// Run with: node app/src/scene/waiting.check.ts (Node 24 strips the types).
import assert from 'node:assert/strict'
import { add, change, drop, sooner } from './waiting.ts'

let q = add(add(add([], 'one', 'Auto'), '*two*', 'Auto'), 'three', 'Whisper')
const [a, b, c] = q.map((w) => w.id)
assert.equal(new Set([a, b, c]).size, 3, 'every waiting line has its own id')
assert.deepEqual(q.map((w) => w.text), ['one', '*two*', 'three'], 'they wait in the order they were sent')
assert.equal(q[2].mode, 'Whisper', 'a line keeps the mode it was sent with')

q = change(q, b, { text: '  two, said  ' })
assert.deepEqual(q[1], { id: b, text: 'two, said', mode: 'Auto' })
q = change(q, b, { mode: 'Think' })
assert.deepEqual(q[1], { id: b, text: 'two, said', mode: 'Think' })
assert.deepEqual(change(q, 999, { text: 'x' }), q, 'an unknown id changes nothing')

assert.deepEqual(sooner(q, c).map((w) => w.id), [a, c, b])
assert.deepEqual(sooner(q, a).map((w) => w.id), [a, b, c], 'the first stays first')
assert.deepEqual(sooner(q, 999), q)

assert.deepEqual(drop(q, a).map((w) => w.id), [b, c])
assert.deepEqual(change(q, b, { text: '   ' }).map((w) => w.id), [a, c], 'edited down to nothing = taken out')
assert.equal(add(drop(q, c), 'four', 'Auto').at(-1)!.id > c, true, 'ids are never reused')
console.log('waiting: ok')
