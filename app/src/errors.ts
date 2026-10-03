// The error catalogue (ERRORS.md, errors.json): every error the app shows comes from here, by
// code, with its own words. "Import it; don't retype it."
import catalogue from './strings/errors.en.json' with { type: 'json' }

export type Code = (typeof catalogue)[number]['code']
export type Shown = { code: Code; title: string; body: string; actions: string[]; surface: string }
const byCode = new Map(catalogue.map((e) => [e.code, e]))

/** The catalogue's words with the facts filled in; a fact we don't know reads as a plain word. */
const fill = (text: string, facts: Record<string, string | number>) =>
  text.replace(/\{(\w+)\}/g, (_, k: string) => String(facts[k] ?? FALLBACK[k] ?? '…'))
const FALLBACK: Record<string, string> = { name: 'The reply', server: 'The model', address: 'its address', provider: 'The service', seconds: 'a few', time: 'just now', ago: 'just now', where: '' }

export function err(code: Code, facts: Record<string, string | number> = {}): Shown {
  const e = byCode.get(code) ?? byCode.get('UNKNOWN')!
  return { code: e.code as Code, title: fill(e.title, facts), body: fill(e.body, facts).replace(/\s+/g, ' ').trim(), actions: e.actions.map((a) => fill(a, facts)), surface: e.surface }
}

/** Which catalogue entry an engine or network failure is, from what it said. `online`: the model is
 *  a service elsewhere; `testing`: Settings is testing a connection, not waiting on a reply. */
export function classify(message: string, online = false, testing = false): Code {
  if (message === 'NO_CREDIT' || message === 'DAILY_CAP' || message === 'SPEND_CAP') return message // Kataki online's own refusals, by code
  const m = message.toLowerCase()
  if (online && typeof navigator !== 'undefined' && navigator.onLine === false) return 'OFFLINE'
  if (/\b401\b|unauthori[sz]ed|invalid.*key|key.*invalid/.test(m)) return online ? 'API_KEY_INVALID' : 'SERVER_UNAUTHORIZED'
  if (/\b402\b|credit|quota|insufficient/.test(m)) return 'API_NO_CREDIT'
  if (/context.?(length|window|size)|n_ctx|maximum context|exceeds? the context/.test(m)) return 'CONTEXT_TOO_SMALL'
  if (/\b429\b|rate.?limit|too many requests/.test(m)) return 'API_RATE_LIMITED'
  if (/model[^.]*(not found|does not exist|not available)|no such model|model_not_found/.test(m)) return online ? 'API_MODEL_NOT_FOUND' : 'MODEL_GONE'
  // "refused" alone is a closed port (ECONNREFUSED), not the model saying no
  if (/content.?policy|safety|refused to (answer|continue|respond)|refusal/.test(m)) return 'API_REFUSED'
  if (/timed? ?out|timeout/.test(m)) return testing ? 'SERVER_TIMEOUT' : 'REPLY_TIMEOUT'
  if (/empty/.test(m)) return 'REPLY_EMPTY'
  if (/cut|max_tokens|length limit|finish.*length/.test(m)) return 'REPLY_CUT_OFF'
  if (/no model is set|not set up|no model/.test(m)) return 'MODEL_GONE'
  if (/connect|reach|refused|unreachable|econn|network|fetch|502|503|504/.test(m)) return online ? 'API_UNREACHABLE' : 'REPLY_UNREACHABLE'
  return 'UNKNOWN'
}
