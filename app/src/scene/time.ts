import { t } from '../strings'

const UNITS: [number, string][] = [[525_600, 'year'], [43_200, 'month'], [10_080, 'week'], [1_440, 'day'], [60, 'hour'], [1, 'minute']]

/** "Six years later", "An hour later": a skip in the story's own words. */
export function later(minutes: number): string {
  const [size, unit] = UNITS.find(([s]) => minutes >= s) ?? UNITS[UNITS.length - 1]
  return t('time.later', { unit, n: Math.max(1, Math.round(minutes / size)) })
}
