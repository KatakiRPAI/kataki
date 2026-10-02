// Accounts: Better Auth on the gateway's Postgres, set as docs/specs/2026-10-02-kataki-online.md
// §2 says and why. G1 is email and password; later slices add to this one place.
import { randomUUID } from 'node:crypto'
import { betterAuth } from 'better-auth'
import { APIError } from 'better-auth/api'
import { getMigrations } from 'better-auth/db/migration'
import { haveIBeenPwned, magicLink } from 'better-auth/plugins'
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
      resetPasswordTokenExpiresIn: 15 * 60,
      sendResetPassword: async ({ user, url }) => {
        void send(user.email, 'Reset your Kataki password', `Open this link to choose a new password:\n\n${url}\n\nIt works for 15 minutes. If you did not ask for this, ignore it: nothing has changed.`)
      },
      // every change to how an account is entered is told to its owner
      onPasswordReset: async ({ user }) => {
        void send(user.email, 'Your Kataki password was changed', `The password for your Kataki account was just changed, and every device was signed out.\n\nIf this was not you, reset it now at ${origin}/app/ and check who else can read this mailbox.`)
      },
      // sign-up answers a known address like a new one; this is how its owner hears of it
      onExistingUserSignUp: async ({ user }) => {
        void send(user.email, 'You already have a Kataki account', `Someone, maybe you, tried to make a Kataki account with this address. You already have one: sign in at ${origin}/app/, or reset your password there.\n\nIf it was not you, nothing has changed.`)
      },
    },
    emailVerification: {
      sendOnSignUp: true,
      autoSignInAfterVerification: true,
      // not awaited by the library's caller either: the answer takes the same time whoever asks
      sendVerificationEmail: async ({ user, url }) => {
        void send(user.email, 'Confirm your email for Kataki', `Open this link to finish making your Kataki account:\n\n${url}\n\nIt works for one hour. If you did not ask for this, ignore it.`)
      },
    },
    // 18 or older, said at sign-up and kept on the account with the time it was made
    user: { additionalFields: { adult: { type: 'boolean', required: true, input: true } } },
    databaseHooks: {
      user: {
        create: {
          before: async (user) => {
            if (user.adult !== true) throw new APIError('BAD_REQUEST', { code: 'ADULTS_ONLY', message: 'Kataki online is for people aged 18 or older.' })
          },
        },
      },
    },
    session: { expiresIn: 30 * DAY, updateAge: DAY, freshAge: 600 },
    rateLimit: {
      storage: 'database', // on in production; shared by every gateway process
      // slowed, never locked: a lockout is something an attacker can do to someone else
      customRules: {
        '/sign-in/email': { window: 60, max: 5 },
        '/sign-up/email': { window: 300, max: 5 },
        '/sign-in/magic-link': { window: 300, max: 3 },
        '/request-password-reset': { window: 300, max: 3 },
        '/send-verification-email': { window: 300, max: 3 },
      },
    },
    advanced: {
      // a user's id is their library id: lowercase, so it passes the engine's folder-name rule
      database: { generateId: () => randomUUID() },
    },
    plugins: [
      haveIBeenPwned({ enabled: pwned }),
      magicLink({
        expiresIn: 10 * 60,
        storeToken: 'hashed',
        disableSignUp: true, // an account is made on the sign-up form, where 18 or older is said
        // The mail links to the app's own page, whose button makes the request that uses the
        // token up: a mail scanner that opens the link burns nothing. Only an account gets one.
        sendMagicLink: async ({ email, token }, ctx) => {
          if (!(await ctx?.context.internalAdapter.findUserByEmail(email))) return
          void send(email, 'Your sign-in link for Kataki', `Open this link to sign in to Kataki:\n\n${origin}/app/?magic=${token}\n\nIt works once, for 10 minutes. If you did not ask for this, ignore it.`)
        },
      }),
    ],
  })
}

export type Auth = ReturnType<typeof makeAuth>

/** Create or bring up to date the tables Better Auth owns. */
export async function migrateAuth(auth: Auth): Promise<void> {
  await (await getMigrations(auth.options)).runMigrations()
}
