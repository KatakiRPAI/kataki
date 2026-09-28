// Search (C8, C9): everything in one list, best first; tabs narrow it.
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { K } from '../ds'
import { face, useLibrary, utc } from '../hooks'
import { lookup, nearly, remember, type Hit } from '../search'
import { relative, t, type Key } from '../strings'

type Tab = 'all' | 'lines' | 'stories' | 'characters' | 'places' | 'memories'
const TABS: Tab[] = ['all', 'lines', 'stories', 'characters', 'places', 'memories']
const SHOWN = 6 // then “{n} more”
const IN: Record<Exclude<Tab, 'all'>, Hit['kind'][]> = { lines: ['line'], stories: ['story', 'book'], characters: ['character', 'persona'], places: ['place', 'scenario'], memories: ['memory'] }
type Sort = 'best' | 'newest' | 'oldest'
const ICON: Record<Hit['kind'], import('../ds/kataki').IconName> = { story: 'chat', book: 'book', character: 'user', persona: 'user', place: 'map-pin', scenario: 'book', line: 'quote', memory: 'thought' }

/** The words with the match marked. */
function Marked({ text, q }: { text: string; q: string }) {
  const i = text.toLowerCase().indexOf(q.toLowerCase())
  if (i < 0) return <>{text}</>
  const from = Math.max(0, i - 60)
  return <>{from ? '…' : ''}{text.slice(from, i)}<mark>{text.slice(i, i + q.length)}</mark>{text.slice(i + q.length, i + q.length + 120)}</>
}

export default function Search() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const { items } = useLibrary()
  const q = params.get('q') ?? ''
  const [typed, setTyped] = useState(q)
  const [hits, setHits] = useState<Hit[]>()
  const [mean, setMean] = useState<string>()
  const [tab, setTab] = useState<Tab>('all')
  const [sort, setSort] = useState<Sort>('best')
  const [all, setAll] = useState(false)
  useEffect(() => {
    setHits(undefined)
    setAll(false)
    lookup(q).then(setHits, () => setHits([]))
    nearly(q).then(setMean, () => {})
  }, [q])
  useEffect(() => setTyped(q), [q])
  const found = hits ?? []
  const sorted = sort === 'best' ? found : [...found].sort((a, b) => (sort === 'newest' ? b.at - a.at : a.at - b.at))
  const of = (tb: Tab) => (tb === 'all' ? sorted : sorted.filter((h) => IN[tb].includes(h.kind)))
  const counts = Object.fromEntries(TABS.map((tb) => [t(`sr.${tb}` as Key), of(tb).length]))
  const row = (h: Hit) => {
    const speaker = h.kind === 'line' ? items.find((i) => i.kind === 'character' && i.name === h.speaker) : undefined
    const lead = h.kind === 'story' ? items.find((i) => i.id === h.story?.cast[0]?.lib_item_id) : undefined
    const f: { who?: string; src?: string } = h.item?.kind === 'character' ? face(h.item) : speaker ? face(speaker) : lead ? face(lead) : {}
    const said = h.kind === 'line' ? h.text!.replace(/\*[^*]*\*/g, ' ').replace(/\s+/g, ' ').trim() : ''
    const done = h.kind === 'line' ? (h.text!.match(/\*[^*]*\*/g) ?? []).map((a) => a.slice(1, -1)).join(' ') : ''
    const s = h.story
    const title = h.kind === 'line' ? `“${said || h.text!.replace(/\*/g, '')}”` : h.title
    const meta = h.kind === 'line' ? [h.speaker, s?.title, h.when].filter(Boolean).join(' · ')
      : h.kind === 'story' ? [t('kind.story'), s && t('card.when.played', { relative: relative(utc(s.last_at)) })].filter(Boolean).join(' · ')
      : h.kind === 'memory' ? [t('kind.memory'), s?.title].filter(Boolean).join(' · ')
      : t(`kind.${h.kind}` as Key)
    const excerpt = h.kind === 'line' ? (said && done ? `*${done}*` : undefined)
      : h.kind === 'story' && s ? [[...s.cast.map((c) => c.name), s.persona?.name].filter(Boolean).join(', '), t('sr.messages', { n: s.messages }), s.date].filter(Boolean).join(' · ')
      : h.kind === 'memory' ? undefined : h.text
    return (
      <a key={`${h.kind}${h.id}`} href={h.href} className="sr-row" onClick={() => remember({ kind: h.kind, title: h.title, href: h.href })}>
        <K.SearchResult icon={ICON[h.kind]} who={f.who} src={f.src} story={!['line', 'memory'].includes(h.kind)} title={title} meta={meta}
          excerpt={excerpt ? <Marked text={excerpt} q={q} /> : undefined} action={h.kind === 'line' ? t('sr.openLine') : undefined} />
      </a>
    )
  }
  const submit = () => setParams(typed.trim() ? { q: typed.trim() } : {}, { replace: true })
  const list = of(tab)
  return (
    <main className="app__main" aria-label={t('sr.results.label')} style={{ gap: 24 }}>
      <div className="row" style={{ gap: 16 }}>
        <K.TextLink href="/home" icon="left">{t('rail.home')}</K.TextLink>
        <form style={{ flex: 1 }} onSubmit={(e) => { e.preventDefault(); submit() }}>
          <K.SearchField size="lg" value={typed} onChange={setTyped} label={t('sr.search')} placeholder={t('sr.search')} shortcut={false} />
        </form>
      </div>
      {q && hits && hits.length === 0 ? (
        <div style={{ maxWidth: 640 }}>
          <K.EmptyState icon="search" title={t('sr.none', { q })} actions={[
            ...[mean].filter((x): x is string => !!x).map((m) => <K.Chip key={m} size="sm" onClick={() => setParams({ q: m })}>{m}</K.Chip>),
            <K.Button key="n" size="sm" icon="user" onClick={() => navigate(`/characters/new?name=${encodeURIComponent(q)}`)}>{t('pal.makeCharacter', { q })}</K.Button>,
            <K.Button key="c" size="sm" variant="ghost" onClick={() => setParams({})}>{t('sr.clear')}</K.Button>,
          ]}>{t('sr.noneBody')}</K.EmptyState>
        </div>
      ) : q ? (
        <>
          <div className="pg-head">
            <div>
              <h1 className="pg-title">“{q}”</h1>
              <p className="pg-sub">{t('sr.results', { n: found.length })}</p>
            </div>
            <div style={{ width: 220 }}>
              <K.Select label={t('sr.sort')} options={(['best', 'newest', 'oldest'] as Sort[]).map((s) => t(`sr.${s}` as Key))} value={t(`sr.${sort}` as Key)}
                onChange={(v) => setSort((['best', 'newest', 'oldest'] as Sort[]).find((s) => t(`sr.${s}` as Key) === v) ?? 'best')} />
            </div>
          </div>
          <K.Tabs label={t('sr.results.label')} size="sm" tabs={TABS.map((tb) => t(`sr.${tb}` as Key))} counts={counts} value={t(`sr.${tab}` as Key)}
            onChange={(v) => { setTab(TABS.find((tb) => t(`sr.${tb}` as Key) === v) ?? 'all'); setAll(false) }} />
          <div className="sr-list" style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 900 }}>
            {(all ? list : list.slice(0, SHOWN)).map(row)}
            {!all && list.length > SHOWN && <div style={{ paddingTop: 4 }} onClick={() => setAll(true)}><K.ShowMore>{t('sr.more', { n: list.length - SHOWN })}</K.ShowMore></div>}
          </div>
        </>
      ) : null}
    </main>
  )
}
