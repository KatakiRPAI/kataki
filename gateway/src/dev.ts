// `pnpm -C gateway dev`: the gateway on one machine with nothing to install. Postgres is PGlite
// (in this process, kept in .dev/gateway-pg), mail is printed, and the secrets are dev ones
// unless the environment already has them. Never for anything a stranger can reach.
import { mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { PGlite } from '@electric-sql/pglite'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'
import { start } from './main.ts'

const data = process.env.KATAKI_PG_DATA ?? fileURLToPath(new URL('../../.dev/gateway-pg', import.meta.url))
mkdirSync(data, { recursive: true })
const db = await PGlite.create(data)
const pgPort = Number(process.env.KATAKI_PG_PORT ?? 54329)
await new PGLiteSocketServer({ db, port: pgPort, host: '127.0.0.1' }).start()

const dev: Record<string, string> = {
  DATABASE_URL: `postgres://postgres@127.0.0.1:${pgPort}/postgres`,
  KATAKI_DB_POOL: '1', // PGlite is one connection
  KATAKI_ORIGIN: 'http://localhost:8787',
  KATAKI_ENGINE: 'http://127.0.0.1:8788',
  BETTER_AUTH_SECRET: 'dev-only-better-auth-secret-not-for-production',
  KATAKI_GATEWAY_SECRET: 'dev-only-gateway-signing-secret-32b',
  KATAKI_GATEWAY_KEY: 'dev-only-gateway-key',
  KATAKI_WEB: fileURLToPath(new URL('../../app/dist-web', import.meta.url)),
  KATAKI_STARTER_CREDIT: '1',
  KATAKI_CLOUD_DIR: fileURLToPath(new URL('../../.dev/gateway-cloud', import.meta.url)),
  KATAKI_PWNED: '0',
}
for (const [k, v] of Object.entries(dev)) process.env[k] ??= v
await start()
