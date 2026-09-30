// Run with: node app/src/scene/modes.check.ts (Node 24 strips the types).
import assert from 'node:assert/strict'
import { force, kind, read } from './modes.ts'

assert.deepEqual(read('Hello there'), { mode: 'Say', text: 'Hello there', detected: 'Say' })
assert.equal(read('*waves* Hi').detected, 'Do + Say')
assert.equal(read('*waves*').detected, 'Do')
assert.deepEqual(read('(meet me out back)'), { mode: 'Whisper', text: 'meet me out back', detected: 'Whisper' })
assert.deepEqual(read('(meet me out back).'), { mode: 'Whisper', text: 'meet me out back.', detected: 'Whisper' })
assert.deepEqual(read('_he knows_'), { mode: 'Think', text: 'he knows', detected: 'Think' })
// punctuation outside the markers still makes a whole thought
assert.deepEqual(read('_interesting_.'), { mode: 'Think', text: 'interesting.', detected: 'Think' })
assert.deepEqual(read('_interesting_'), { mode: 'Think', text: 'interesting', detected: 'Think' })
assert.equal(read('"_why now?_"').mode, 'Think')
// mixed lines are read span by span; the text keeps its markers for the renderer and the engine
assert.deepEqual(read("that's _interesting_"), { mode: 'Say', text: "that's _interesting_", detected: 'Say + Think' })
assert.deepEqual(read("*leans in* that's _interesting_"), { mode: 'Do', text: "*leans in* that's _interesting_", detected: 'Do + Say + Think' })
assert.equal(read('*frowns* _he is lying_').detected, 'Do + Think')
assert.equal(read('*frowns* _he is lying_').mode, 'Do')
assert.equal(read('*sighs*.').detected, 'Do')
assert.deepEqual(read('> The rain stops.'), { mode: 'Narrate', text: 'The rain stops.', detected: 'Narrate' })
assert.equal(read('I (think) so').mode, 'Say', 'brackets inside a line are just words')
assert.equal(read('call it my_file_name').detected, 'Say', 'underscores inside a word are not a thought')
assert.equal(read('').detected, '')
// the /g regexes must not carry state between calls
assert.equal(read('*a*').detected, 'Do')
assert.equal(read('*a*').detected, 'Do')
assert.equal(force('waves', 'Do').text, '*waves*')
assert.equal(force('*waves* hi', 'Do').text, '*waves* hi')
assert.equal(force('(psst)', 'Say').text, 'psst')
assert.equal(force('_hm_.', 'Think').text, 'hm.')
assert.equal(force('he knows', 'Think').text, 'he knows')
assert.equal(force('> it rains', 'Say').text, 'it rains')
assert.equal(kind({ speaker_id: null }), 'narrate')
assert.equal(kind({ speaker_id: 1, audience: [] }), 'think')
assert.equal(kind({ speaker_id: 1, audience: [2] }), 'whisper')
assert.equal(kind({ speaker_id: 1, audience: null }), undefined)
console.log('modes: ok')
