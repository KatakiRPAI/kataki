// Opening (A1, A2), first run (B1–B6) and Nobody is answering (N1).
import { useEffect, useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, mediaUrl, upload, type Item, type Provider, type RoleRow, type Story, type StorySummary } from '../api'
import { isCharacter, isDraft, isPersona } from '../characters'
import { K } from '../ds'
import { face, useLibrary, useLoad } from '../hooks'
import { Overlay, toast } from '../overlay'
import { loadPrefs, pref, setPref, usePrefs } from '../prefs'
import { seedSampleWorld } from '../sample/seed'
import { t } from '../strings'

type Found = { name: string; base_url: string; models: string[] }

/** A1 / A2: the only thing on screen while the library opens, then on to the right place. */
export function Opening() {
  const navigate = useNavigate()
  const [steps, setSteps] = useState<{ library?: string; model?: string; failed?: boolean }>({})
  const [people, setPeople] = useState<number>()
  const run = async () => {
    setSteps({})
    const started = Date.now()
    try {
      const [stories, items, roles] = await Promise.all([api<StorySummary[]>('/stories'), api<Item[]>('/library'), api<RoleRow[]>('/roles'), loadPrefs()])
      const characters = items.filter(isCharacter).length
      setPeople(characters)
      setSteps((s) => ({ ...s, library: t('op.libraryDone', { lines: stories.reduce((n, x) => n + x.messages, 0), characters, stories: stories.length }) }))
      const rp = roles.find((r) => r.role === 'rp')
      setSteps((s) => ({ ...s, model: rp?.effective_model ? t('op.modelDone', { server: String(rp.effective_provider_id), model: rp.effective_model }) : t('op.modelNone') }))
      await new Promise((r) => setTimeout(r, Math.max(0, 400 - (Date.now() - started)))) // never less than 400 ms
      if (!items.length && !stories.length) return navigate('/welcome', { replace: true })
      const last = pref<string>('general.openTo', 'home') === 'last' ? [...stories].sort((a, b) => b.last_at.localeCompare(a.last_at))[0] : undefined
      navigate(last ? `/story/${last.id}` : '/home', { replace: true })
    } catch {
      setSteps({ failed: true })
    }
  }
  useEffect(() => { run() }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div data-theme="night" className="fr">
      <K.Sky />
      <main className="fr__col fr__col--narrow" aria-label={t('app.name')} style={{ paddingTop: 150 }}>
        <span className="fr__mark">{t('app.name')}</span>
        <h1 className="fr__h1">{people ? t('op.waking', { n: people }) : t('op.wakingNone')}</h1>
        <K.StepList steps={[
          { label: t('op.library'), detail: steps.failed ? t('op.failed') : steps.library ?? t('op.reading'), state: steps.failed ? 'failed' : steps.library ? 'done' : 'doing' },
          { label: t('op.memories'), detail: steps.library ? t('op.memoriesDone') : undefined, state: steps.library ? 'done' : 'wait' },
          { label: t('op.model'), detail: steps.model ?? t('op.modelWait'), state: steps.model ? 'done' : steps.library ? 'doing' : 'wait' },
        ]} />
        {steps.failed && <K.Alert title={t('op.failed')} code="LIBRARY_UNREADABLE" actions={<K.Button variant="primary" onClick={run}>{t('op.retry')}</K.Button>}>{t('op.failedBody')}</K.Alert>}
        <div className="privacy"><K.Icon name="lock" size={16} /><span>{t('op.privacy')}</span></div>
      </main>
    </div>
  )
}

function Frame({ step, children }: { step: 1 | 2; children: ReactNode }) {
  return (
    <div data-theme="night" className="fr">
      <K.Sky />
      <main className="fr__col" aria-label={t('fr.step', { n: step })}>
        <div className="row" style={{ justifyContent: 'space-between' }}><span className="fr__mark">{t('app.name')}</span><span className="t-meta">{t('fr.step', { n: step })}</span></div>
        {children}
      </main>
    </div>
  )
}

/** The first-run pages: /welcome, /welcome/server, /welcome/online, /welcome/who. */
export default function FirstRun() {
  const page = useParams()['*'] ?? ''
  if (page === 'server') return <Server />
  if (page === 'online') return <Online />
  if (page === 'who') return <Who />
  return <Doors />
}

/** B1: three doors. */
function Doors() {
  const navigate = useNavigate()
  const [found, again] = useLoad(() => api<Found[]>('/providers/detect').catch(() => []), [])
  const server = found?.[0]
  const use = async () => {
    if (!server) return
    const p = await api<Provider>('/providers', 'POST', { name: server.name, base_url: server.base_url }).catch(async () => (await api<Provider[]>('/providers')).find((x) => x.base_url === server.base_url)!)
    await api('/roles/rp', 'PUT', { provider_id: p.id, model: server.models[0], kind: 'auto', params: {} })
    navigate('/welcome/who')
  }
  const six = ['liv', 'mike', 'theo', 'nico', 'jae', 'cas'].map((who) => ({ who }))
  return (
    <Frame step={1}>
      <div className="col" style={{ gap: 12, maxWidth: 760 }}>
        <h1 className="fr__h1">{t('fr.title')}</h1>
        <p className="fr__sub">{t('fr.sub')}</p>
      </div>
      <div className="row" style={{ gap: 12, fontSize: 16, fontWeight: 600 }}><K.Icon name="shield" size={20} color="var(--ok)" /><span>{t('fr.private')}</span></div>
      <div className="fr__doors">
        <K.DoorCard icon="flame" eyebrow={t('fr.startTag')} title={t('fr.start')} actions={<K.Button variant="primary" disabled>{t('fr.start')}</K.Button>}>{t('fr.startBody')}</K.DoorCard>
        <K.DoorCard icon="server" eyebrow={server ? t('fr.serverFound') : t('fr.server')} title={t('fr.server')} recommended={!!server}
          actions={<>{server ? <K.Button variant="primary" onClick={use}>{t('fr.use')}</K.Button> : <K.Button onClick={() => navigate('/welcome/server')}>{t('fr.add')}</K.Button>}
            <K.Button variant="ghost" onClick={() => again()}>{t('fr.look')}</K.Button></>}>
          {server ? t('fr.serverFoundBody', { server: server.name, model: server.models[0] ?? '' }) : t('fr.serverNone')}
        </K.DoorCard>
        <K.DoorCard icon="globe" eyebrow={t('fr.onlineTag')} title={t('fr.online')} actions={<K.Button onClick={() => navigate('/welcome/online')}>{t('fr.addKey')}</K.Button>}>{t('fr.onlineBody')}</K.DoorCard>
      </div>
      <div className="row" style={{ justifyContent: 'space-between', paddingTop: 8 }}>
        <div className="row" style={{ gap: 10 }}>
          <K.AvatarStack people={six} size={30} max={6} label={t('fr.sixLabel')} />
          <span style={{ fontSize: 14, color: 'var(--mid)' }}>{t('fr.six')}</span>
        </div>
        <div className="row" style={{ gap: 14 }}>
          <span className="t-faint">{t('fr.later')}</span>
          <K.Button variant="ghost" onClick={() => navigate('/welcome/who')}>{t('fr.skip')}</K.Button>
        </div>
      </div>
    </Frame>
  )
}

/** B3: a server by address, tested before it's used. */
function Server() {
  const navigate = useNavigate()
  const [address, setAddress] = useState('http://127.0.0.1:8080/v1')
  const [key, setKey] = useState('')
  const [state, setState] = useState<{ tone: 'ok' | 'warm' | 'bad'; title: string; body?: string; provider?: Provider; model?: string } | null>(null)
  const test = async () => {
    setState({ tone: 'warm', title: t('fr.testing', { address }) })
    let p: Provider | undefined
    try {
      p = await api<Provider>('/providers', 'POST', { name: new URL(address).host, base_url: address.trim(), api_key: key.trim() || null })
      const { models } = await api<{ models: string[] }>(`/providers/${p.id}/models`)
      setState(models.length ? { tone: 'ok', title: t('fr.connected'), body: t('fr.connectedBody', { n: models.length, model: models[0] }), provider: p, model: models[0] }
        : { tone: 'warm', title: t('fr.noModel'), provider: p })
    } catch {
      if (p) await api(`/providers/${p.id}`, 'DELETE').catch(() => {})
      setState({ tone: 'bad', title: t('fr.nothing'), body: t('fr.nothingBody', { address }) })
    }
  }
  const go = async () => {
    if (!state?.provider || !state.model) return
    await api('/roles/rp', 'PUT', { provider_id: state.provider.id, model: state.model, kind: 'auto', params: {} })
    navigate('/welcome/who')
  }
  return (
    <Frame step={1}>
      <h1 className="fr__h1">{t('fr.srvTitle')}</h1>
      <div className="card card--pad col" style={{ gap: 16, maxWidth: 640 }}>
        <K.TextField label={t('fr.address')} value={address} onChange={setAddress} error={state?.tone === 'bad' ? state.body : undefined} />
        <K.TextField label={t('fr.key')} optional type="password" hint={t('fr.keyHint')} value={key} onChange={setKey} />
        {state && <K.StatusLine tone={state.tone} title={state.title}>{state.tone !== 'bad' ? state.body : undefined}</K.StatusLine>}
        <div className="row" style={{ gap: 8 }}>
          <K.Button variant="ghost" onClick={() => navigate('/welcome')}>{t('fr.back')}</K.Button>
          <K.Button onClick={test}>{t('fr.test')}</K.Button>
          <K.Button variant="primary" disabled={state?.tone !== 'ok'} onClick={go}>{t('fr.useServer')}</K.Button>
        </div>
      </div>
    </Frame>
  )
}

const SERVICES: [string, string, string][] = [['OpenRouter', 'api.openrouter', 'https://openrouter.ai/api/v1'], ['OpenAI', 'api.openai', 'https://api.openai.com/v1'], ['Anthropic', 'api.anthropic', 'https://api.anthropic.com/v1'], ['Other', 'api.other', '']]

/** B4: an online model by key. */
function Online() {
  const navigate = useNavigate()
  const [service, setService] = useState('OpenRouter')
  const [address, setAddress] = useState('')
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const url = service === 'Other' ? address.trim() : SERVICES.find(([s]) => s === service)![2]
  const go = async () => {
    setBusy(true)
    setError('')
    let p: Provider | undefined
    try {
      p = await api<Provider>('/providers', 'POST', { name: service === 'Other' ? new URL(url).host : service, base_url: url, api_key: key.trim() })
      const { models } = await api<{ models: string[] }>(`/providers/${p.id}/models`)
      await api('/roles/rp', 'PUT', { provider_id: p.id, model: models[0], kind: 'auto', params: {} })
      navigate('/welcome/who')
    } catch (e) {
      if (p) await api(`/providers/${p.id}`, 'DELETE').catch(() => {})
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Frame step={1}>
      <h1 className="fr__h1">{t('fr.onTitle')}</h1>
      <div className="card card--pad col" style={{ gap: 16, maxWidth: 640 }}>
        <K.RadioGroup value={service} onChange={setService} options={SERVICES.map(([v, l]) => ({ value: v, label: t(l as 'api.openrouter') }))} />
        {service === 'Other' && <K.TextField label={t('api.address')} value={address} onChange={setAddress} placeholder="https://…/v1" />}
        <K.TextField label={t('api.key')} type="password" hint={t('api.keyHint')} value={key} onChange={setKey} error={error ? `${t('api.bad')} · ${error}` : undefined} />
        <K.Callout tone="warm" icon="globe" title={t('api.privacy')}>{t('api.privacyBody')}</K.Callout>
        <div className="row" style={{ gap: 8 }}>
          <K.Button variant="ghost" onClick={() => navigate('/welcome')}>{t('fr.back')}</K.Button>
          <K.Button variant="primary" loading={busy} disabled={!key.trim() || !url} onClick={go}>{t('fr.testContinue')}</K.Button>
        </div>
      </div>
    </Frame>
  )
}

/** B5, B6: who to meet first, and who you are. */
function Who() {
  const navigate = useNavigate()
  const { items, reload } = useLibrary()
  const [prefs] = usePrefs()
  const [seeding, setSeeding] = useState(false)
  const [picked, setPicked] = useState<number>()
  const [persona, setPersona] = useState(false)
  useEffect(() => {
    if (seeding || items.length) return
    setSeeding(true)
    seedSampleWorld().then(() => { reload(); loadPrefs() }).finally(() => setSeeding(false))
  }, [items.length]) // eslint-disable-line react-hooks/exhaustive-deps
  const people = items.filter(isCharacter).slice(0, 6)
  const chosen = people.find((c) => c.id === picked) ?? people.find((c) => c.name === 'Mike') ?? people[0]
  const me = typeof prefs.persona === 'number' ? items.find((i) => i.id === prefs.persona) : items.find(isPersona)
  const start = async () => {
    if (!chosen) return
    const place = chosen.data.places?.[0]
    const at = place ? items.find((i) => i.id === place) : undefined
    const story = await api<Story>('/stories', 'POST', {
      title: `${at?.name ?? chosen.name} · ${new Date().toLocaleDateString('en-GB', { weekday: 'long' })}`,
      character_ids: [chosen.id], place_id: place ?? null, persona_id: me?.id ?? null,
    })
    navigate(`/story/${story.id}`, { replace: true })
  }
  return (
    <Frame step={2}>
      <div className="col" style={{ gap: 12 }}><h1 className="fr__h1">{t('fr.who')}</h1><p className="fr__sub">{t('fr.whoSub')}</p></div>
      {seeding && !people.length ? <K.Spinner label={t('fr.seeding')} /> : (
        <div className="fr__who" role="radiogroup" aria-label={t('fr.who')}
          onKeyDown={(e) => {
            const i = people.findIndex((c) => c.id === chosen?.id)
            const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]
            if (d) { e.preventDefault(); setPicked(people[(i + d + people.length) % people.length].id) }
            if (e.key === 'Enter') start()
          }}>
          {people.map((c) => (
            <button key={c.id} type="button" role="radio" aria-checked={c.id === chosen?.id} tabIndex={c.id === chosen?.id ? 0 : -1} className="fr__pick" onClick={() => setPicked(c.id)}>
              <K.CharacterCard {...face(c)} focus={c.data.focus} name={c.name} line={c.data.tagline} when={isDraft(c) ? t('fr.draftLine') : ''} badge={isDraft(c) ? t('fr.draft') : undefined} />
            </button>
          ))}
        </div>
      )}
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="row" style={{ gap: 10 }}>
          <span className="t-meta">{t('fr.youAre')}</span>
          {me && <><K.Avatar {...face(me)} size={30} /><b>{me.name}</b></>}
          <K.Button size="sm" variant="ghost" onClick={() => setPersona(true)}>{t('fr.change')}</K.Button>
        </div>
        <div className="row" style={{ gap: 12 }}>
          <K.Button variant="ghost" onClick={() => navigate('/welcome')}>{t('fr.back')}</K.Button>
          <K.Button variant="ghost" onClick={() => navigate('/home', { replace: true })}>{t('fr.empty')}</K.Button>
          <K.Button variant="primary" size="lg" disabled={!chosen} onClick={start}>{t('fr.startWith', { name: chosen?.name ?? '' })}</K.Button>
        </div>
      </div>
      {persona && <Persona me={me} onClose={() => setPersona(false)} onDone={reload} />}
    </Frame>
  )
}

/** B6: who you are in these stories. */
function Persona({ me, onClose, onDone }: { me?: Item; onClose: () => void; onDone: () => void }) {
  const [name, setName] = useState(me?.name ?? '')
  const [who, setWho] = useState(me?.description ?? '')
  const [portrait, setPortrait] = useState(me?.data.portrait)
  const [justYou, setJustYou] = useState(false)
  const save = async () => {
    if (justYou) { await setPref('persona', null); onClose(); return }
    const body = { name: name.trim(), description: who.trim(), data: { ...(me?.data ?? {}), persona: true, portrait } }
    const saved = me ? await api<Item>(`/library/${me.id}`, 'PATCH', body) : await api<Item>('/library', 'POST', { kind: 'character', ...body })
    await setPref('persona', saved.id)
    onDone()
    onClose()
    toast(t('set.saved'), {}, 2000)
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="user" title={t('fr.personaTitle')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>, <K.Button key="s" variant="primary" disabled={!justYou && !name.trim()} onClick={save}>{t('fr.save')}</K.Button>]}>
        <div className="row" style={{ gap: 14 }}>
          <K.Avatar src={portrait ? mediaUrl(portrait) : undefined} {...(me && !portrait ? face(me) : {})} name={name || '?'} size={56} />
          <div className="col" style={{ gap: 6 }}>
            <label className="k-btn k-btn--secondary k-btn--sm" style={{ alignSelf: 'flex-start' }}>{t('fr.pic')}<input type="file" accept="image/png,image/jpeg,image/webp" hidden disabled={justYou} onChange={async (e) => { const f = e.target.files?.[0]; if (f) setPortrait((await upload(f)).name) }} /></label>
            <span className="t-faint">{t('fr.picHint')}</span>
          </div>
        </div>
        <K.TextField label={t('fr.name')} required story disabled={justYou} value={name} onChange={setName} />
        <K.TextArea label={t('fr.whoYou')} rows={2} story disabled={justYou} value={who} onChange={setWho} />
        <K.Checkbox label={t('fr.justYou')} checked={justYou} onChange={setJustYou} />
      </K.Dialog>
    </Overlay>
  )
}

/** N1: the model stopped answering. Tries again every 10 s and goes back when it answers. */
export function ModelGone() {
  const navigate = useNavigate()
  const [left, setLeft] = useState(10)
  useEffect(() => {
    const tick = setInterval(() => setLeft((s) => (s <= 1 ? 10 : s - 1)), 1000)
    return () => clearInterval(tick)
  }, [])
  const check = async () => {
    const roles = await api<RoleRow[]>('/roles')
    const rp = roles.find((r) => r.role === 'rp')
    if (!rp?.effective_provider_id) return false
    try {
      await api(`/providers/${rp.effective_provider_id}/models`)
      toast(t('toast.modelBack'), {}, 4000)
      navigate(-1)
      return true
    } catch { return false }
  }
  useEffect(() => { if (left === 10) check() }, [left]) // eslint-disable-line react-hooks/exhaustive-deps
  const causes: [string, string][] = [['mg.c1', 'mg.c1Body'], ['mg.c2', 'mg.c2Body'], ['mg.c3', 'mg.c3Body'], ['mg.c4', 'mg.c4Body']]
  return (
    <main className="app__main" aria-label={t('mg.title')} style={{ gap: 24 }}>
      <K.Alert title={t('mg.title')} code="MODEL_GONE" actions={<>
        <K.Button variant="primary" onClick={check}>{t('mg.retry')}</K.Button>
        <K.Button href="/settings/models">{t('mg.settings')}</K.Button>
      </>}>{t('mg.body')}</K.Alert>
      <span className="t-meta">{t('mg.live', { s: left })}</span>
      <section className="sec"><h2 className="sec-title">{t('mg.works')}</h2>
        <div className="row" style={{ gap: 14, alignItems: 'stretch' }}>
          {([['mg.read', 'mg.readBody'], ['mg.write', 'mg.writeBody'], ['mg.export', 'mg.exportBody']] as const).map(([a, b]) => <K.Callout key={a} tone="ok" title={t(a)}>{t(b)}</K.Callout>)}
        </div>
      </section>
      <section className="sec"><h2 className="sec-title">{t('mg.causes')}</h2>
        <div className="col" style={{ gap: 10 }}>{causes.map(([a, b]) => <K.Callout key={a} title={t(a as 'mg.c1')}>{t(b as 'mg.c1Body')}</K.Callout>)}</div>
      </section>
    </main>
  )
}
