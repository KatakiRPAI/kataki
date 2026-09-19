import { useEffect, useState, type ReactNode } from 'react'
import { api, upload, type Item, type Provider, type RoleRow } from '../api'
import { Avatar, nextPalette, Portrait } from '../art'
import clouds from '../design/clouds.svg'
import { dive, go, useAction, useLibrary, useLoad } from '../hooks'
import { Candy, ErrorLine, Field, Icon } from '../ui'
import NewChat from './NewChat'
import { AddApi } from './Settings'

type Found = { name: string; base_url: string; models: string[] }

const hostOf = (url: string) => url.replace(/^https?:\/\//, '').replace(/\/v1\/?$/, '')

function StepCard({ n, title, active, done, teaser, children }: {
  n: number
  title: string
  active: boolean
  done: boolean
  teaser: ReactNode
  children: ReactNode
}) {
  return (
    <section className={`k-glass ka-welcome__step${active ? ' is-active' : ''}`} aria-current={active ? 'step' : undefined} aria-label={title}>
      <h2 className="ka-row ka-row--gap">
        <span className={`k-step__dot${done && !active ? ' ka-dot-done' : ''}`}>{done && !active ? <Icon name="check" size={16} /> : n}</span>
        {title}
      </h2>
      {active ? children : teaser}
    </section>
  )
}

/** A name, a portrait and one line: a persona in step 2, a first friend in step 3. */
function QuickPerson({ persona, onCreated }: { persona: boolean; onCreated: (item: Item) => void }) {
  const { items } = useLibrary()
  const [name, setName] = useState('')
  const [line, setLine] = useState('')
  const [portrait, setPortrait] = useState<string>()
  const [palette] = useState(() => nextPalette(items))
  const [run, error, busy] = useAction()
  const look = { data: { palette, portrait } } as Item
  const create = () =>
    run(async () => {
      const item = await api<Item>('/library', 'POST', {
        kind: 'character',
        name: name.trim(),
        description: line.trim(),
        data: { persona, palette, portrait, pronouns: 'they' },
      })
      onCreated(item)
    })
  return (
    <form
      className="ka-quick"
      onSubmit={(e) => {
        e.preventDefault()
        create()
      }}
    >
      <label className="ka-quick__portrait" title="Add a portrait">
        <Portrait item={look} name={name || '?'} className="ka-quick__art" />
        <span className="ka-quick__add"><Icon name="image" size={14} /></span>
        <input type="file" className="k-sr" accept="image/png,image/jpeg,image/gif,image/webp" aria-label="Portrait" onChange={(e) => {
          const file = e.target.files?.[0]
          e.target.value = ''
          if (file) run(async () => setPortrait((await upload(file)).name))
        }} />
      </label>
      <div className="ka-stack ka-grow">
        <Field label={persona ? 'Your name in stories' : 'Their name'}>
          <input className="k-input" value={name} autoFocus placeholder={persona ? 'Aren' : 'Mira'} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label={persona ? 'One line about you' : 'One line about them'}>
          <input className="k-input" value={line} placeholder={persona ? 'A newcomer to the docks.' : 'Guild courier. Loyal to friends, wary of everyone else.'} onChange={(e) => setLine(e.target.value)} />
        </Field>
        <ErrorLine error={error} />
        <button className="k-btn k-btn--dark ka-self-start" disabled={busy || !name.trim()}>
          <Icon name="check" size={16} />
          {persona ? `I'll be ${name.trim() || 'them'}` : `Add ${name.trim() || 'them'}`}
        </button>
      </div>
    </form>
  )
}

/** #/welcome — connect a model, make yourself, add your first friend. */
export default function FirstRun() {
  const { items, loaded, reload: reloadLibrary } = useLibrary()
  const [providers, reloadProviders] = useLoad(() => api<Provider[]>('/providers'), [])
  const [roles, reloadRoles] = useLoad(() => api<RoleRow[]>('/roles'), [])
  const [settings, reloadSettings] = useLoad(() => api<{ persona?: number | null }>('/settings'), [])
  const [found, setFound] = useState<Found[] | null>(null)
  const [adding, setAdding] = useState({ open: false, n: 0 })
  const [pick, setPick] = useState({ provider: 0, model: '', models: [] as string[] })
  const [directing, setDirecting] = useState(false)
  const [friend, setFriend] = useState<Item>()
  const [chat, setChat] = useState(false)
  const [step, setStep] = useState<number>()
  const [run, error, busy] = useAction()

  const rp = roles?.find((r) => r.role === 'rp')
  const connected = !!rp?.effective_model
  const me = items.find((i) => i.data.persona && i.id === settings?.persona)
  const done = [connected, !!me || directing, !!friend || items.some((i) => i.kind === 'character' && !i.data.persona)]
  const ready = providers && roles && settings && loaded

  useEffect(() => {
    const first = done.indexOf(false) // start at the first step not done yet
    if (ready && step === undefined) setStep(first === -1 ? 2 : first)
  }, [ready]) // eslint-disable-line react-hooks/exhaustive-deps
  const look = () => run(async () => setFound(await api<Found[]>('/providers/detect')))
  useEffect(() => void look(), []) // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = () => {
    reloadProviders()
    reloadRoles()
  }
  const use = (f: Found) =>
    run(async () => {
      const p = await api<Provider>('/providers', 'POST', { name: f.name, base_url: f.base_url })
      if (f.models[0]) await api('/roles/rp', 'PUT', { provider_id: p.id, model: f.models[0] })
      refresh()
    })
  const addApi = (name: string, base_url: string, api_key: string) =>
    run(async () => {
      await api('/providers', 'POST', { name, base_url, api_key: api_key || null })
      setAdding((a) => ({ ...a, open: false }))
      refresh()
    })
  const choose = (provider: number) => {
    setPick({ provider, model: '', models: [] })
    if (provider) api<{ models: string[] }>(`/providers/${provider}/models`).then((r) => setPick((p) => ({ ...p, models: r.models })), () => {})
  }
  const known = new Set((providers ?? []).map((p) => p.base_url.replace(/\/$/, '')))
  const fresh = (found ?? []).filter((f) => !known.has(f.base_url.replace(/\/$/, '')))
  const server = providers?.find((p) => p.id === rp?.effective_provider_id)

  const bottom =
    step === 0 ? { label: 'Continue', icon: 'arrow', disabled: !connected, act: () => setStep(1) }
    : step === 1 ? { label: me ? 'Continue' : 'Skip: I direct the story', icon: 'arrow', disabled: false, act: () => {
        if (!me) api('/settings', 'PUT', { persona: null }).then(() => setDirecting(true))
        setStep(2)
      } }
    : { label: done[2] ? 'Go home' : 'Skip for now', icon: 'home', disabled: false, act: () => go('/home') }

  return (
    <div className="k-sky ka-sky ka-welcome">
      <img className="ka-clouds" src={clouds} alt="" />
      <img className="ka-clouds ka-clouds--high" src={clouds} alt="" />
      <main className="ka-welcome__main">
        <span className="ka-logo ka-logo--row">
          <span className="ka-logo__tile"><Icon name="cloud" size={20} /></span>
          <span className="k-display">Kataki</span>
        </span>
        <h1 className="k-display ka-welcome__hero">They’ll remember this.</h1>
        <p className="ka-welcome__lede">Characters who see, hear, remember and forget, like people do.</p>
        <div className="ka-welcome__steps">
          <StepCard n={1} title="Connect a model" active={step === 0} done={done[0]}
            teaser={<p className="ka-muted ka-small">{connected ? `Using ${rp?.effective_model}${server ? ` on ${server.name}` : ''}.` : 'A model server on this computer, or an online API.'}</p>}>
            {connected && (
              <div className="ka-found">
                <Candy icon="server" color="green" />
                <span className="ka-stack ka-stack--tight ka-grow">
                  <strong>{server?.name ?? 'Your model'}</strong>
                  <span className="ka-mono-sm">{server ? hostOf(server.base_url) : ''} · {rp?.effective_model}</span>
                </span>
                <span className="k-status">connected</span>
              </div>
            )}
            {!connected && fresh.map((f) => (
              <div key={f.base_url} className="ka-found">
                <Candy icon="server" color="green" />
                <span className="ka-stack ka-stack--tight ka-grow">
                  <strong>{f.name} on this computer</strong>
                  <span className="ka-mono-sm">{hostOf(f.base_url)}{f.models[0] ? ` · ${f.models[0]}` : ''}</span>
                </span>
                <button type="button" className="k-btn k-btn--dark" disabled={busy} onClick={() => use(f)}>
                  <Icon name="check" size={16} />
                  Use this
                </button>
              </div>
            ))}
            {!connected && (providers ?? []).length > 0 && (
              <div className="ka-stack">
                <span className="ka-small">Which model plays your characters?</span>
                <div className="ka-grid2">
                  <select className="k-select" value={pick.provider || ''} onChange={(e) => choose(Number(e.target.value))}>
                    <option value="">Server…</option>
                    {providers!.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                  <input className="k-input" list="ka-first-models" placeholder="Model" value={pick.model} disabled={!pick.provider} onChange={(e) => setPick({ ...pick, model: e.target.value })} />
                  <datalist id="ka-first-models">{pick.models.map((m) => <option key={m} value={m} />)}</datalist>
                </div>
                <button type="button" className="k-btn k-btn--dark ka-self-start" disabled={busy || !pick.provider || !pick.model.trim()}
                  onClick={() => run(async () => { await api('/roles/rp', 'PUT', { provider_id: pick.provider, model: pick.model.trim() }); refresh() })}>
                  Use this model
                </button>
              </div>
            )}
            <div className="ka-row ka-row--gap ka-welcome__look">
              <Icon name="search" size={15} />
              <span className="ka-muted ka-small ka-grow">
                {found === null ? 'Looking for model servers on this computer…' : `Looked for model servers on this computer · found ${found.length}`}
              </span>
              <button type="button" className="ka-link ka-m0" disabled={busy} onClick={look}>Look again</button>
            </div>
            <div className="ka-found ka-found--api">
              <Candy icon="globe" color="purple" />
              <span className="ka-stack ka-stack--tight ka-grow">
                <strong>Or add an online API</strong>
                <span className="ka-muted ka-small">OpenRouter and others. Keys stay in your system keychain.</span>
              </span>
              <button type="button" className="k-btn" onClick={() => setAdding((a) => ({ open: true, n: a.n + 1 }))}>
                <Icon name="plus" size={16} />
                Add an API
              </button>
            </div>
            <ErrorLine error={error} />
          </StepCard>

          <StepCard n={2} title="Make yourself" active={step === 1} done={done[1]}
            teaser={me ? (
              <div className="ka-teaser"><Avatar item={me} size={48} /><span className="ka-muted ka-small">{me.name}{me.description ? ` · ${me.description}` : ''}</span></div>
            ) : (
              <div className="ka-teaser"><Candy icon="user" color="blue" /><span className="ka-muted ka-small">{directing ? 'You direct the story.' : 'Your first persona: a name, a portrait, one line about who you are.'}</span></div>
            )}>
            {me ? (
              <div className="ka-row ka-row--gap"><Avatar item={me} size={48} /><span>You are <strong>{me.name}</strong>.</span></div>
            ) : (
              <QuickPerson persona onCreated={async (item) => {
                await api('/settings', 'PUT', { persona: item.id })
                reloadSettings()
                reloadLibrary()
                setStep(2)
              }} />
            )}
          </StepCard>

          <StepCard n={3} title="Add your first friend" active={step === 2} done={done[2]}
            teaser={<div className="ka-teaser"><Candy icon="users" color="pink" /><span className="ka-muted ka-small">Then add your first friend, and message them.</span></div>}>
            {friend ? (
              <div className="ka-stack">
                <div className="ka-row ka-row--gap"><Avatar item={friend} size={48} /><span><strong>{friend.name}</strong> is here.</span></div>
                <button type="button" className="k-btn k-btn--dark ka-self-start" onClick={() => setChat(true)}>
                  <Icon name="chat" size={16} />
                  Start a story with {friend.name}
                </button>
              </div>
            ) : (
              <QuickPerson persona={false} onCreated={(item) => {
                setFriend(item)
                reloadLibrary()
              }} />
            )}
          </StepCard>
        </div>
      </main>
      <footer className="ka-welcome__foot">
        <span className="ka-row ka-row--gap ka-small">
          <Icon name="shield" size={16} />
          Everything runs on your computer. Text only leaves it for the models you connect.
        </span>
        <button type="button" className="k-btn k-btn--dark k-btn--lg" disabled={bottom.disabled} onClick={bottom.act}>
          <Icon name={bottom.icon} size={17} />
          {bottom.label}
        </button>
      </footer>
      <AddApi key={`api-${adding.n}`} open={adding.open} onClose={() => setAdding((a) => ({ ...a, open: false }))} onAdd={addApi} busy={busy} error={error} />
      {friend && (
        <NewChat open={chat} preset={{ friends: [friend.id] }} onClose={() => setChat(false)}
          onCreated={(story) => {
            setChat(false)
            dive(`/chats/${story.id}`) // until the Scene lands (task 20), the new story waits in Chats
          }} />
      )}
    </div>
  )
}
