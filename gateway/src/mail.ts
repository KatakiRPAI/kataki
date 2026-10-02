// Mail (docs/specs/2026-10-02-kataki-online.md §2): the one way the gateway sends anything.
// Printed in development; sent through Resend's HTTP API once RESEND_API_KEY is set
// (docs/decisions.md: another provider is another `send` here, nothing else changes).
import type { Send } from './auth.ts'

export const printed: Send = (to, subject, text) => console.log(`\n--- mail to ${to}: ${subject}\n${text}\n---`)

export function mailer(env: Record<string, string | undefined>, post: typeof fetch = fetch): Send {
  const key = env.RESEND_API_KEY
  if (!key) return printed
  const from = env.KATAKI_MAIL_FROM
  if (!from) throw new Error('RESEND_API_KEY is set but KATAKI_MAIL_FROM (e.g. "Kataki <hello@your-domain>") is not')
  return async (to, subject, text) => {
    // a mail that fails is logged by its status only: never its address or what it said
    try {
      const r = await post('https://api.resend.com/emails', {
        method: 'POST',
        headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ from, to: [to], subject, text }),
        signal: AbortSignal.timeout(10_000),
      })
      if (!r.ok) console.error(`gateway: a mail was not sent (${r.status})`)
    } catch (e) {
      console.error('gateway: a mail was not sent:', e instanceof Error ? e.name : e)
    }
  }
}
