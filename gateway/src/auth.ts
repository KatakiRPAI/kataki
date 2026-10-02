// Accounts: Better Auth on the gateway's Postgres, set as docs/specs/2026-10-02-kataki-online.md
// §2 says and why. G1 is email and password; later slices add to this one place.
import { randomUUID } from 'node:crypto'
import { betterAuth } from 'better-auth'
import { getMigrations } from 'better-auth/db/migration'
import { haveIBeenPwned } from 'better-auth/plugins'
import type { Pool } from 'pg'

export type Send = (to: string, subject: string, text: string) => void | Promise<void>
export type AuthConfig = {
  pool: Pool
  origin: string // where the gateway is reached, e.g. https://app.kataki.example
  secret: string
  send: Send
  pwned?: boolean // refuse breached passwords (asks api.pwnedpasswords.com); tests turn it off
}

const DAY = 86_400

export function makeAuth({ pool, origin, secret, send, pwned = true }: AuthConfig) {
  return betterAuth({
    baseURL: origin,
    secret,
    database: pool,
    trustedOrigins: [origin],
    emailAndPassword: {
      enabled: true,
      // an unverified account gets no session and holds nothing; and sign-up answers the same
      // for a known address as for a new one
      requireEmailVerification: true,
      minPasswordLength: 12,
      maxPasswordLength: 128,
      revokeSessionsOnPasswordReset: true,
    },
    emailVerification: {
      sendOnSignUp: true,
      autoSignInAfterVerification: true,
      // not awaited by the library's caller either: the answer takes the same time whoever asks
      sendVerificationEmail: async ({ user, url }) => {
        void send(user.email, 'Confirm your email for Kataki', `Open this link to finish making your Kataki account:\n\n${url}\n\nIt works for one hour. If you did not ask for this, ignore it.`)
      },
    },
    session: { expiresIn: 30 * DAY, updateAge: DAY, freshAge: 600 },
    rateLimit: { storage: 'database' }, // on in production; shared by every gateway process
    advanced: {
      // a user's id is their library id: lowercase, so it passes the engine's folder-name rule
      database: { generateId: () => randomUUID() },
    },
    plugins: [haveIBeenPwned({ enabled: pwned })],
  })
}

export type Auth = ReturnType<typeof makeAuth>

/** Create or bring up to date the tables Better Auth owns. */
export async function migrateAuth(auth: Auth): Promise<void> {
  await (await getMigrations(auth.options)).runMigrations()
}
