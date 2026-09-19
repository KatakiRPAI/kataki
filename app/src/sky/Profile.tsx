import { useState } from 'react'
import { api, type Item, type StorySummary } from '../api'
import { Avatar, Orb, Portrait, pronounsOf, Room } from '../art'
import { go, href, useLibrary, useLoad } from '../hooks'
import { Candy, ErrorLine, Glass, Icon, Prose } from '../ui'
import { status, storiesWith } from './Friends'
import NewChat, { type Preset } from './NewChat'

/** "Mira: Coin first." -> "Coin first." (example lines are written as "Name: line"). */
const spoken = (line: string, item: Item) => {
  const names = [item.name, ...(item.data.aliases ?? [])].map((n) => n.toLowerCase())
  const m = /^\s*([^:*]{1,40}):\s*(.*)$/.exec(line)
  return m && names.includes(m[1].trim().toLowerCase()) ? m[2] : line.trim()
}

/** #/friend/:id — a friend before you message them. */
export default function Profile({ id }: { id: number }) {
  const { byId, loaded } = useLibrary()
  const [stories, reload, error] = useLoad(() => api<StorySummary[]>('/stories'), [])
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
          </div>
          <div className="ka-cards">
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
          go(`/chats/${story.id}`) // until the Scene lands (task 20)
        }}
      />
    </>
  )
}
