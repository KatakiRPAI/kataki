// The gateway's own tables: numbered SQL files in ../migrations, applied in order, forward only.
// Better Auth's tables are its own to migrate (auth.ts).
import { readdirSync, readFileSync } from 'node:fs'
import type { Pool } from 'pg'

const dir = new URL('../migrations/', import.meta.url)

export async function migrate(pool: Pool): Promise<void> {
  await pool.query('CREATE TABLE IF NOT EXISTS schema_version(n integer PRIMARY KEY, at timestamptz NOT NULL DEFAULT now())')
  const done = new Set((await pool.query('SELECT n FROM schema_version')).rows.map((r) => r.n as number))
  for (const file of readdirSync(dir).filter((f) => /^\d+_.*\.sql$/.test(f)).sort()) {
    const n = Number.parseInt(file, 10)
    if (done.has(n)) continue
    const client = await pool.connect()
    try { // a migration lands whole or not at all
      await client.query('BEGIN')
      await client.query(readFileSync(new URL(file, dir), 'utf8'))
      await client.query('INSERT INTO schema_version(n) VALUES($1)', [n])
      await client.query('COMMIT')
    } catch (e) {
      await client.query('ROLLBACK')
      throw e
    } finally {
      client.release()
    }
  }
}
