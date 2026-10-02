// Badges on the profile card (docs/specs/2026-10-02-profiles-and-accounts.md P3). The engine
// awards them from what the library holds; here they are shown, hidden one by one, or all off.
import { useState } from 'react'
import { api } from '../api'
import { K } from '../ds'
import { useLoad } from '../hooks'
import { Overlay, toast } from '../overlay'
import { pref, setPref } from '../prefs'
import { t, type Key } from '../strings'

type Badge = { key: string; group: string; target: number; progress: number; earned_at: string | null; backdated: boolean }
type Check = { badges: Badge[]; new: string[] }
export type BadgePrefs = { off?: boolean; hidden?: string[] }

const mine = (): BadgePrefs => pref<{ badges?: BadgePrefs }>('profile', {}).badges ?? {}
const name = (key: string) => t(`bd.${key}` as Key)

/** Look for badges earned since the last look, and say so once: one toast, however many. */
export async function checkBadges(): Promise<Check | undefined> {
  if (mine().off) return
  const got = await api<Check>('/achievements/check', 'POST')
  if (got.new.length) toast(t('bd.new', { n: got.new.length, name: name(got.new[0]) }), { icon: 'star' }, 8000)
  return got
}

export default function Badges() {
  const [got] = useLoad(checkBadges, [])
  const [all, setAll] = useState(false)
  const { hidden = [] } = mine()
  if (!got) return null
  const earned = got.badges.filter((b) => b.earned_at)
  const shown = earned.filter((b) => !hidden.includes(b.key))
  const hide = (key: string, on: boolean) => setPref('profile', { ...pref('profile', {}), badges: { ...mine(), hidden: on ? [...hidden, key] : hidden.filter((k) => k !== key) } })
  return (
    <div className="pc__badges">
      {shown.map((b) => <span key={b.key} title={t(`bd.${b.key}.how` as Key)}><K.Tag tone="warm">{name(b.key)}</K.Tag></span>)}
      <K.Button size="sm" variant="link" onClick={() => setAll(true)}>{t('bd.all', { n: earned.length, of: got.badges.length })}</K.Button>
      {all && (
        <Overlay onClose={() => setAll(false)}>
          <K.Dialog size="lg" icon="star" title={t('bd.title')} description={t('bd.body')} onClose={() => setAll(false)}
            actions={[<K.Button key="d" variant="primary" onClick={() => setAll(false)}>{t('bk.done')}</K.Button>]}>
            <K.Panel flush style={{ maxHeight: '50vh', overflowY: 'auto', scrollbarWidth: 'thin', scrollbarColor: 'var(--border) transparent' }}>
              {got.badges.map((b) => (
                <div key={b.key} className="ch-row" style={{ padding: '10px 14px', gap: 14 }}>
                  <div className="col" style={{ flex: 1, gap: 2, minWidth: 0 }}>
                    <b style={{ fontSize: 13.5 }}>{name(b.key)}</b>
                    <span className="t-meta">{t(`bd.${b.key}.how` as Key)}</span>
                  </div>
                  {b.earned_at ? (
                    <>
                      <K.StatePill tone="ok" icon="check">{new Date(`${b.earned_at.replace(' ', 'T')}Z`).toLocaleDateString()}</K.StatePill>
                      <K.Button size="sm" variant="ghost" onClick={() => hide(b.key, !hidden.includes(b.key))}>{t(hidden.includes(b.key) ? 'bd.show' : 'bd.hide')}</K.Button>
                    </>
                  ) : <span className="t-meta">{t('bd.progress', { n: b.progress, of: b.target })}</span>}
                </div>
              ))}
            </K.Panel>
          </K.Dialog>
        </Overlay>
      )}
    </div>
  )
}
