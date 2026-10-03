// What was spent (design brief 3 T5; docs/specs/2026-10-02-kataki-online.md G7): the last 30
// days by day (the gateway's ledger), what each story cost (the library's own log), and when
// credit was added. The full ledger downloads with the account's data.
import { api } from '../../api'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { setPref, usePrefs } from '../../prefs'
import { t } from '../../strings'

type Usage = { days: { day: string; replies: number; calls: number; storage: number }[]; added: { micros: number; reason: string; at: string }[] }
type ByStory = { stories: { story_id: number; title: string; calls: number; cost: number }[] }

const usd = (dollars: number) => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: dollars && dollars < 0.01 ? 4 : 2 }).format(dollars)
const CAPS = [0, 5, 10, 20, 50, 100] // dollars a month; 0 is no limit (T7)
const date = (iso: string) => new Date(iso.length === 10 ? `${iso}T12:00:00Z` : iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })

export default function Spending() {
  const [usage] = useLoad(() => api<Usage>('/api/usage'), [])
  const [byStory] = useLoad(() => api<ByStory>('/spend'), [])
  const [prefs] = usePrefs()
  const cap = Number(prefs['spend.monthly_cap']) || 0
  const capWord = (c: number) => (c ? t('sp.capOf', { amount: usd(c) }) : t('sp.noCap'))
  if (!usage) return null
  const spent = (d: Usage['days'][number]) => (d.replies + d.storage) / 1e6
  const total = usage.days.reduce((s, d) => s + spent(d), 0)
  const most = Math.max(...usage.days.map(spent), 0)
  const stories = byStory?.stories.filter((s) => s.cost > 0).slice(0, 5) ?? []
  return (
    <K.SettingsSection title={t('sp.title')} note={t('sp.note')}>
      <K.SettingsRow title={t('sp.month')} description={t('sp.monthSub', { calls: usage.days.reduce((s, d) => s + d.calls, 0) })}><b>{usd(total)}</b></K.SettingsRow>
      <K.SettingsRow title={t('sp.cap')} description={t('sp.capSub')}>
        <div style={{ width: 160 }}>
          <K.Select label="" options={CAPS.map(capWord)} value={capWord(CAPS.includes(cap) ? cap : 0)} onChange={(v) => setPref('spend.monthly_cap', CAPS.find((c) => capWord(c) === v) || 'none')} />
        </div>
      </K.SettingsRow>
      {usage.days.length > 0 && (
        <div className="spend">
          {usage.days.slice(0, 14).map((d) => (
            <K.Meter key={d.day} label={date(d.day) + (d.storage ? ` · ${t('sp.storage')}` : '')} word={usd(spent(d))} value={most ? (spent(d) / most) * 100 : 0} tone="accent" />
          ))}
        </div>
      )}
      {stories.length > 0 && (
        <div className="spend">
          <b>{t('sp.byStory')}</b>
          {stories.map((s) => <K.ListRow key={s.story_id} story title={s.title} subtitle={t('sp.calls', { calls: s.calls })} meta={usd(s.cost)} href={`${import.meta.env.BASE_URL}story/${s.story_id}`} />)}
        </div>
      )}
      {usage.added.length > 0 && (
        <div className="spend">
          <b>{t('sp.added')}</b>
          {usage.added.slice(0, 5).map((a) => <K.ListRow key={a.at} icon="plus" title={t(`sp.r.${a.reason as 'starter' | 'topup' | 'refund' | 'adjust'}`)} subtitle={date(a.at)} meta={usd(a.micros / 1e6)} />)}
        </div>
      )}
    </K.SettingsSection>
  )
}
