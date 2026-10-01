// The model picker: one field that opens a dialog to search, file, filter and sort every model the
// connections list. Used wherever a model is chosen (Settings › Models, the character editor,
// first run). What each row says comes from the engine (`ModelInfo`); nothing is guessed here.
import { useEffect, useId, useMemo, useState, type KeyboardEvent, type ReactNode } from 'react'
import { api, type ModelInfo, type Provider } from '../api'
import { K } from '../ds'
import { useLoad } from '../hooks'
import { Overlay } from '../overlay'
import { relative, t, type Key } from '../strings'

export type Picked = { provider_id: number; model: string }
export type Job = 'rp' | 'narrator' | 'utility' | 'reasoning' | 'embed'
type Row = ModelInfo & { provider: Provider; local: boolean; hay: string }
type Kind = Exclude<ModelInfo['kinds'][number], 'chat'>

const KINDS: Kind[] = ['roleplay', 'reasoning', 'small', 'vision', 'image', 'voice', 'embedding']
const MOST = 200 // ponytail: rows drawn at once; past it the search narrows. Virtualize if a list this long must scroll whole.
const local = (url: string) => /^https?:\/\/(localhost|127\.|\[::1\]|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(url)
const price = (m: Row) => (m.local ? 0 : m.input !== undefined && m.output !== undefined ? m.input + m.output : Number.MAX_VALUE)
const SORTS: Record<string, (a: Row, b: Row) => number> = {
  listed: () => 0,
  name: (a, b) => a.id.localeCompare(b.id),
  size: (a, b) => (b.params_b ?? -1) - (a.params_b ?? -1),
  price: (a, b) => price(a) - price(b),
  context: (a, b) => (b.context ?? -1) - (a.context ?? -1),
  recent: (a, b) => (b.last_used ?? '').localeCompare(a.last_used ?? ''),
}
const size = (b: number) => (b >= 1000 ? `${+(b / 1000).toFixed(1)}T` : b >= 1 ? `${+b.toFixed(1)}B` : `${Math.round(b * 1000)}M`)
const tokens = (n: number) => (n >= 1e6 ? `${+(n / 1e6).toFixed(1)}M` : `${Math.round(n / (n % 1024 ? 1000 : 1024))}k`)
const dollars = (n: number) => String(+n.toFixed(3))

/** A field showing the chosen model; pressing it opens the picker. `providers`: which connections
 *  to list (all of them when left out). `job`: what the model is for, so "Fits" can filter.
 *  `none`: the words for "no choice" (the default), which then is a row of its own. */
export function ModelPicker({ label, hint, value, onChange, providers, job, none }: {
  label: string; hint?: string; value: Picked | null; onChange: (v: Picked | null) => void; providers?: Provider[]; job?: Job; none?: string
}) {
  const id = useId()
  const [open, setOpen] = useState(false)
  const shown = value?.model ?? none ?? t('mp.choose')
  return (
    <>
      <K.Field label={label} hint={hint} htmlFor={id}>
        <button id={id} type="button" className="k-select mp-field" aria-haspopup="dialog" aria-label={`${label}: ${shown}`} onClick={() => setOpen(true)}>
          <span className="mp-field__v">{shown}</span>
          <K.Icon name="down" size={15} stroke={2} />
        </button>
      </K.Field>
      {open && <Picker title={label} value={value} providers={providers} job={job} none={none} onClose={() => setOpen(false)} onPick={(v) => { onChange(v); setOpen(false) }} />}
    </>
  )
}

function Picker({ title, value, providers, job, none, onPick, onClose }: {
  title: string; value: Picked | null; providers?: Provider[]; job?: Job; none?: string; onPick: (v: Picked | null) => void; onClose: () => void
}) {
  const uid = useId()
  const [rows] = useLoad(async () => {
    const from = providers ?? await api<Provider[]>('/providers')
    const lists = await Promise.all(from.map((p) => api<{ info: ModelInfo[] }>(`/providers/${p.id}/models`).then(
      (r) => r.info.map((m): Row => ({ ...m, provider: p, local: local(p.base_url), hay: `${m.id} ${m.name ?? ''} ${p.name} ${(m.hosts ?? []).join(' ')}`.toLowerCase() })),
      () => [] as Row[], // a connection that isn't answering lists nothing
    )))
    return lists.flat()
  }, [])
  const [q, setQ] = useState('')
  const [kind, setKind] = useState<Kind>()
  const [fits, setFits] = useState(!!job)
  const [where, setWhere] = useState<'local' | 'online'>()
  const [pid, setPid] = useState<number>()
  const [sort, setSort] = useState('listed')
  const [active, setActive] = useState(0)
  useEffect(() => setActive(0), [q, kind, fits, where, pid, sort])

  const { counts, found } = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean)
    const base = (rows ?? []).filter((m) => (!fits || m.kinds.includes(job === 'embed' ? 'embedding' : 'chat')) && (!where || m.local === (where === 'local'))
      && (pid === undefined || m.provider.id === pid) && words.every((w) => m.hay.includes(w)))
    const counts = Object.fromEntries(KINDS.map((k) => [k, base.filter((m) => m.kinds.includes(k)).length])) as Record<Kind, number>
    return { counts: { ...counts, all: base.length }, found: (kind ? base.filter((m) => m.kinds.includes(kind)) : base).sort(SORTS[sort]) }
  }, [rows, q, kind, fits, where, pid, sort, job])

  const is = (m: Row) => value?.provider_id === m.provider.id && value.model === m.id
  // what Enter and the arrows walk: the default (if there is one), a choice no connection lists now, then the list
  const gone = rows && value && !rows.some(is) ? value : null
  const shown = found.slice(0, MOST)
  const entries: (Row | 'none' | 'gone')[] = [...(none ? ['none' as const] : []), ...(gone ? ['gone' as const] : []), ...shown]
  const pick = (e: Row | 'none' | 'gone' | undefined) => { if (e) onPick(e === 'none' ? null : e === 'gone' ? gone : { provider_id: e.provider.id, model: e.id }) }
  useEffect(() => { document.getElementById(`${uid}-${active}`)?.scrollIntoView({ block: 'nearest' }) }, [uid, active])
  const keys = (e: KeyboardEvent) => {
    const el = e.target as HTMLElement
    if (el.tagName !== 'INPUT' && el.getAttribute('role') !== 'listbox') return // chips and the sort keep their own keys
    const to = { ArrowDown: active + 1, ArrowUp: active - 1, PageDown: active + 8, PageUp: active - 8, Home: 0, End: entries.length - 1 }[e.key]
    if (to !== undefined && !(el.tagName === 'INPUT' && (e.key === 'Home' || e.key === 'End'))) { e.preventDefault(); setActive(Math.max(0, Math.min(entries.length - 1, to))) }
    if (e.key === 'Enter') { e.preventDefault(); pick(entries[active]) }
  }

  const all = rows ?? []
  const conns = [...new Map(all.map((m) => [m.provider.id, m.provider])).values()]
  const mixed = all.some((m) => m.local) && all.some((m) => !m.local)
  const sorts = Object.keys(SORTS).map((s) => [s, t(`mp.sort.${s}` as Key)])
  const option = (i: number, chosen: boolean, name: string, tags: ReactNode, e: Row | 'none' | 'gone') => (
    <div key={i} id={`${uid}-${i}`} role="option" aria-selected={chosen} className={`mp-row${i === active ? ' is-active' : ''}`} onClick={() => pick(e)} onMouseMove={() => setActive(i)}>
      <span className="mp-row__id">{name}</span>
      {chosen && <K.Icon name="check" size={15} stroke={2.4} />}
      <span className="mp-row__tags">{tags}</span>
    </div>
  )
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="cpu" size="lg" title={title} onClose={onClose}>
        <div className="mp" onKeyDown={keys}>
          <K.SearchField size="lg" shortcut={false} label={t('mp.search')} placeholder={t('mp.search')} value={q} onChange={setQ} />
          <div className="mp-chips" role="group" aria-label={t('mp.kinds')}>
            <K.Chip size="sm" pressed={!kind} onPress={() => setKind(undefined)} count={counts.all}>{t('mp.all')}</K.Chip>
            {KINDS.filter((k) => counts[k] || k === kind).map((k) => (
              <K.Chip key={k} size="sm" pressed={kind === k} onPress={(on) => setKind(on ? k : undefined)} count={counts[k]}>{t(`mp.kind.${k}` as Key)}</K.Chip>
            ))}
          </div>
          <div className="mp-chips" role="group" aria-label={t('mp.filters')}>
            {job && <K.Chip size="sm" icon="filter" pressed={fits} onPress={setFits}>{t('mp.fits', { job: t(`mo.job.${job}` as Key) })}</K.Chip>}
            {mixed && (['local', 'online'] as const).map((w) => <K.Chip key={w} size="sm" pressed={where === w} onPress={(on) => setWhere(on ? w : undefined)}>{t(`mp.${w}`)}</K.Chip>)}
            {conns.length > 1 && conns.map((p) => <K.Chip key={p.id} size="sm" icon={local(p.base_url) ? 'server' : 'globe'} pressed={pid === p.id} onPress={(on) => setPid(on ? p.id : undefined)}>{p.name}</K.Chip>)}
            <label className="mp-sort">
              <span className="t-meta">{t('mp.sort')}</span>
              <K.Select options={sorts.map(([, l]) => l)} value={sorts.find(([s]) => s === sort)?.[1]} onChange={(v) => setSort(sorts.find(([, l]) => l === v)?.[0] ?? 'listed')} />
            </label>
          </div>
          <div className="mp-list" role="listbox" tabIndex={0} aria-label={title} aria-activedescendant={entries.length ? `${uid}-${active}` : undefined}>
            {rows === undefined ? <K.Spinner /> : entries.map((e, i) => (
              e === 'none' ? option(i, !value, none!, null, e)
                : e === 'gone' ? option(i, true, gone!.model, <K.Tag tone="warm">{t('mp.tag.gone')}</K.Tag>, e)
                  : option(i, is(e), e.id, <Tags m={e} />, e)
            ))}
            {rows && !found.length && <div className="mp-none t-meta">{t(all.length ? 'mp.none' : 'mp.empty')}</div>}
          </div>
          <div className="t-faint" aria-live="polite">{found.length > MOST ? t('mp.more', { shown: MOST, n: found.length }) : t('mp.count', { n: found.length })}</div>
        </div>
      </K.Dialog>
    </Overlay>
  )
}

function Tags({ m }: { m: Row }) {
  const used = m.last_used ? Date.parse(`${m.last_used.replace(' ', 'T')}Z`) : NaN
  return (
    <>
      <K.Tag>{m.provider.name}</K.Tag>
      <K.Tag>{t(m.local ? 'mp.local' : 'mp.online')}</K.Tag>
      {m.params_b !== undefined && <K.Tag>{size(m.params_b)}</K.Tag>}
      {m.context !== undefined && <K.Tag>{t('mp.tag.context', { n: tokens(m.context) })}</K.Tag>}
      {m.input !== undefined && m.output !== undefined && (
        <span title={t('mp.tag.priceHint')}><K.Tag>{m.input + m.output ? t('mp.tag.price', { input: dollars(m.input), output: dollars(m.output) }) : t('mp.tag.free')}</K.Tag></span>
      )}
      {m.kinds.includes('roleplay') && <K.Tag tone="warm">{t('mp.kind.roleplay')}</K.Tag>}
      {m.kinds.includes('reasoning') && <K.Tag tone="accent">{t('mp.tag.thinks')}</K.Tag>}
      {(['vision', 'image', 'voice', 'embedding'] as const).filter((k) => m.kinds.includes(k)).map((k) => <K.Tag key={k}>{t(`mp.kind.${k}`)}</K.Tag>)}
      {m.hosts && m.hosts.length > 1 && <span title={m.hosts.join(', ')}><K.Tag>{t('mp.tag.hosts', { n: m.hosts.length })}</K.Tag></span>}
      {!Number.isNaN(used) && <K.Tag>{t('mp.tag.used', { when: relative(used) })}</K.Tag>}
    </>
  )
}
