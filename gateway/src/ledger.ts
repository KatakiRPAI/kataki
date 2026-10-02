// The ledger: what each account was given and what it used, in whole micro-dollars
// (docs/specs/2026-10-02-kataki-online.md §3; the engine's side is minds spec §8.4).
import type { Pool } from 'pg'
import { micros, type Prices } from './money.ts'
import { USER } from './sign.ts'

export async function balance(pool: Pool, user: string): Promise<bigint> {
  const { rows } = await pool.query(
    'SELECT (SELECT coalesce(sum(micros), 0) FROM credit WHERE user_id = $1) - (SELECT coalesce(sum(micros), 0) FROM usage WHERE user_id = $1) AS micros',
    [user],
  )
  return BigInt(rows[0].micros)
}

/** Give credit once per `ref`. True when this call was the one that gave it. */
export async function grant(pool: Pool, user: string, amount: bigint, reason: 'starter' | 'topup' | 'refund' | 'adjust', ref: string): Promise<boolean> {
  const r = await pool.query('INSERT INTO credit(user_id, micros, reason, ref) VALUES($1, $2, $3, $4) ON CONFLICT (ref) DO NOTHING', [user, amount.toString(), reason, ref])
  return r.rowCount === 1
}

/** `GET /allow`: can this balance cover a call of about `estimate` dollars? */
export async function allow(pool: Pool, user: string, estimate: number): Promise<boolean> {
  if (!USER.test(user) || !Number.isFinite(estimate) || estimate < 0) return false
  return (await balance(pool, user)) >= BigInt(Math.round(estimate * 1e6))
}

const whole = (x: unknown): x is number => Number.isInteger(x) && (x as number) >= 0

/** `POST /usage`: bill one model call. 200 billed, 409 already billed, 422 not a row we can bill. */
export async function bill(pool: Pool, prices: Prices, row: Record<string, unknown>): Promise<200 | 409 | 422> {
  const { user, usage_id, role, model, prompt_tokens, cached_tokens, completion_tokens, estimated, at } = row
  if (typeof user !== 'string' || !USER.test(user) || typeof usage_id !== 'string' || !/^[0-9a-f]{8,64}$/.test(usage_id)) return 422
  if (typeof role !== 'string' || typeof model !== 'string' || !whole(prompt_tokens) || !whole(cached_tokens) || !whole(completion_tokens)) return 422
  const cost = micros(prices, { model, role, prompt_tokens, cached_tokens, completion_tokens })
  if (cost === null) return 422 // a model the service does not price is never called (§8.4): this row is not ours
  // the engine's clock, UTC ("2026-10-02 10:57:33"); a row resent later is still billed to its day
  const used = typeof at === 'string' && !Number.isNaN(Date.parse(`${at.replace(' ', 'T')}Z`)) ? new Date(`${at.replace(' ', 'T')}Z`) : new Date()
  const r = await pool.query(
    'INSERT INTO usage(usage_id, user_id, micros, role, model, prompt_tokens, cached_tokens, completion_tokens, estimated, used_at) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) ON CONFLICT (usage_id) DO NOTHING',
    [usage_id, user, cost.toString(), role, model, prompt_tokens, cached_tokens, completion_tokens, estimated === true, used],
  )
  return r.rowCount === 1 ? 200 : 409
}
