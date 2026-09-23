// A reply types itself out at a reading pace, whatever speed the model streams it at: a hosted
// model can send a whole paragraph in a blink, which is too fast to follow.

/** Characters per second for each "Reading speed" (Settings → Chat). Instant: as it arrives. */
export const SPEEDS = { slow: 25, normal: 45, fast: 90, instant: Infinity } as const
export type Speed = keyof typeof SPEEDS

const TICK = 40 // ms between steps: smooth enough to read as typing

/** Queue text with `push`; it reaches `show` at `cps` characters a second. `drain` resolves once
 *  everything queued is out, and `flush` shows the rest at once (Stop). */
export function pacer(show: (text: string) => void, cps: number) {
  let queue = ''
  let owed = 0
  let timer: ReturnType<typeof setInterval> | undefined
  const waiting: (() => void)[] = []
  const settle = () => {
    clearInterval(timer)
    timer = undefined
    owed = 0
    waiting.splice(0).forEach((resolve) => resolve())
  }
  const tick = () => {
    owed += (cps * TICK) / 1000
    const n = Math.floor(owed)
    if (n > 0) {
      owed -= n
      show(queue.slice(0, n))
      queue = queue.slice(n)
    }
    if (!queue) settle()
  }
  return {
    push(text: string) {
      if (!Number.isFinite(cps)) return show(text)
      queue += text
      timer ??= setInterval(tick, TICK)
    },
    drain: () => new Promise<void>((resolve) => (queue ? waiting.push(resolve) : resolve())),
    flush() {
      if (queue) show(queue)
      queue = ''
      settle()
    },
  }
}
