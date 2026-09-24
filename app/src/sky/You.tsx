import { api, type Profile, type RoleRow, type StorySummary } from '../api'
import { Avatar, Portrait, Room } from '../art'
import { diveLink, go, href, useLibrary, useLoad } from '../hooks'
import { ErrorLine, Glass, Icon } from '../ui'
import { PersonaChoices } from './Home'
import { Look } from './Profile'

/** #/you and #/you/:id — who you play, and who you are in new chats. */
export default function You({ id }: { id?: number }) {
  const { items, byId, loaded } = useLibrary()
  const [settings, reloadSettings, settingsError] = useLoad(() => api<{ persona?: number | null }>('/settings'), [])
  const [stories, , storiesError] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [roles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const pictures = !!roles?.find((r) => r.role === 'image')?.effective_model
  const who = id ?? settings?.persona
  const [profile] = useLoad(
    () => (who ? api<Profile>(`/library/${who}/profile`).then((p) => ({ who, p })) : Promise.resolve(null)),
    [who],
  )
  if (!loaded || !settings) return null

  const personas = items.filter((i) => i.kind === 'character' && i.data.persona).sort((a, b) => a.id - b.id)
  const current = personas.find((p) => p.id === settings.persona)
  const shown = id === undefined ? current : byId.get(id)
  const theirs = (stories ?? []).filter((s) => (shown ? s.persona?.lib_item_id === shown.id : !s.persona))
  // who has met this persona, and how much of them they still hold; the emptiest last
  const knowers = (profile && profile.who === who ? profile.p.stories : [])
    .flatMap((story) => (story.known_by ?? []).map((k) => ({ story, k })))
    .sort((a, b) => b.k.count - a.k.count)
  const pick = (persona: number | null) =>
    api('/settings', 'PUT', { persona }).then(() => {
      reloadSettings()
      go('/you')
    })

  return (
    <>
      <header className="ka-row ka-row--gap16">
        <Avatar item={current} name={current?.name ?? 'Director'} size={62} className="k-avatar--ring" />
        <span className="ka-stack ka-stack--tight">
          <span className="ka-home-head__hello">{current ? 'You are playing' : 'You are'}</span>
          <h1 className="k-display ka-home-head__name ka-m0">{current?.name ?? 'the director'}</h1>
        </span>
      </header>
      <ErrorLine error={settingsError || storiesError} />
      <div className="ka-you">
        <section className="k-card ka-you__choices" aria-label="Who are you in new chats?">
          <h2 className="k-eyebrow ka-eyebrow">Who are you in new chats?</h2>
          <PersonaChoices current={current} personas={personas} onPick={pick} big />
        </section>

        <div className="ka-stack">
          {shown ? (
            <>
              <Portrait item={shown} className="ka-you__portrait">
                <span className="ka-you__badge">
                  <Icon name="user" size={14} />
                  {shown.id === current?.id ? 'Played by you' : 'One of your personas'}
                </span>
                <div className="k-nameplate">
                  <span className="k-display ka-live__name">{shown.name}</span>
                  {shown.description && <span className="ka-live__tagline">{shown.description.split('\n')[0]}</span>}
                </div>
              </Portrait>
              {shown.id !== current?.id && (
                <button type="button" className="k-btn k-btn--dark" onClick={() => pick(shown.id)}>
                  <Icon name="swap" size={16} />
                  Be {shown.name} in new chats
                </button>
              )}
              <a className="k-btn" href={href(`/friend/${shown.id}/edit`)}>
                <Icon name="edit" size={16} />
                Edit {shown.name}
              </a>
            </>
          ) : (
            <Glass title="You're directing">
              <span className="ka-muted">
                In new chats you play no one: you set the scene and every character answers for themselves. Pick a persona to step into a story yourself.
              </span>
            </Glass>
          )}
        </div>

        <div className="ka-stack ka-stack--18">
        {shown && pictures && <Look key={shown.id} item={shown} />}
        {shown && knowers.length > 0 && (
          <Glass title={`Who knows ${shown.name}`}>
            {knowers.map(({ story, k }) => (
              <a key={`${story.id}-${k.id}`} className="ka-knows" {...diveLink(`/story/${story.id}/backstage/${k.id}`)}>
                <Avatar item={byId.get(k.lib_item_id ?? -1)} name={k.name} size={44} />
                <span className="ka-stack ka-stack--tight ka-grow">
                  <strong>
                    {k.count
                      ? `${k.name} remembers ${k.count} ${k.count === 1 ? 'thing' : 'things'}`
                      : `${k.name} has nothing of you yet`}
                  </strong>
                  <span className="ka-muted ka-small">
                    {[story.title, k.hazy ? `${k.hazy} hazy` : '', k.forgotten ? `${k.forgotten} faded out` : '']
                      .filter(Boolean)
                      .join(' · ')}
                  </span>
                </span>
                <Icon name="right" size={18} />
              </a>
            ))}
          </Glass>
        )}

        <Glass title={shown ? `${shown.name}'s chats` : 'Stories you direct'}>
          {theirs.length === 0 && <span className="ka-muted">{shown ? `No chats as ${shown.name} yet.` : 'None yet.'}</span>}
          {theirs.map((st) => (
            <a key={st.id} className="ka-story-row" href={href(`/chats/${st.id}`)}>
              <span className="ka-story-row__thumb">
                <Room item={byId.get(st.place?.lib_item_id ?? -1)} minute={st.minute_of_day} />
              </span>
              <span className="ka-stack ka-stack--tight">
                <strong>{st.title}</strong>
                <span className="ka-muted ka-small">
                  {[st.cast.map((c) => c.name).join(' and '), st.clock.split(',')[0]].filter(Boolean).join(' · ')}
                </span>
              </span>
            </a>
          ))}
        </Glass>
        </div>
      </div>
    </>
  )
}
