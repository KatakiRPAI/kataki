// Run with: node app/src/pace.check.ts (Node 24 strips the types). Fails loudly if pacing breaks.
import assert from 'node:assert/strict'
import { pacer } from './pace.ts'

let out = ''
const fast = pacer((t) => (out += t), 1000) // 40 characters a tick
fast.push('x'.repeat(100))
assert.equal(out, '', 'nothing shows before the first tick')
await fast.drain()
assert.equal(out, 'x'.repeat(100), 'all of it comes out, in order')

out = ''
const slow = pacer((t) => (out += t), 25) // one character a tick
slow.push('hello world')
await new Promise((r) => setTimeout(r, 130))
assert.ok(out.length > 0 && out.length < 11, `paced, not dumped (got ${out.length})`)
slow.flush()
assert.equal(out, 'hello world', 'Stop shows the rest at once')
await slow.drain() // already settled: resolves at once

out = ''
pacer((t) => (out += t), Infinity).push('now')
assert.equal(out, 'now', 'instant shows text as it arrives')
console.log('pace ok')
