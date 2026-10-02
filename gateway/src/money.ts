// What one model call costs, in whole micro-dollars: the engine's `usage.micros`, to the digit
// (docs/specs/2026-10-02-kataki-online.md §3). Exact decimal arithmetic on BigInt, rounded
// half-up once. Held to engine/tests/gateway_vectors.json by money.test.ts.

export type Prices = Record<string, Record<string, unknown>>
export type Tokens = { model: string; role: string; prompt_tokens?: number | null; cached_tokens?: number | null; completion_tokens?: number | null }

/** A price as an exact decimal: digits and how many of them sit after the point. */
function decimal(x: unknown): { n: bigint; scale: number } {
  if (typeof x !== 'number' || !Number.isFinite(x) || x < 0) throw new Error('not a price')
  const m = /^(\d+)(?:\.(\d+))?(?:e([+-]\d+))?$/.exec(String(x))
  if (!m) throw new Error('not a price')
  const [, whole, frac = '', exp = '0'] = m
  const scale = frac.length - Number(exp)
  return scale >= 0 ? { n: BigInt(whole + frac), scale } : { n: BigInt(whole + frac) * 10n ** BigInt(-scale), scale: 0 }
}

const count = (x: number | null | undefined): bigint => {
  if (x != null && (!Number.isInteger(x) || x < 0)) throw new Error('not a count')
  return BigInt(x ?? 0)
}

/** Micro-dollars for one call ($ per million tokens is micro-dollars per token), or null when
 *  its model has no usable price. A malformed entry prices nothing. */
export function micros(prices: Prices, row: Tokens): bigint | null {
  try {
    const p = prices[row.model]
    if (!p) return null
    const prompt = count(row.prompt_tokens)
    let parts: [bigint, { n: bigint; scale: number }][]
    if (row.role === 'voice') {
      parts = [[prompt, decimal(p.char)]]
    } else {
      const input = decimal(p.input)
      const cachedRate = 'cached' in p ? decimal(p.cached) : input
      const output = row.role === 'embed' && !('output' in p) ? decimal(0) : decimal(p.output) // embeddings write none
      const cached = count(row.cached_tokens) < prompt ? count(row.cached_tokens) : prompt
      parts = [[prompt - cached, input], [cached, cachedRate], [count(row.completion_tokens), output]]
    }
    const scale = Math.max(...parts.map(([, d]) => d.scale))
    const spent = parts.reduce((sum, [tokens, d]) => sum + tokens * d.n * 10n ** BigInt(scale - d.scale), 0n)
    const one = 10n ** BigInt(scale)
    return (spent * 2n + one) / (2n * one) // half-up, and nothing here is negative
  } catch {
    return null
  }
}
