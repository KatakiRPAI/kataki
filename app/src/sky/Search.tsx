// Search (C8, C9): everything, grouped and sorted.
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { K } from '../ds'
import { face } from '../hooks'
import { find, index, nearly, remember, type Hit } from '../search'
import { t, type Key } from '../strings'

type Tab = 'all' | 'lines' | 'stories' | 'characters' | 'places' | 'memories'
const TABS: Tab[] = ['all', 'lines', 'stories', 'characters', 'places', 'memories']
const IN: Record<Exclude<Tab, 'all'>, Hit['kind'][]> = { lines: ['line'], stories: ['story', 'book'], characters: ['character', 'persona'], places: ['place', 'scenario'], memories: ['memory'] }
type Sort = 'best' | 'newest' | 'oldest'
const ICON: Record<Hit['kind'], import('../ds/kataki').IconName> = { story: 'chat', book: 'book', character: 'user', persona: 'user', place: 'map-pin', scenario: 'quote', line: 'quote', memory: 'spark' }

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
  const q = params.get('q') ?? ''
  const [typed, setTyped] = useState(q)
  const [ix, setIx] = useState<Awaited<ReturnType<typeof index>>>()
  const [tab, setTab] = useState<Tab>('all')
  const [sort, setSort] = useState<Sort>('best')
  const [more, setMore] = useState<Tab[]>([])
  useEffect(() => { index().then(setIx, () => {}) }, [])
  useEffect(() => setTyped(q), [q])
  const hits = ix ? find(ix, q) : []
  const sorted = sort === 'best' ? hits : [...hits].sort((a, b) => (sort === 'newest' ? b.at - a.at : a.at - b.at))
  const of = (tb: Exclude<Tab, 'all'>) => sorted.filter((h) => IN[tb].includes(h.kind))
  const counts = Object.fromEntries(TABS.map((tb) => [t(`sr.${tb}` as Key), tb === 'all' ? hits.length : of(tb).length]))
  const row = (h: Hit) => {
    const f: { who?: string; src?: string } = h.item ? face(h.item) : {}
    return (
      <a key={`${h.kind}${h.id}`} href={h.href} className="sr-row" onClick={() => remember({ kind: h.kind, title: h.title, href: h.href })}>
        <K.SearchResult icon={ICON[h.kind]} who={f.who} src={f.src} story={h.kind === 'story'} title={h.kind === 'line' || h.kind === 'memory' ? (h.story?.title ?? '') : h.title}
          meta={[t(`kind.${h.kind}` as Key), h.speaker, h.when].filter(Boolean).join(' · ')}
          excerpt={h.text ? <Marked text={h.text.replace(/\*/g, '')} q={q} /> : undefined} />
      </a>
    )
  }
  const submit = () => setParams(typed.trim() ? { q: typed.trim() } : {}, { replace: true })
  return (
    <main className="app__main" aria-label={t('sr.search')} style={{ gap: 22 }}>
      <form onSubmit={(e) => { e.preventDefault(); submit() }}>
        <K.SearchField size="lg" value={typed} onChange={setTyped} label={t('sr.search')} placeholder={t('sr.search')} shortcut={false} />
      </form>
      {q && ix && hits.length === 0 ? (
        <div style={{ maxWidth: 640 }}>
          <K.EmptyState icon="search" title={t('sr.none', { q })} actions={[
            ...[nearly(ix, q)].filter((x): x is string => !!x).map((m) => <K.Chip key={m} size="sm" onClick={() => setParams({ q: m })}>{m}</K.Chip>),
            <K.Button key="n" size="sm" icon="user" onClick={() => navigate(`/characters/new?name=${encodeURIComponent(q)}`)}>{t('pal.makeCharacter', { q })}</K.Button>,
            <K.Button key="c" size="sm" variant="ghost" onClick={() => setParams({})}>{t('sr.clear')}</K.Button>,
          ]}>{t('sr.noneBody')}</K.EmptyState>
        </div>
      ) : q ? (
        <>
          <span className="t-meta">{t('sr.results', { n: hits.length })}</span>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <K.Tabs label={t('sr.search')} tabs={TABS.map((tb) => t(`sr.${tb}` as Key))} counts={counts} value={t(`sr.${tab}` as Key)}
              onChange={(v) => setTab(TABS.find((tb) => t(`sr.${tb}` as Key) === v) ?? 'all')} />
            <div style={{ width: 190 }}>
              <K.Select label="" options={(['best', 'newest', 'oldest'] as Sort[]).map((s) => t(`sr.${s}` as Key))} value={t(`sr.${sort}` as Key)}
                onChange={(v) => setSort((['best', 'newest', 'oldest'] as Sort[]).find((s) => t(`sr.${s}` as Key) === v) ?? 'best')} />
            </div>
          </div>
          {tab === 'all' ? TABS.slice(1).map((tb) => {
            const list = of(tb as Exclude<Tab, 'all'>)
            if (!list.length) return null
            const open = more.includes(tb)
            return (
              <section key={tb} className="sec" aria-label={t(`sr.${tb}` as Key)}>
                <h2 className="sec-title">{t(`sr.${tb}` as Key)}</h2>
                <div className="card sr-list">{(open ? list : list.slice(0, 3)).map(row)}</div>
                {!open && list.length > 3 && <button type="button" className="linkbtn" onClick={() => setMore((m) => [...m, tb])}>{t('sr.more', { n: list.length - 3 })}</button>}
              </section>
            )
          }) : <div className="card sr-list">{of(tab).map(row)}</div>}
        </>
      ) : null}
    </main>
  )
}
