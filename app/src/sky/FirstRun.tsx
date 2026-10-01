// Opening (A1, A2), first run (B1–B6) and Nobody is answering (N1).
import { useEffect, useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router'
import { api, mediaUrl, upload, type Item, type Provider, type RoleRow, type Story, type StorySummary } from '../api'
import { byShipped, isCharacter, isDraft, isPersona } from '../characters'
import { K } from '../ds'
import { face, useLibrary, useLoad } from '../hooks'
import { Overlay, toast } from '../overlay'
import { loadPrefs, pref, setPref, skyTheme, usePrefs } from '../prefs'
import { seedSampleWorld } from '../sample/seed'
import { t, type Key } from '../strings'
import { ImportCards } from './Characters'
import { Crop, type Picture } from './Crop'
import { openFeedback } from './Feedback'
import { ModelPicker } from './ModelPicker'
import Top from './Top'
import { classify, err } from '../errors'

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
      // after a crash Kataki goes to Home first either way (A3)
      const last = pref<string>('general.openTo', 'home') === 'last' && !window.kataki?.crashed ?[...stories].sort((a, b) => b.last_at.localeCompare(a.last_at))[0] : undefined
      navigate(last ? `/story/${last.id}` : '/home', { replace: true })
    } catch {
      setSteps({ failed: true })
    }
  }
  useEffect(() => { run() }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div data-theme={skyTheme(usePrefs()[0])} className="fr">
      <K.Sky />
      <main className="fr__col fr__col--narrow" aria-label={t('app.name')} style={{ paddingTop: 150 }}>
        <span className="fr__mark">{t('app.name')}</span>
        <h1 className="fr__h1">{people ? t('op.waking', { n: people }) : t('op.wakingNone')}</h1>
        <K.StepList steps={[
          { label: t('op.library'), detail: steps.failed ? t('op.failed') : steps.library ?? t('op.reading'), state: steps.failed ? 'failed' : steps.library ? 'done' : 'doing' },
          { label: t('op.memories'), detail: steps.library ? t('op.memoriesDone') : undefined, state: steps.library ? 'done' : 'wait' },
          { label: t('op.model'), detail: steps.model ?? t('op.modelWait'), state: steps.model ? 'done' : steps.library ? 'doing' : 'wait' },
        ]} />
        {steps.failed && <K.Alert title={t('op.failed')} code="LIBRARY_UNREADABLE" actions={<K.Button variant="primary" onClick={run}>{t('op.retry')}</K.Button>}>{err('LIBRARY_UNREADABLE', { file: 'library.db', folder: 'the library folder' }).body}</K.Alert>}
        <div className="privacy"><K.Icon name="lock" size={16} /><span>{t('op.privacy')}</span></div>
      </main>
    </div>
  )
}

function Frame({ step, gap, children }: { step: 1 | 2; gap?: number; children: ReactNode }) {
  return (
    <div data-theme={skyTheme(usePrefs()[0])} className="fr">
      <K.Sky />
      <main className="fr__col" style={gap ? { gap } : undefined} aria-label={t('fr.step', { n: step })}>
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
  const { items, reload } = useLibrary()
  const [importing, setImporting] = useState(false) // cards come in here and the doors stay; setup isn't skipped
  const server = found?.[0]
  const use = async () => {
    if (!server) return
    const p = await api<Provider>('/providers', 'POST', { name: server.name, base_url: server.base_url }).catch(async () => (await api<Provider[]>('/providers')).find((x) => x.base_url === server.base_url)!)
    await api('/roles/rp', 'PUT', { provider_id: p.id, model: server.models[0], kind: 'auto', params: {} })
    navigate('/welcome/who')
  }
  const six = [...['mike', 'theo', 'nico', 'jae', 'cas'].map((who) => ({ who })), { who: 'dani', name: 'Dani' }]
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
          <K.Button variant="link" icon="download" onClick={() => setImporting(true)}>{t('fr.import')}</K.Button>
        </div>
        <div className="row" style={{ gap: 14 }}>
          <span className="t-faint">{t('fr.later')}</span>
          <K.Button variant="ghost" onClick={() => navigate('/welcome/who')}>{t('fr.skip')}</K.Button>
        </div>
      </div>
      {importing && <ImportCards names={items.map((i) => i.name)} onClose={() => setImporting(false)} onDone={reload} byName={(n) => items.find((i) => i.name.toLowerCase() === n.toLowerCase())} />}
    </Frame>
  )
}

/** B3, B4: one card on the left, where the test's answer shows in place (the board's right-hand
 *  column only lists the answers, so it stays empty here and keeps the card its width). */
function Form({ icon, title, children }: { icon: 'server' | 'globe'; title: string; children: ReactNode }) {
  return (
    <Frame step={1} gap={28}>
      <K.TextLink href="/welcome" icon="left">{t('fr.doors')}</K.TextLink>
      <div className="fr__form">
        <section className="card fr__card" aria-label={title}>
          <div className="row" style={{ gap: 14 }}>
            <span className="dlg__icon"><K.Icon name={icon} size={20} /></span>
            <h1 className="fr__h2">{title}</h1>
          </div>
          {children}
        </section>
      </div>
    </Frame>
  )
}

type Tested = { tone: 'ok' | 'warm' | 'bad'; title: string; body?: string; provider?: Provider; model?: string; testing?: boolean }
const KINDS = ['auto', 'llama.cpp', 'Ollama', 'LM Studio', 'KoboldCpp', 'text-generation-webui', 'other'] as const

/** B3: a server by address, tested before it's used. */
function Server() {
  const navigate = useNavigate()
  const [found, again] = useLoad(() => api<Found[]>('/providers/detect').catch(() => []), [])
  const [address, setAddress] = useState('http://127.0.0.1:8080/v1')
  const [kind, setKind] = useState<string>('auto')
  const [key, setKey] = useState('')
  const [state, setState] = useState<Tested | null>(null)
  const kindLabel = (k: string) => (k === 'auto' ? t('fr.kind.auto') : k === 'other' ? t('fr.kind.other') : k)
  const test = async () => {
    setState({ tone: 'ok', title: t('fr.testing', { address: address.replace(/^https?:\/\//, '').replace(/\/v1\/?$/, '') }), body: t('fr.testingBody'), testing: true })
    let p: Provider | undefined
    try {
      p = await api<Provider>('/providers', 'POST', { name: kind === 'auto' || kind === 'other' ? new URL(address).host : kind, base_url: address.trim(), api_key: key.trim() || null })
      const { models } = await api<{ models: string[] }>(`/providers/${p.id}/models`)
      setState(models.length ? { tone: 'ok', title: t('fr.connected'), body: t('fr.connectedBody', { n: models.length, model: models[0] }), provider: p, model: models[0] }
        : { tone: 'warm', title: err('SERVER_NO_MODEL').title, body: err('SERVER_NO_MODEL', { server: p.name }).body, provider: p })
    } catch (e) {
      if (p) await api(`/providers/${p.id}`, 'DELETE').catch(() => {})
      const code = classify((e as Error).message)
      const shown = code === 'SERVER_UNAUTHORIZED' || code === 'SERVER_NOT_COMPATIBLE' ? code : 'SERVER_UNREACHABLE'
      setState({ tone: 'bad', title: err(shown).title, body: err(shown, { address, seconds: 5 }).body })
    }
  }
  const go = async () => {
    if (!state?.provider || !state.model) return
    await api('/roles/rp', 'PUT', { provider_id: state.provider.id, model: state.model, kind: 'auto', params: {} })
    navigate('/welcome/who')
  }
  const unreachable = state?.tone === 'bad' && state.title === err('SERVER_UNREACHABLE').title
  return (
    <Form icon="server" title={t('fr.server')}>
      {found && (found.length
        ? <K.StatusLine title={t('fr.serverFound')}>{t('fr.serverFoundBody', { server: found[0].name, model: found[0].models[0] ?? '' })}</K.StatusLine>
        : <K.StatusLine tone="warm" title={t('fr.srvNone')}>{t('fr.srvNoneBody')}</K.StatusLine>)}
      <div className="fr__test">
        <K.TextField label={t('fr.address')} icon="link" value={address} onChange={setAddress} error={unreachable ? state!.body : undefined} />
        <div style={{ paddingBottom: 26 }}><K.Button onClick={test} loading={state?.testing}>{t('fr.test')}</K.Button></div>
      </div>
      {state && !unreachable && !state.testing && <K.StatusLine tone={state.tone} title={state.title}>{state.body}</K.StatusLine>}
      {state?.testing && <K.StatusLine title={state.title}><span className="row" style={{ gap: 8 }}><K.Spinner size={14} />{state.body}</span></K.StatusLine>}
      {state?.provider && state.model && <ModelPicker label={t('fr.model')} job="rp" providers={[state.provider]} value={{ provider_id: state.provider.id, model: state.model }} onChange={(v) => v && setState({ ...state, model: v.model })} />}
      <K.Select label={t('fr.kind')} options={KINDS.map(kindLabel)} value={kindLabel(kind)} onChange={(v) => setKind(KINDS.find((k) => kindLabel(k) === v) ?? 'auto')} hint={t('fr.kindHint')} />
      <K.TextField label={t('fr.key')} optional type="password" icon="key" placeholder={t('fr.keyPlaceholder')} hint={t('fr.keyHint')} value={key} onChange={setKey} />
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <K.Button variant="ghost" icon="refresh" onClick={() => again()}>{t('fr.look')}</K.Button>
        <K.Button variant="primary" disabled={state?.tone !== 'ok' || !state.model} onClick={go}>{t('fr.useServer')}</K.Button>
      </div>
    </Form>
  )
}

const SERVICES: [string, string, string][] = [['OpenRouter', 'api.openrouter', 'https://openrouter.ai/api/v1'], ['OpenAI', 'api.openai', 'https://api.openai.com/v1'], ['Anthropic', 'api.anthropic', 'https://api.anthropic.com/v1'], ['Other', 'fr.otherService', '']]
const KEYCHAIN = /Win/.test(navigator.userAgent) ? 'win' : /Mac/.test(navigator.userAgent) ? 'mac' : 'other'

/** B4: an online model by key. */
function Online() {
  const navigate = useNavigate()
  const [service, setService] = useState('OpenRouter')
  const [address, setAddress] = useState('')
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [made, setMade] = useState<{ provider: Provider; model: string; n: number }>()
  const url = service === 'Other' ? address.trim() : SERVICES.find(([s]) => s === service)![2]
  // a different service, address or key is a different connection: the tested one goes
  const changed = (set: (v: string) => void) => (v: string) => { if (made) api(`/providers/${made.provider.id}`, 'DELETE').catch(() => {}); setMade(undefined); set(v) }
  const go = async () => {
    if (made) {
      await api('/roles/rp', 'PUT', { provider_id: made.provider.id, model: made.model, kind: 'auto', params: {} })
      return navigate('/welcome/who')
    }
    setBusy(true)
    setError('')
    let p: Provider | undefined
    try {
      p = await api<Provider>('/providers', 'POST', { name: service === 'Other' ? new URL(url).host : service, base_url: url, api_key: key.trim() })
      const { models } = await api<{ models: string[] }>(`/providers/${p.id}/models`)
      await api('/roles/rp', 'PUT', { provider_id: p.id, model: models[0], kind: 'auto', params: {} }) // a first pick, so going on works even if the list is left alone
      setMade({ provider: p, model: models[0], n: models.length })
    } catch (e) {
      if (p) await api(`/providers/${p.id}`, 'DELETE').catch(() => {})
      setError(err(classify((e as Error).message, true), { service: service === 'Other' ? t('fr.otherService') : service }).body)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Form icon="globe" title={t('fr.online')}>
      <K.Callout tone="warm" title={t('api.privacy')}>{t('fr.onPrivacy')}</K.Callout>
      <K.RadioGroup label={t('api.service')} value={service} onChange={changed(setService)}
        options={SERVICES.map(([v, l]) => ({ value: v, label: t(l as 'api.openrouter'), description: v === 'OpenRouter' ? t('fr.openrouterSub') : v === 'Other' ? t('fr.otherSub') : undefined }))} />
      {service === 'Other' && <K.TextField label={t('api.address')} icon="link" value={address} onChange={changed(setAddress)} placeholder="https://…/v1" />}
      <K.TextField label={t('api.key')} required type="password" icon="key" value={key} onChange={changed(setKey)} error={error || undefined} />
      {made ? (
        <>
          <K.StatusLine tone="ok" title={t('fr.keyWorks')}>{t('fr.keyWorksBody', { n: made.n })}</K.StatusLine>
          <ModelPicker label={t('fr.model')} hint={t('fr.modelHint')} job="rp" providers={[made.provider]} value={{ provider_id: made.provider.id, model: made.model }} onChange={(v) => v && setMade({ ...made, model: v.model })} />
        </>
      ) : <K.Select label={t('fr.model')} options={[t('fr.modelWait')]} hint={t('fr.modelHint')} disabled />}
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="t-faint">{t('fr.keyStored', { os: KEYCHAIN })}</span>
        <K.Button variant="primary" loading={busy} disabled={!key.trim() || !url} onClick={go}>{t(made ? 'fr.continue' : 'fr.testContinue')}</K.Button>
      </div>
    </Form>
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
  const me = typeof prefs.persona === 'number' ? items.find((i) => i.id === prefs.persona) : items.find(isPersona)
  const people = items.filter((i) => i.kind === 'character' && i.id !== me?.id)
    .sort(byShipped).slice(0, 6)
  const chosen = people.find((c) => c.id === picked) ?? people.find((c) => c.name === 'Mike') ?? people[0]
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
    <Frame step={2} gap={26}>
      <div className="col" style={{ gap: 10 }}><h1 className="fr__h1 fr__h1--who">{t('fr.who')}</h1><p className="fr__sub fr__sub--who">{t('fr.whoSub')}</p></div>
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
              <K.CharacterCard {...face(c)} focus={c.data.focus} name={c.name} line={c.data.tagline}
                when={isDraft(c) ? t('fr.draftLine') : c.data.source === 'shipped' ? t('fr.ships') : ''} badge={isDraft(c) ? t('fr.draft') : undefined} />
            </button>
          ))}
        </div>
      )}
      <div className="card fr__you">
        <span className="t-faint" style={{ width: 90 }}>{t('fr.youAre')}</span>
        {me ? <K.Avatar {...face(me)} size={40} /> : <K.Avatar name="?" size={40} />}
        <div style={{ flex: 1 }}>
          <div className="fr__youName">{me ? (me.data.aliases?.[0] ?? me.name) : t('fr.justYouName')}</div>
          <div className="t-meta">{t('fr.orYou')}</div>
        </div>
        <K.Button size="sm" onClick={() => setPersona(true)}>{t('fr.change')}</K.Button>
      </div>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <K.Button variant="ghost" icon="left" onClick={() => navigate('/welcome')}>{t('fr.back')}</K.Button>
        <div className="row" style={{ gap: 16 }}>
          <K.Button variant="link" onClick={() => navigate('/home', { replace: true })}>{t('fr.empty')}</K.Button>
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
  const [pic, setPic] = useState<Picture>({ portrait: me?.data.portrait, focus: me?.data.focus, zoom: me?.data.zoom, alt: me?.data.alt })
  const [cropping, setCropping] = useState<string>() // a media name
  const [justYou, setJustYou] = useState(false)
  const save = async () => {
    if (justYou) { await setPref('persona', null); onClose(); return }
    const body = { name: name.trim(), description: who.trim(), data: { ...(me?.data ?? {}), persona: true, ...pic } }
    const saved = me ? await api<Item>(`/library/${me.id}`, 'PATCH', body) : await api<Item>('/library', 'POST', { kind: 'character', ...body })
    await setPref('persona', saved.id)
    onDone()
    onClose()
    toast(t('set.saved'), {}, 2000)
  }
  if (cropping) return <Crop src={mediaUrl(cropping)} {...(cropping === pic.portrait ? pic : {})} name={name} onClose={() => setCropping(undefined)} onUse={(focus, zoom, alt) => { setPic({ portrait: cropping, focus, zoom, alt }); setCropping(undefined) }} />
  const { portrait } = pic
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="user" title={t('fr.personaTitle')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>, <K.Button key="s" variant="primary" disabled={!justYou && !name.trim()} onClick={save}>{t('fr.save')}</K.Button>]}>
        <div className="row" style={{ gap: 14 }}>
          <K.Avatar src={portrait ? mediaUrl(portrait) : undefined} {...(me && !portrait ? face(me) : {})} focus={pic.focus} zoom={pic.zoom} name={name || '?'} size={56} />
          <div className="col" style={{ gap: 6 }}>
            <label className="k-btn k-btn--secondary k-btn--sm" style={{ alignSelf: 'flex-start' }}>{t('fr.pic')}<input type="file" accept="image/png,image/jpeg,image/webp" hidden disabled={justYou} onChange={async (e) => { const f = e.target.files?.[0]; if (f) setCropping((await upload(f)).name) }} /></label>
            {portrait && !justYou && <K.Button size="sm" variant="ghost" onClick={() => setCropping(portrait)}>{t('ed.cropFocus')}</K.Button>}
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
  const [server] = useLoad(async () => {
    const [roles, providers] = await Promise.all([api<RoleRow[]>('/roles'), api<Provider[]>('/providers')])
    const rp = roles.find((r) => r.role === 'rp')
    return { rp, provider: providers.find((p) => p.id === rp?.effective_provider_id) }
  }, [])
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
      toast(t('toast.modelBack'), { icon: 'check' }, 4000)
      navigate(-1)
      return true
    } catch { return false }
  }
  useEffect(() => { if (left === 10) check() }, [left]) // eslint-disable-line react-hooks/exhaustive-deps
  const p = server?.provider
  const host = p ? (() => { try { return new URL(p.base_url).host } catch { return p.base_url } })() : ''
  const local = /^(localhost|127\.0\.0\.1|\[::1\])(:|$)/.test(host)
  const name = p?.name ?? t('mg.theServer')
  // the facts in bold, as the board has them
  const facts = { server: '\u0001server', where: local ? t('mg.here') : '', address: '\u0001address', ago: '\u0001ago' }
  const shown: Record<string, string> = { server: name, address: host || t('mg.itsAddress'), ago: t('mg.agoNow') }
  const body = err('MODEL_GONE', facts).body.replace(/\s+/g, ' ').split(/(\u0001\w+)/).map((part, i) => (part.startsWith('\u0001') ? <b key={i}>{shown[part.slice(1)]}</b> : part))
  const causes: [Key, Key, ReactNode?][] = [
    ['mg.c1', 'mg.c1Body'], ['mg.c2', 'mg.c2Body'], ['mg.c3', 'mg.c3Body'],
    ['mg.c4', 'mg.c4Body', <K.Button key="f" size="sm" href="/settings/models">{t('mg.look')}</K.Button>],
  ]
  return (
    <main className="app__main" aria-label={t('mg.label')} style={{ gap: 24, maxWidth: 980 }}>
      <Top />
      <K.Alert title={err('MODEL_GONE').title} code="MODEL_GONE" icon="server" actions={<>
        <K.Button variant="primary" icon="refresh" onClick={check}>{t('mg.retry')}</K.Button>
        <K.Button href="/settings/models">{t('mg.settings')}</K.Button>
      </>}>{body}</K.Alert>
      <div className="row" style={{ gap: 10 }} role="status" aria-live="polite"><K.Spinner size={14} /><span className="t-meta">{t('mg.live', { s: left })}</span></div>
      <section className="sec" aria-labelledby="mg-works">
        <div className="sec-head"><h2 className="sec-title" id="mg-works">{t('mg.works')}</h2></div>
        <div className="mg-works">
          {([['book', 'mg.read', 'mg.readBody'], ['edit', 'mg.write', 'mg.writeBody'], ['download', 'mg.export', 'mg.exportBody']] as const).map(([icon, a, b]) => <K.Callout key={a} tone="ok" icon={icon} title={t(a)}>{t(b)}</K.Callout>)}
        </div>
      </section>
      <section className="sec" aria-labelledby="mg-causes">
        <div className="sec-head"><h2 className="sec-title" id="mg-causes">{t('mg.causes')}</h2></div>
        <div className="card">
          {causes.map(([a, b, act]) => <div key={a} className="mg-cause"><b>{t(a)}</b><span className="t-body">{t(b, { server: name, model: server?.rp?.effective_model ?? '' })}</span>{act ?? <span />}</div>)}
        </div>
      </section>
      <div className="row" style={{ gap: 10 }}><span className="t-meta">{t('mg.stuck')}</span><span onClick={() => openFeedback('bug')}><K.TextLink icon="help">{t('mg.report')}</K.TextLink></span></div>
    </main>
  )
}
