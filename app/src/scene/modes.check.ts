// Run with: node app/src/scene/modes.check.ts (Node 24 strips the types).
import assert from 'node:assert/strict'
import { force, read } from './modes.ts'

assert.deepEqual(read('Hello there'), { mode: 'Say', text: 'Hello there', detected: 'Say' })
assert.equal(read('*waves* Hi').detected, 'Do + Say')
assert.equal(read('*waves*').detected, 'Do')
assert.deepEqual(read('(meet me out back)'), { mode: 'Whisper', text: 'meet me out back', detected: 'Whisper' })
assert.deepEqual(read('_he knows_'), { mode: 'Think', text: 'he knows', detected: 'Think' })
assert.deepEqual(read('> The rain stops.'), { mode: 'Narrate', text: 'The rain stops.', detected: 'Narrate' })
assert.equal(read('I (think) so').mode, 'Say', 'brackets inside a line are just words')
assert.equal(force('waves', 'Do').text, '*waves*')
assert.equal(force('(psst)', 'Say').text, 'psst')
console.log('modes: ok')
