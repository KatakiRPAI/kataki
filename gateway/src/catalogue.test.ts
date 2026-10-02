import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { DatabaseSync } from 'node:sqlite'
import { test } from 'node:test'
import { pricesFrom } from './main.ts'

test('the catalogue is read without a lock or a -shm, and not with changes left in its -wal', () => {
  const dir = mkdtempSync(join(tmpdir(), 'kataki-catalogue-'))
  const file = join(dir, 'catalogue.db')
  const db = new DatabaseSync(file)
  db.exec(`CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT); INSERT INTO settings VALUES('prices', '{"m": {"input": 1, "output": 2}}')`)
  db.close()
  assert.deepEqual(pricesFrom(file), { m: { input: 1, output: 2 } })
  writeFileSync(`${file}-wal`, 'unsaved')
  assert.throws(() => pricesFrom(file), /open and close it once/)
})
