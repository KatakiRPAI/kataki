import { useState } from 'react'
import { api, EXPRESSIONS, mediaUrl, type Expression, type Item, type PictureFailure, type Profile as Profiled, type RoleRow, type StorySummary } from '../api'
import { Avatar, Orb, Portrait, pronounsOf, Room } from '../art'
import { dive, diveLink, href, useAction, useLibrary, useLoad } from '../hooks'
import { Candy, ErrorLine, Glass, Icon, Menu, Prose } from '../ui'
import Elsewhere from './Elsewhere'
import { status, storiesWith } from './Friends'
import NewChat, { type Preset } from './NewChat'

const HER = { she: 'her', he: 'his', they: 'their' }

export const sentence = (s: string) => s[0].toUpperCase() + s.slice(1)

/** A share of the bar, rounded so the three parts never add up past 100. */
const part = (n: number, all: number) => (all ? Math.round((n / all) * 100) : 0)

/** "Mira: Coin first." -> "Coin first." (example lines are written as "Name: line"). */
const spoken = (line: string, item: Item) => {
  const names = [item.name, ...(item.data.aliases ?? [])].map((n) => n.toLowerCase())
  const m = /^\s*([^:*]{1,40}):\s*(.*)$/.exec(line)
  return m && names.includes(m[1].trim().toLowerCase()) ? m[2] : line.trim()
}


/** What the memory reader has noticed about someone in one story: where they were last, what
 *  they hold, how they feel about you, and how much of you they still hold on to. */
export function RightNow({ item, profile, prefer }: { item: Item; profile: Profiled; prefer?: number }) {
  const playing = profile.stories.filter((s) => s.person)
  const [inStory, setInStory] = useState<number>()
  // the story you played last, unless you pick another
  const story = playing.find((s) => s.id === inStory) ?? playing.find((s) => s.id === prefer) ?? playing.at(-1)
  const person = story?.person
  if (!person) return null

  const they = pronounsOf(item)
  const flag = (key: string) => person.state.find((f) => f.key.toLowerCase() === key)?.value
  const feels = person.relationships.filter((r) => r.you).map((r) => `${r.rel} you`)
  const about = person.about_you
  const known = about?.count ?? 0
  const rows: [string, string][] = [
    ['Last seen', person.present
      ? [person.where, story.clock].filter(Boolean).join(' · ')
      : `Away · since ${person.since}`],
    ['Holding', flag('holding') ?? '—'],
    ['Wearing', flag('wearing') ?? '—'],
    ['Feels about you', feels.length ? sentence(feels.join(', ')) : 'Nothing the reader has caught yet'],
  ]
  return (
    <Glass
      title="Right now"
      className="ka-cards__wide"
      action={
        playing.length > 1 ? (
          <Menu label="Which story" icon="film" text={`In ${story.title}`} className="k-btn k-btn--sm">
            {playing.map((s) => (
              <button key={s.id} type="button" aria-current={s.id === story.id ? 'true' : undefined}
                onClick={() => setInStory(s.id)}>
                <Icon name={s.id === story.id ? 'check' : 'film'} />
                {s.title}
              </button>
            ))}
          </Menu>
        ) : (
          <span className="ka-muted ka-small">In {story.title}</span>
        )
      }
    >
      {rows.map(([key, value]) => (
        <div key={key} className="ka-now">
          <span className="ka-now__key">{key}</span>
          <span className="ka-now__value">{value}</span>
        </div>
      ))}
      {about && (
        <>
          <div className="ka-now__head">
            <strong>
              Remembers {known} {known === 1 ? 'thing' : 'things'} about you
            </strong>
            <a className="ka-link ka-m0" {...diveLink(`/story/${story.id}/backstage/${person.id}`)}>
              See {HER[they]} memories
            </a>
          </div>
          <div className="ka-bar" role="img" aria-label={`${about.sharp} sharp, ${about.hazy} hazy, ${about.forgotten} forgotten`}>
            <span className="ka-bar__sharp" style={{ width: `${part(about.sharp, known)}%` }} />
            <span className="ka-bar__hazy" style={{ width: `${part(about.hazy, known)}%` }} />
          </div>
          <span className="ka-muted ka-small">
            {about.sharp} sharp · {about.hazy} hazy · {about.forgotten} faded out
          </span>
        </>
      )}
      {person.relationships.length > 0 && (
        <div className="ka-row ka-row--gap">
          {person.relationships.map((r) => (
            <span key={`${r.rel}-${r.other_id}`} className="k-tag" title={r.note ?? undefined}>
              {sentence(r.rel)} {r.you ? 'you' : r.other}
            </span>
          ))}
        </div>
      )}
    </Glass>
  )
}

/** A character's look: their picture (the sheet) and the five expressions made from it. Every
 *  button is one click and real money, so each says roughly what it costs. */
function Look({ item }: { item: Item }) {
  const { reload } = useLibrary()
  const [run, error, busy] = useAction()
  const [doing, setDoing] = useState<string>()
  const [failed, setFailed] = useState<Partial<Record<Expression, PictureFailure>>>({})
  const { portrait, pack } = item.data
  const stale = pack && pack.from !== portrait

  const act = (what: string, fn: () => Promise<unknown>) => {
    setDoing(what)
    run(fn).finally(() => setDoing(undefined))
  }
  const draw = () => act('draw', async () => {
    await api(`/library/${item.id}/draw`, 'POST', {})
    reload()
  })
  const make = (expressions?: Expression[]) => act(expressions?.[0] ?? 'all', async () => {
    const made = await api<{ failed: typeof failed }>(`/library/${item.id}/look`, 'POST', { expressions })
    // a redraw of one leaves the others' failures as they were
    setFailed((f) => ({ ...(expressions ? f : {}), ...Object.fromEntries((expressions ?? EXPRESSIONS).map((e) => [e, undefined])), ...made.failed }))
    reload()
  })

  return (
    <Glass title="Look" className="ka-cards__wide">
      <span className="ka-muted ka-small">
        {portrait
          ? `The five expressions are made from ${item.name}'s picture, never from each other, so the face stays the same.`
          : `${item.name} has no picture yet. Draw one from the description, or add your own in Edit profile.`}
      </span>
      <span className="ka-row ka-row--gap">
        <button type="button" className="k-btn k-btn--sm" disabled={busy} onClick={draw}>
          <Icon name="image" size={15} />
          {doing === 'draw' ? 'Drawing…' : portrait ? 'Draw a new picture' : `Draw ${item.name}`}
        </button>
        {portrait && (
          <button type="button" className="k-btn k-btn--dark k-btn--sm" disabled={busy} onClick={() => make()}>
            <Icon name="spark" size={15} />
            {doing === 'all' ? 'Making five expressions… about half a minute' : pack && !stale ? 'Remake all five' : 'Use this look'}
          </button>
        )}
        <span className="ka-muted ka-small">A picture costs about $0.005; five expressions about $0.24.</span>
      </span>
      {stale && <span className="ka-small">These were made from an earlier picture. Remake them to match the new one.</span>}
      <ErrorLine error={error} />
      {pack && (
        <div className="ka-look">
          {EXPRESSIONS.map((e) => {
            const sprite = pack.sprites[e]
            return (
              <figure key={e} className="ka-look__tile">
                <span className="ka-look__art">
                  {sprite ? <img src={mediaUrl(sprite)} alt={`${item.name}, ${e}`} /> : <span className="ka-muted ka-small">Not made</span>}
                </span>
                <figcaption className="ka-row ka-row--gap">
                  <span className="ka-small">{sentence(e)}</span>
                  <button type="button" className="k-btn k-btn--ghost k-btn--sm ka-push-right" disabled={busy} onClick={() => make([e])}
                    aria-label={`Redraw ${e}`}>
                    {doing === e ? 'Drawing…' : 'Redraw'}
                  </button>
                </figcaption>
                {failed[e] && <span className="ka-error" role="alert">{failed[e]!.message}</span>}
              </figure>
            )
          })}
        </div>
      )}
    </Glass>
  )
}

/** #/friend/:id — a friend before you message them. */
export default function Profile({ id }: { id: number }) {
  const { byId, loaded } = useLibrary()
  const [stories, reload, error] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [profile] = useLoad(() => api<Profiled>(`/library/${id}/profile`), [id])
  const [roles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const pictures = !!roles?.find((r) => r.role === 'image')?.effective_model
  const [newChat, setNewChat] = useState<{ preset?: Preset; n: number }>({ n: 0 })
  const [revealed, setRevealed] = useState(false)
  const item = byId.get(id)
  if (!loaded) return null
  if (!item) return <p className="ka-muted">There's no one here. They may have been deleted.</p>

  const they = pronounsOf(item)
  const s = they === 'they' ? '' : 's' // "How she talks" / "How they talk"
  const theirs = storiesWith(item, stories ?? [])
  const latest = theirs[0]
  const { text: where, idle } = status(item, stories ?? [])
  const playedAs = [...new Set(theirs.map((st) => (st.persona ? `as ${st.persona.name}` : 'directing')))]
  const lines = (item.data.example_dialogue ?? '').split('\n').filter((l) => l.trim())
  // the newest story they are in leads the tiles; the places are wherever they have played
  const playing = (profile?.stories ?? []).filter((st) => st.person)
  const now = playing.find((st) => st.id === latest?.id) ?? playing.at(-1)
  const holds = now?.person?.about_you?.count
  const youAre = latest?.persona?.name ?? 'you'
  const lastSeen = (profile?.places ?? []).filter((p) => p.story_id === now?.id).at(-1)
  const startNew = (preset: Preset) => setNewChat((c) => ({ preset, n: c.n + 1 }))

  return (
    <>
      <a className="ka-back" href={href('/friends')}>
        <Icon name="left" size={16} />
        Friends
      </a>
      <div className="ka-profile">
        <div className="ka-profile__side">
          <Portrait item={item} className="ka-profile__portrait">
            <div className="k-nameplate">
              <span className="ka-row ka-row--gap">
                <h1 className="k-display ka-profile__name">{item.name}</h1>
                <span className={`k-status${idle ? ' k-status--idle' : ''}`}>{where}</span>
              </span>
              {item.description && <span className="ka-profile__tagline">{item.description.split('\n')[0]}</span>}
              {item.tags.length > 0 && (
                <span className="ka-row ka-row--gap">
                  {item.tags.map((t) => <span key={t} className="k-tag">{t}</span>)}
                </span>
              )}
            </div>
          </Portrait>
          {latest ? (
            // until the Scene lands (task 20), a story opens in Chats
            <a className="ka-message" href={href(`/chats/${latest.id}`)}>
              <span className="ka-stack ka-stack--tight">
                <strong>Message {item.name}</strong>
                <span>Continues {latest.title}</span>
              </span>
              <Orb size={48} />
            </a>
          ) : (
            <button type="button" className="ka-message" onClick={() => startNew({ friends: [item.id] })}>
              <span className="ka-stack ka-stack--tight">
                <strong>Message {item.name}</strong>
                <span>Starts your first story together</span>
              </span>
              <Orb size={48} />
            </button>
          )}
          <div className="ka-grid2">
            <button type="button" className="k-btn" onClick={() => startNew({ friends: [item.id] })}>
              <Icon name="plus" size={17} />
              Start a new story
            </button>
            <button type="button" className="k-btn" onClick={() => startNew({ friends: [item.id], group: true })}>
              <Icon name="users" size={17} />
              Start a group scene
            </button>
          </div>
          <a className="k-btn k-btn--ghost ka-center" href={href(`/friend/${item.id}/edit`)}>
            <Icon name="edit" size={15} />
            Edit profile
          </a>
        </div>

        <div className="ka-profile__main">
          <ErrorLine error={error} />
          <div className="ka-stats">
            <div className="k-glass ka-stat">
              <Candy icon="book" color="purple" />
              <span className="ka-stack ka-stack--tight">
                <strong>{theirs.length === 0 ? 'No stories yet' : `${theirs.length === 1 ? '1 story' : `${theirs.length} stories`} together`}</strong>
                <span className="ka-muted ka-small">{playedAs.length ? playedAs.join(' and ') : `Message ${item.name} to start one`}</span>
              </span>
            </div>
            {holds !== undefined && (
              <div className="k-glass ka-stat">
                <Candy icon="spark" color="gold" />
                <span className="ka-stack ka-stack--tight">
                  <strong>Remembers {holds} {holds === 1 ? 'thing' : 'things'}</strong>
                  <span className="ka-muted ka-small">about {youAre}</span>
                </span>
              </div>
            )}
            {lastSeen && (
              <div className="k-glass ka-stat">
                <Candy icon="map-pin" color="green" />
                <span className="ka-stack ka-stack--tight">
                  <strong>Last seen: {lastSeen.name}</strong>
                  <span className="ka-muted ka-small">{lastSeen.clock}</span>
                </span>
              </div>
            )}
          </div>
          <div className="ka-cards">
            {pictures && item.kind === 'character' && <Look item={item} />}
            {profile && <RightNow item={item} profile={profile} prefer={latest?.id} />}
            <Glass title={`Where else ${item.name} is`}>
              <Elsewhere item={item.id} name={item.name} />
            </Glass>
            <Glass title="About">
              <div className="ka-prose-sky"><Prose text={item.description || `Nothing written about ${item.name} yet.`} /></div>
              <span className="ka-muted ka-small">What anyone in a scene can see or know.</span>
              {(item.data.aliases ?? []).length > 0 && (
                <span className="ka-row ka-row--gap">
                  <span className="ka-muted ka-small">Also known as</span>
                  {item.data.aliases!.map((a) => <span key={a} className="k-tag">{a}</span>)}
                </span>
              )}
            </Glass>
            <Glass title={`How ${they} talk${s}`}>
              {lines.length ? (
                lines.map((l, i) => (
                  <div key={i} className="ka-said">
                    <Avatar item={item} size={30} />
                    <div className="k-bubble"><Prose text={spoken(l, item)} /></div>
                  </div>
                ))
              ) : (
                <a className="ka-link" href={href(`/friend/${item.id}/edit?step=4`)}>Show how {item.name} talks</a>
              )}
            </Glass>
            <Glass title={`How ${they} say${s} hi`}>
              {item.data.first_message ? (
                <div className="ka-said">
                  <Avatar item={item} size={30} />
                  <div className="k-bubble"><Prose text={item.data.first_message} /></div>
                </div>
              ) : (
                <a className="ka-link" href={href(`/friend/${item.id}/edit?step=5`)}>Give {item.name} a way to say hi</a>
              )}
            </Glass>
            {item.private ? (
              <section className={`k-secret${revealed ? ' is-revealed' : ''}`} aria-label="Secret">
                <div className="ka-card-head">
                  <strong className="ka-row ka-row--gap">
                    <Icon name="lock" size={17} />
                    Only {item.name} knows this
                  </strong>
                  <button type="button" className="ka-reveal" aria-pressed={revealed} onClick={() => setRevealed(!revealed)}>
                    <Icon name={revealed ? 'eyeoff' : 'eye'} size={15} />
                    {revealed ? 'Hide it again' : 'Reveal as author'}
                  </button>
                </div>
                <p className="k-secret__text" aria-hidden={!revealed}>{item.private}</p>
                <span className="ka-secret__note">Other characters never see it. {item.name} acts on it.</span>
              </section>
            ) : (
              <Glass title="A secret">
                <span className="ka-muted">{item.name} has no secret yet. Characters with secrets hold back, and it shows.</span>
                <a className="ka-link" href={href(`/friend/${item.id}/edit?step=3`)}>Add a secret</a>
              </Glass>
            )}
            {(profile?.places ?? []).length > 0 && (
              <Glass title={`Places ${they === 'they' ? "they've" : `${they}'s`} been`} className="ka-cards__wide">
                {profile!.places.map((p) => (
                  <a key={`${p.story_id}-${p.name}`} className="ka-story-row" href={href(`/chats/${p.story_id}`)}>
                    <span className="ka-story-row__thumb">
                      <Room item={byId.get(p.lib_item_id ?? -1)} minute={1140} />
                    </span>
                    <span className="ka-stack ka-stack--tight">
                      <strong>{p.name}</strong>
                      <span className="ka-muted ka-small">{p.story} · {p.clock}</span>
                    </span>
                  </a>
                ))}
              </Glass>
            )}
            <Glass title="Stories together" className="ka-cards__wide">
              {theirs.length === 0 && <span className="ka-muted">None yet. Start one above.</span>}
              {theirs.map((st) => {
                const others = st.cast.filter((c) => c.lib_item_id !== item.id).map((c) => c.name)
                const meta = [others.length ? `with ${others.join(', ')}` : '', st.persona ? `as ${st.persona.name}` : 'directing', st.clock.split(',')[0]]
                return (
                  <a key={st.id} className="ka-story-row" href={href(`/chats/${st.id}`)}>
                    <span className="ka-story-row__thumb">
                      <Room item={byId.get(st.place?.lib_item_id ?? -1)} minute={st.minute_of_day} />
                    </span>
                    <span className="ka-stack ka-stack--tight">
                      <strong>{st.title}</strong>
                      <span className="ka-muted ka-small">{meta.filter(Boolean).join(' · ')}</span>
                    </span>
                  </a>
                )
              })}
            </Glass>
          </div>
        </div>
      </div>
      <NewChat
        key={`chat-${newChat.n}`}
        open={!!newChat.preset}
        preset={newChat.preset ?? {}}
        onClose={() => setNewChat((c) => ({ n: c.n }))}
        onCreated={(story) => {
          setNewChat((c) => ({ n: c.n }))
          reload()
          dive(`/story/${story.id}`)
        }}
      />
    </>
  )
}
