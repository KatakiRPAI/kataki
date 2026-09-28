// Home (C1, C2, C3): docs/handoff/kataki-handoff/SCREENS.md › /home.
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { api, type ActivityEvent, type Item, type Person, type Provider, type RoleRow, type Story, type StorySummary } from '../api'
import { K } from '../ds'
import { face, scenery, twelve, useLibrary, useLoad, utc } from '../hooks'
import { relative, t } from '../strings'
import { err } from '../errors'
import { byShipped, isDraft, said } from '../characters'
import { storyMenu } from './storyMenu'
import Top from './Top'
import { openFeedback } from './Feedback'
import { Overlay, withMenu } from '../overlay'
import { setPref, usePrefs } from '../prefs'

type Filter = 'all' | 'story' | 'drafts'
const TONE = { memory: 'ok', belief: 'warm', feeling: 'warm', time: 'muted' } as const
const EVENT = { memory: 'event.memory', belief: 'event.belief', feeling: 'event.feeling', time: 'event.time' } as const
// a quote is what was said; the *actions* of the chat are left out
const quoted = (text: string) => `“${said(text)}”`

export default function Home() {
  const navigate = useNavigate()
  const { items, byId } = useLibrary()
  const [settings] = useLoad(() => api<{ persona?: number }>('/settings'), [])
  const [stories, reloadStories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [events] = useLoad(() => api<ActivityEvent[]>('/activity?limit=12'), [])
  const [filter, setFilter] = useState<Filter>('all')
  // C3: is anyone answering? Sky pages never wait on it.
  const [offline] = useLoad(async () => {
    const rp = (await api<RoleRow[]>('/roles')).find((r) => r.role === 'rp')
    if (!rp?.effective_provider_id) return null
    const provider = (await api<Provider[]>('/providers')).find((p) => p.id === rp.effective_provider_id)
    const elsewhere = !!provider && !/^https?:\/\/(localhost|127\.|\[::1\])/.test(provider.base_url)
    if (elsewhere && !navigator.onLine) return 'OFFLINE'
    return api(`/providers/${rp.effective_provider_id}/models`).then(() => null, () => provider?.name ?? '?')
  }, [])
  const played = [...(stories ?? [])].sort((a, b) => utc(b.last_at) - utc(a.last_at))
  const hero = played[0]
  const [people] = useLoad(() => (hero ? api<Person[]>(`/stories/${hero.id}/people`) : Promise.resolve([])), [hero?.id])

  const persona = settings?.persona ? byId.get(settings.persona) : undefined
  const characters = items.filter((i) => i.kind === 'character' && !i.data.persona)
  const lastPlayed = (c: Item) => played.find((s) => s.cast.some((x) => x.lib_item_id === c.id))
  const shown = characters.filter((c) => (filter === 'story' ? !!lastPlayed(c) : filter === 'drafts' ? isDraft(c) : true))
  const lead = hero?.cast.find((c) => c.present) ?? hero?.cast[0]
  const ordered = [...shown].sort((a, b) => (a.id === lead?.lib_item_id ? -1 : b.id === lead?.lib_item_id ? 1 : utc(lastPlayed(b)?.last_at ?? '1970-01-01 00:00:00') - utc(lastPlayed(a)?.last_at ?? '1970-01-01 00:00:00')))

  const [crash, setCrash] = useState(() => !!window.kataki?.crashed && !crashSeen.done)
  if (!stories) return <main className="app__main" aria-label={t('home.label')}><K.Skeleton /></main>

  const top = (
    <>
      <Top />
      {crash && hero && <Crashed story={hero} onClose={() => { crashSeen.done = true; setCrash(false) }} onContinue={() => { crashSeen.done = true; navigate(`/story/${hero.id}`) }} />}
    </>
  )
  // day one: everyone who came with Kataki except the one you are (Home › C2)
  const others = items.filter((i) => i.kind === 'character' && i.id !== persona?.id).sort(byShipped)
  const start = async (c: Item) => {
    const place = c.data.places?.[0]
    const story = await api<Story>('/stories', 'POST', { title: `${(place && byId.get(place)?.name) || c.name} · ${new Date().toLocaleDateString('en-GB', { weekday: 'long' })}`, character_ids: [c.id], place_id: place ?? null, persona_id: persona?.id ?? null })
    navigate(`/story/${story.id}`)
  }

  if (!hero) {
    return (
      <main className="app__main" aria-label={t('home.label')}>
        {top}
        <section className="home-day1">
          <K.Eyebrow tone="mid">{t('home.empty.eyebrow')}</K.Eyebrow>
          <h1 className="home-day1__h">{t('home.empty.title')}</h1>
          <p className="home-day1__p">{t('home.empty.sub', { n: others.length })}</p>
        </section>
        {others.length > 0 && (
          <section className="sec" aria-label={t('home.empty.start')}>
            <h2 className="sec-title">{t('home.empty.start')}</h2>
            <div className="row row--wrap" style={{ gap: 16, alignItems: 'flex-start' }}>
              {others.filter((c) => !isDraft(c)).map((c, i) => (
                <div key={c.id} className="col" style={{ gap: 10 }}>
                  <K.CharacterCard {...face(c)} name={c.name} line={c.data.tagline} when={t('card.when.never')} />
                  <K.Button variant={i ? 'secondary' : 'primary'} size="sm" full onClick={() => start(c)}>{t('home.empty.sayHello')}</K.Button>
                </div>
              ))}
            </div>
          </section>
        )}
        <section className="sec" aria-label={t('home.empty.nothing')}>
          <h2 className="sec-title">{t('home.empty.nothing')}</h2>
          <div className="row" style={{ gap: 16, alignItems: 'stretch' }}>
            <K.DoorCard icon="feather" eyebrow={t('home.door.writeTag')} title={t('home.door.write')} actions={<K.Button size="sm" href="/characters/new">{t('home.newCharacter')}</K.Button>}>{t('home.door.writeBody')}</K.DoorCard>
            <K.DoorCard icon="download" eyebrow={t('home.door.importTag')} title={t('home.door.import')} actions={<K.Button size="sm" href="/characters?import=1">{t('fr.importBtn')}</K.Button>}>{t('home.door.importBody')}</K.DoorCard>
            <K.DoorCard icon="map" eyebrow={t('home.door.placeTag')} title={t('home.door.place')} actions={<K.Button size="sm" href="/world?new=place">{t('w.newPlace')}</K.Button>}>{t('home.door.placeBody')}</K.DoorCard>
          </div>
        </section>
        <div style={{ maxWidth: 760 }}><K.Callout tone="warm" title={t('home.empty.know')}>{t('home.empty.knowBody', { name: others[0]?.name ?? '' })}</K.Callout></div>
      </main>
    )
  }

  const heroPerson = people?.find((p) => p.lib_item_id === lead?.lib_item_id)
  const since = (events ?? []).filter((e) => e.new).slice(0, 3)
  const place = hero.place ? byId.get(hero.place.lib_item_id ?? -1) : undefined
  const counts = {
    all: characters.length,
    story: characters.filter((c) => lastPlayed(c)).length,
    drafts: characters.filter(isDraft).length,
  }

  return (
    <main className="app__main" aria-label={t('home.label')}>
      <a href={`/story/${hero.id}`} className="sr">{t('home.skip')}</a>
      {top}
      {offline === 'OFFLINE' ? <K.StatusLine tone="warm" title={err('OFFLINE').title}>{err('OFFLINE').body}</K.StatusLine> : offline && (
        <K.StatusLine tone="bad" title={t('home.offline')} action={<K.Button size="sm" href="/status/model">{t('home.what')}</K.Button>}>{t('home.offlineBody', { server: offline })}</K.StatusLine>
      )}
      <K.ContinueHero
        title={hero.title}
        book={hero.book?.title ?? t('home.noBook')}
        lastLine={hero.last_line ? quoted(hero.last_line.text) : t('home.noLine')}
        {...(() => { const f = face(byId.get(lead?.lib_item_id ?? -1), lead?.name); return { who: f.who, avatarSrc: f.src, avatarName: f.name } })()}
        stats={t('home.stats', { memories: heroPerson?.remembers ?? 0, changed: hero.new_events })}
        where={t('home.where', { relative: hero.date, place: hero.place?.name ?? '', time: twelve(hero.clock) })}
        {...(() => { const s = scenery(place); return { place: s.place ?? '', placeSrc: s.src } })()}
        caption={hero.scene_title ?? undefined}
        placeAlt={hero.place?.name}
        continueHref={`/story/${hero.id}`}
        newHref={`/stories/new?with=${hero.cast.flatMap((c) => (c.lib_item_id ? [c.lib_item_id] : [])).join(",")}`}
      />

      {since.length > 0 && (
        <section className="sec" aria-label={t('home.since')}>
          <div style={{ display: 'flex', gap: 22, alignItems: 'baseline' }}>
            <K.Eyebrow>{t('home.since')}</K.Eyebrow>
            <span className="t-faint">{t('home.events', { n: since.length, lastPlayed: relative(utc(hero.last_at)) })}</span>
          </div>
          <div className="home-row" style={{ display: 'flex', gap: 12 }}>
            {since.map((e) => {
              const who = e.who[0]
              const f = face(byId.get(who?.lib_item_id ?? -1), who?.name)
              return (
                <a key={e.key} href={who?.lib_item_id ? `/characters/${who.lib_item_id}` : `/story/${e.story_id}`} style={{ flex: 1, minWidth: 0 }}>
                  <K.EventCard who={f.who ?? ''} avatarSrc={f.src} name={who?.name ?? ''} event={t(EVENT[e.kind])} tone={TONE[e.kind]}
                    memory={quoted(e.text)} meta={e.sub} />
                </a>
              )
            })}
          </div>
        </section>
      )}

      <section className="sec" aria-label={t('home.characters')}>
        <div className="sec-head">
          <h2 className="sec-title">{t('home.characters')}</h2>
          <div className="row" style={{ gap: 8 }}>
            {(['all', 'story', 'drafts'] as const).map((f) => (
              <K.Chip key={f} size="sm" pressed={filter === f} count={counts[f]} onPress={() => setFilter(f)}>
                {t(f === 'all' ? 'home.filter.all' : f === 'story' ? 'home.filter.inStory' : 'home.filter.drafts')}
              </K.Chip>
            ))}
          </div>
        </div>
        <div className="home-row" style={{ display: 'flex', gap: 16, alignItems: 'flex-start', overflow: 'hidden' }}>
          {ordered.slice(0, 5).map((c) => {
            const last = lastPlayed(c)
            const featured = c.id === lead?.lib_item_id
            return (
              <a key={c.id} href={`/characters/${c.id}`} aria-label={c.name}>
                <K.CharacterCard {...face(c)} name={c.name} featured={featured}
                  when={last ? t('card.when.played', { relative: relative(utc(last.last_at)) }) : t('card.when.never')}
                  badge={featured ? t('home.inStory') : undefined} badgeTone={featured ? 'warm' : undefined} />
              </a>
            )
          })}
          <K.AddCard href="/characters/new" sub={t('home.newCharacterSub')}>{t('home.newCharacter')}</K.AddCard>
        </div>
      </section>

      {played.length > 1 && (
        <section className="sec" aria-label={t('home.threads')}>
          <div className="sec-head">
            <h2 className="sec-title">{t('home.threads')}</h2>
            <K.TextLink href="/stories">{t('home.allStories')}</K.TextLink>
          </div>
          <div className="home-row" style={{ display: 'flex', gap: 14, alignItems: 'stretch' }}>
            {played.slice(1, 4).map((s) => (
              <a key={s.id} href={`/story/${s.id}`} style={{ flex: '1 1 260px', display: 'flex' }} {...withMenu(() => storyMenu(s, navigate, reloadStories))}>
                <K.StoryCard title={s.title} book={s.book?.title ?? t('home.noBook')} pinned={s.pinned}
                  people={s.cast.map((c) => { const f = face(byId.get(c.lib_item_id ?? -1), c.name); return { who: f.who, src: f.src, name: c.name } })}
                  quote={s.last_line ? quoted(s.last_line.text) : t('home.noLine')}
                  when={t('card.when.played', { relative: relative(utc(s.last_at)) })} storyTime={s.date} />
              </a>
            ))}
          </div>
        </section>
      )}
      <Privacy />
    </main>
  )
}

const crashSeen = { done: false } // A3 shows once per launch

/** A3: the last run ended without closing properly. */
function Crashed({ story, onClose, onContinue }: { story: StorySummary; onClose: () => void; onContinue: () => void }) {
  const [prefs] = usePrefs()
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="alert" tone="warm" title={t('crash.title')} description={t('crash.body')} onClose={onClose} note={t('crash.note')}
        actions={[
          <K.Button key="r" variant="ghost" onClick={() => { onClose(); openFeedback('bug') }}>{t('crash.report')}</K.Button>,
          <K.Button key="s" variant="ghost" onClick={onClose}>{t('crash.stay')}</K.Button>,
          <K.Button key="c" variant="primary" onClick={onContinue}>{t('crash.continue')}</K.Button>,
        ]}>
        <K.KeyValue label={t('crash.last')}>{story.title}</K.KeyValue>
        <K.KeyValue label={t('crash.checked')}>{t('crash.checkedValue')}</K.KeyValue>
        <K.Checkbox label={t('crash.ask')} checked={!!prefs['general.askAfterCrash']} onChange={(v) => setPref('general.askAfterCrash', v)} />
      </K.Dialog>
    </Overlay>
  )
}

function Privacy() {
  return (
    <div className="privacy">
      <K.Icon name="lock" size={16} />
      <span>{t('home.privacy')}</span>
      <a href="/settings/data">{t('home.whereData')}</a>
    </div>
  )
}
