// Adding credit (docs/specs/2026-10-02-kataki-online.md G7; design brief 3 T2, T3).
//
// A top-up opens a checkout for one of a few amounts and sends the person to the processor's
// hosted page; the processor tells us it was paid, and the credit is granted once. Which
// processor is the owner's to choose (docs/decisions.md); until then the `test` processor is a
// page of our own, on only when KATAKI_PAYMENTS=test, that pays without money.
import { randomBytes } from 'node:crypto'
import type { Pool } from 'pg'
import { grant } from './ledger.ts'

export const AMOUNTS = [5, 10, 20, 50] // dollars
export type Payments = { processor: 'test' }
export type TopupConfig = { pool: Pool; origin: string; payments: Payments }
export type Checkout = { id: string; dollars: number; status: 'open' | 'paid' | 'cancelled' }

/** Open a checkout and say where to pay it. Null: not one of the amounts. */
export async function startTopup(c: TopupConfig, user: string, dollars: unknown): Promise<{ id: string; url: string } | null> {
  if (typeof dollars !== 'number' || !AMOUNTS.includes(dollars)) return null
  const id = randomBytes(12).toString('hex')
  await c.pool.query("INSERT INTO checkout(id, user_id, micros, processor, status) VALUES($1, $2, $3, $4, 'open')", [id, user, (BigInt(dollars) * 1_000_000n).toString(), c.payments.processor])
  return { id, url: `${c.origin}/test-checkout/${id}` }
}

/** The processor says it was paid: grant the credit, once, however often it says so. */
export async function settle(c: TopupConfig, id: string, ref: string): Promise<boolean> {
  const { rows } = await c.pool.query("UPDATE checkout SET status = 'paid', ref = $2, settled_at = now() WHERE id = $1 AND status = 'open' RETURNING user_id, micros", [id, ref])
  if (!rows[0]) return false
  return grant(c.pool, rows[0].user_id, BigInt(rows[0].micros), 'topup', `topup:${id}`)
}

export async function cancel(c: TopupConfig, id: string): Promise<void> {
  await c.pool.query("UPDATE checkout SET status = 'cancelled', settled_at = now() WHERE id = $1 AND status = 'open'", [id])
}

/** A checkout as its owner may see it (null: not theirs, or no such checkout). */
export async function checkoutOf(c: TopupConfig, user: string | null, id: string): Promise<Checkout | null> {
  const { rows } = await c.pool.query('SELECT id, user_id, micros, status FROM checkout WHERE id = $1', [id])
  const row = rows[0]
  if (!row || (user !== null && row.user_id !== user)) return null
  return { id: row.id, dollars: Number(row.micros) / 1e6, status: row.status }
}

const page = (title: string, body: string) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${title}</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0b1230;color:#e9eeff;font:16px/1.5 system-ui,sans-serif}main{width:min(360px,calc(100vw - 32px));display:flex;flex-direction:column;gap:14px}
button{font:inherit;color:inherit;border-radius:12px;border:1px solid #2b3766;background:#131c44;padding:12px;width:100%;cursor:pointer}button.pay{background:#3d5bf0;border-color:#3d5bf0;font-weight:600}p{margin:0;color:#9aa6d8}</style></head><body><main>${body}</main></body></html>`

/** The test processor's hosted page: what a real one draws, minus the card. */
export function testCheckoutPage(checkout: Checkout): string {
  if (checkout.status !== 'open') return page('Checkout', `<h1>This checkout is ${checkout.status}</h1><form method="get" action="/app/settings/account"><button>Back to Kataki</button></form>`)
  return page('Test checkout', `<h1>Test checkout</h1><p>Add $${checkout.dollars} of credit to your Kataki account. This is the test processor: no money moves.</p>
<form method="post" action="/test-checkout/${checkout.id}/pay"><button class="pay">Pay $${checkout.dollars} (test)</button></form>
<form method="post" action="/test-checkout/${checkout.id}/cancel"><button>Cancel</button></form>`)
}
