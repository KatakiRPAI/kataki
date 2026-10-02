// Accounts: Better Auth on the gateway's Postgres, set as docs/specs/2026-10-02-kataki-online.md
// §2 says and why. G1 is email and password; later slices add to this one place.
import { randomUUID } from 'node:crypto'
import { betterAuth } from 'better-auth'
import { APIError, createAuthMiddleware, getOAuthState, isAPIError } from 'better-auth/api'
import { getMigrations } from 'better-auth/db/migration'
import { genericOAuth, haveIBeenPwned, magicLink, twoFactor, type GenericOAuthConfig } from 'better-auth/plugins'
import type { Pool } from 'pg'

export type Send = (to: string, subject: string, text: string) => void | Promise<void>
export type AuthConfig = {
  pool: Pool
  origin: string // where the gateway is reached, e.g. https://app.kataki.example
  secret: string
  send: Send
  pwned?: boolean // refuse breached passwords (asks api.pwnedpasswords.com); tests turn it off
  social?: Social // the providers the owner has registered an app with; none by default
  others?: GenericOAuthConfig[] // any other OAuth service, by its endpoints (the tests' stand-in for GitHub)
}

// Sign in with another service (spec §2, G3). Apple is not here yet: it needs a signed client
// secret and a form-post callback.
export const PROVIDERS = ['google', 'github', 'discord'] as const
export type Provider = (typeof PROVIDERS)[number]
export type Social = Partial<Record<Provider, { clientId: string; clientSecret: string }>>

/** The providers whose keys are in the environment: GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET, and so on. */
export function socialFrom(env: Record<string, string | undefined>): Social {
  const found: Social = {}
  for (const p of PROVIDERS) {
    const clientId = env[`${p.toUpperCase()}_CLIENT_ID`]
    const clientSecret = env[`${p.toUpperCase()}_CLIENT_SECRET`]
    if (clientId && clientSecret) found[p] = { clientId, clientSecret }
  }
  return found
}

const DAY = 86_400

/** Two-step sign-in (spec §2, G4): an authenticator app's code, with ten backup codes.
 *
 *  The library asks for the second step only after a password. A sign-in link or another
 *  service would walk straight past it, so its own hook is pointed at those routes too: the
 *  session they made is taken back, and the browser goes to the app's code screen instead. */
function secondStep(origin: string) {
  const plugin = twoFactor({ issuer: 'Kataki', backupCodeOptions: { amount: 10, storeBackupCodes: 'encrypted' } })
  const hook = plugin.hooks.after[0]
  const afterPassword = hook.matcher
  const ask = hook.handler
  const byRedirect = (path?: string) => path === '/magic-link/verify' || path === '/callback/:id'
  hook.matcher = (c) => afterPassword(c) || byRedirect(c.path)
  // ponytail: leans on the library's hook shape ({response, headers}); the version is pinned and
  // app.test.ts walks this path, so an upgrade that changes it fails there, not in production
  type Said = { response?: unknown; headers?: Headers } | undefined
  hook.handler = (async (ctx: { path?: string }) => {
    const said = await (ask as unknown as (c: unknown) => Promise<Said>)(ctx)
    if (said?.response === undefined || !byRedirect(ctx.path)) return said
    // those routes answer with a redirect, not JSON: the browser goes to the code screen,
    // with the cookie the library just set for the pending second step
    const headers = new Headers(said.headers)
    headers.set('location', `${origin}/app/?step=2`)
    return { response: new APIError('FOUND', undefined, headers), headers }
  }) as unknown as typeof ask
  return plugin
}

export function makeAuth({ pool, origin, secret, send, pwned = true, social = {}, others = [] }: AuthConfig) {
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
        void send(user.email, 'Confirm your email for Kataki', `Open this link to confirm this address for your Kataki account:\n\n${url}\n\nIt works for one hour. If you did not ask for this, ignore it.`)
      },
    },
    // 18 or older, said at sign-up and kept on the account with the time it was made
    // not "required": the library checks that before the hook below can fill it in from another service's sign-up
    user: {
      additionalFields: { adult: { type: 'boolean', required: false, input: true } },
      // a new address is asked for from a signed-in account, approved from the old address,
      // then confirmed from the new one: neither a stolen session nor a typo moves the account
      changeEmail: {
        enabled: true,
        sendChangeEmailConfirmation: async ({ user, newEmail, url }) => {
          void send(user.email, 'Approve changing your Kataki email', `Your Kataki account was asked to change its email to ${newEmail}.\n\nIf that was you, open this link to approve it:\n\n${url}\n\nIf it was not you, do not open it, and change your password at ${origin}/app/.`)
        },
      },
    },
    hooks: {
      // a changed password is told to the account's owner, as a reset is
      after: createAuthMiddleware(async (ctx) => {
        const who = ctx.context.session?.user
        if (ctx.path !== '/change-password' || !who || isAPIError(ctx.context.returned)) return
        void send(who.email, 'Your Kataki password was changed', `The password for your Kataki account was just changed.\n\nIf this was not you, reset it now at ${origin}/app/ and check who else can read this mailbox.`)
      }),
    },
    databaseHooks: {
      user: {
        create: {
          // said on the sign-up form; with another service, said on our page before leaving
          // for theirs and carried through the redirect
          before: async (user) => {
            const said = user.adult === true || (await getOAuthState<{ adult?: boolean }>().catch(() => null))?.adult === true
            if (!said) throw new APIError('BAD_REQUEST', { code: 'ADULTS_ONLY', message: 'Kataki online is for people aged 18 or older.' })
            return { data: { ...user, adult: true } }
          },
        },
      },
    },
    // "Sign in with" never makes an account by itself: that is "Create account", where 18 or
    // older is said first
    socialProviders: Object.fromEntries(Object.entries(social).map(([name, keys]) => [name, { ...keys, disableImplicitSignUp: true }])),
    account: {
      accountLinking: {
        enabled: true,
        // a sign-in joins an existing account only when the service vouches for the address;
        // Discord's is never trusted for that (research §7)
        trustedProviders: ['google', 'github'],
        allowDifferentEmails: false,
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
      secondStep(origin),
      ...(others.length ? [genericOAuth({ config: others.map((o) => ({ ...o, disableImplicitSignUp: true })) })] : []),
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
