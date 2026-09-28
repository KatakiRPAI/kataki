// Run with: node app/src/errors.check.ts (Node 24 strips the types).
import assert from 'node:assert/strict'
import { classify, err } from './errors.ts'

assert.equal(classify('cannot reach http://127.0.0.1:8080/v1: ECONNREFUSED'), 'REPLY_UNREACHABLE', 'a closed port is not a refusal')
assert.equal(classify('connect ECONNREFUSED', true), 'API_UNREACHABLE')
assert.equal(classify('The model refused to continue: content policy', true), 'API_REFUSED')
assert.equal(classify('HTTP 401 Unauthorized', true), 'API_KEY_INVALID')
assert.equal(classify('HTTP 401 Unauthorized'), 'SERVER_UNAUTHORIZED')
assert.equal(classify('429 Too Many Requests', true), 'API_RATE_LIMITED')
assert.equal(classify("This model's maximum context length is 8192 tokens", true), 'CONTEXT_TOO_SMALL')
assert.equal(classify('The model `gpt-9` does not exist', true), 'API_MODEL_NOT_FOUND')
assert.equal(classify('model "qwen" not found'), 'MODEL_GONE')
assert.equal(classify('ReadTimeout: timed out'), 'REPLY_TIMEOUT')
assert.equal(classify('ReadTimeout: timed out', false, true), 'SERVER_TIMEOUT')
assert.equal(classify('something else entirely'), 'UNKNOWN')
assert.equal(err('SERVER_TIMEOUT', { server: 'llama.cpp' }).title, 'llama.cpp took too long')
assert.ok(!err('SERVER_TIMEOUT').title.includes('{'), 'an unknown fact never shows as {braces}')
console.log('errors: ok')
