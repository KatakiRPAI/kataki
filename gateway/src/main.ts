// `pnpm -C gateway start`: the gateway, from its environment (docs/specs/2026-10-02-kataki-online.md §6, §7).
import { createServer } from 'node:http'
import { DatabaseSync } from 'node:sqlite'
import pg from 'pg'
import { sweep } from './account.ts'
import { chargeStorage } from './cloud.ts'
import { createGateway } from './app.ts'
import { makeAuth, migrateAuth, socialFrom, type Send } from './auth.ts'
import { mailer } from './mail.ts'
import { migrate } from './db.ts'
import type { Prices } from './money.ts'

function need(name: string): string {
  const v = process.env[name]
  if (!v) throw new Error(`${name} is not set`)
  return v
}

/** The service's price table: the `prices` setting of the same catalogue the engine is given. */
export function pricesFrom(catalogue: string): Prices {
  const db = new DatabaseSync(catalogue, { readOnly: true })
  try {
    const row = db.prepare("SELECT value FROM settings WHERE key = 'prices'").get() as { value: string } | undefined
    return row ? JSON.parse(row.value) : {}
  } finally {
    db.close()
  }
}

export async function start(send: Send = mailer(process.env)) {
  const origin = need('KATAKI_ORIGIN')
  const signing = need('KATAKI_GATEWAY_SECRET')
  if (Buffer.byteLength(signing) < 32) throw new Error('KATAKI_GATEWAY_SECRET must be at least 32 bytes')
  const pool = new pg.Pool({ connectionString: need('DATABASE_URL'), max: Number(process.env.KATAKI_DB_POOL ?? 10) })
  const social = socialFrom(process.env)
  const auth = makeAuth({ pool, origin, secret: need('BETTER_AUTH_SECRET'), send, pwned: process.env.KATAKI_PWNED !== '0', social })
  await migrateAuth(auth)
  await migrate(pool)
  const engine = need('KATAKI_ENGINE')
  // cloud save for the desktop is on when there is somewhere to keep the snapshots
  const cloud = process.env.KATAKI_CLOUD_DIR ? { dir: process.env.KATAKI_CLOUD_DIR, maxBytes: Number(process.env.KATAKI_CLOUD_MAX_BYTES ?? 250 * 1024 * 1024) } : undefined
  const gateway = createGateway({
    auth, pool, origin, send, cloud,
    engine,
    secret: signing,
    key: need('KATAKI_GATEWAY_KEY'),
    prices: process.env.KATAKI_CATALOGUE ? pricesFrom(process.env.KATAKI_CATALOGUE) : {},
    web: process.env.KATAKI_WEB,
    starter: BigInt(Math.round(Number(process.env.KATAKI_STARTER_CREDIT ?? 0) * 1e6)),
    social: Object.keys(social),
  })
  const server = createServer(gateway)
  const port = Number(process.env.PORT ?? 8787)
  await new Promise<void>((done) => server.listen(port, process.env.KATAKI_BIND ?? '127.0.0.1', done))
  // accounts whose day has come are removed now and every hour
  const leaving = () => sweep({ auth, pool, origin, engine, secret: signing, send, cloud }).catch((e) => console.error('gateway: sweep failed:', e instanceof Error ? e.message : e))
  // and cloud storage past the free limit is charged, once a day per account (an hourly try is a no-op after the first)
  const charging = () => cloud && chargeStorage({ pool, origin, ...cloud }).catch((e) => console.error('gateway: storage charge failed:', e instanceof Error ? e.message : e))
  void leaving()
  void charging()
  setInterval(() => { void leaving(); void charging() }, 3_600_000).unref()
  console.log(`gateway: ${origin} (listening on ${port}); sign in with: password${Object.keys(social).map((p) => `, ${p}`).join('')}`)
  return { server, pool }
}

if (import.meta.main) await start()
