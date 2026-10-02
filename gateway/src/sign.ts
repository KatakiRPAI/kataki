// The gateway's signature on one request to the engine (minds spec §8.4; the engine's
// `hosted.sign`). `target` is the path and query as sent, with the `?` always there.
import { createHmac } from 'node:crypto'

/** What the engine accepts as a user id: it names that user's library folder. */
export const USER = /^(?!(?:con|prn|aux|nul|com[1-9]|lpt[1-9])$)[a-z0-9_-]{1,64}$/

export const sign = (secret: string, user: string, channel: string, at: number, method: string, target: string): string =>
  createHmac('sha256', secret).update(`${user}\n${channel}\n${at}\n${method}\n${target}`).digest('hex')

/** The headers that tell the engine who is asking, for this one request line. */
export function signed(secret: string, user: string, channel: string, method: string, url: string, now = Date.now()): Record<string, string> {
  const at = Math.floor(now / 1000)
  const cut = url.indexOf('?')
  const target = cut < 0 ? `${url}?` : `${url.slice(0, cut)}?${url.slice(cut + 1)}`
  return { 'x-kataki-user': user, 'x-kataki-channel': channel, 'x-kataki-time': String(at), 'x-kataki-sig': sign(secret, user, channel, at, method, target) }
}
