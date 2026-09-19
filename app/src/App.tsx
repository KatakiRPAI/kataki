import { useEffect, useState, type ReactNode } from 'react'
import { api, type Provider, type StorySummary } from './api'
import { Orb } from './art'
import clouds from './design/clouds.svg'
import { diveLink, go, href, lastSky, LibraryProvider, useLoad, useRoute } from './hooks'
import Kit from './Kit'
import Scene from './scene/Scene'
import Chats from './sky/Chats'
import Editor from './sky/Editor'
import FirstRun from './sky/FirstRun'
import Friends from './sky/Friends'
import Home from './sky/Home'
import Places from './sky/Places'
import Settings from './sky/Settings'
import You from './sky/You'
import Profile from './sky/Profile'
import { Icon } from './ui'

// The rail grows as each Sky screen lands: [route, icon, label].
const RAIL: [string, string, string][] = [
  ['home', 'home', 'Home'],
  ['friends', 'users', 'Friends'],
  ['chats', 'chat', 'Chats'],
  ['places', 'map', 'Places'],
  ['you', 'user', 'You'],
]

/** The Sky: bright glass over clouds, with the rail on the left. */
function Sky({ at, children }: { at: string; children: ReactNode }) {
  const [stories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const last = stories?.reduce<StorySummary | undefined>((a, s) => (!a || s.last_at > a.last_at ? s : a), undefined)
  return (
    <div className="k-sky ka-sky">
      <img className="ka-clouds" src={clouds} alt="" />
      <img className="ka-clouds ka-clouds--high" src={clouds} alt="" />
      <nav className="k-rail k-glass ka-rail" aria-label="Main">
        <div className="ka-logo">
          <span className="ka-logo__tile"><Icon name="cloud" size={20} /></span>
          <span className="k-display">Kataki</span>
        </div>
        {RAIL.map(([route, icon, label]) => (
          <a key={route} className="k-rail__item" href={href(`/${route}`)} aria-current={at === route ? 'page' : undefined}>
            <Icon name={icon} size={21} />
            {label}
          </a>
        ))}
        <div className="ka-grow" />
        <a className="k-rail__item ka-rail__small" href={href('/settings')} aria-current={at === 'settings' ? 'page' : undefined}>
          <Icon name="settings" size={19} />
          Settings
        </a>
        <a className="ka-rail__dive" {...diveLink(last ? `/story/${last.id}` : '/chats')} aria-label="Dive into your last scene">
          <Orb size={54} />
          <span aria-hidden="true">Dive in</span>
        </a>
      </nav>
      <main className="ka-sky__main">{children}</main>
    </div>
  )
}

/** The dive: the clouds part and the scene's dark comes up, then the page changes under it.
 *  Rising out of a scene plays it backwards: the clouds close in over the sky. */
function Dive({ to, up, onDone }: { to: string; up: boolean; onDone: () => void }) {
  const [landed, setLanded] = useState(false)
  useEffect(() => {
    const quick = matchMedia('(prefers-reduced-motion: reduce)').matches
    const arrive = setTimeout(() => {
      go(to)
      setLanded(true)
    }, quick ? 200 : 900)
    const end = setTimeout(onDone, quick ? 400 : 1200)
    return () => {
      clearTimeout(arrive)
      clearTimeout(end)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className={`ka-dive${up ? ' ka-dive--up' : ''}${landed ? ' is-landed' : ''}`} aria-hidden="true">
      <span className="ka-dive__scene" />
      <img className="ka-dive__cloud ka-dive__cloud--left" src={clouds} alt="" />
      <img className="ka-dive__cloud ka-dive__cloud--right" src={clouds} alt="" />
    </div>
  )
}

// With no model connected, everything but these sends you to First run.
const OPEN_WITHOUT_A_MODEL = ['welcome', 'settings', 'dev']

export default function App() {
  const route = useRoute()
  const [at = 'home', second, third] = route.parts
  const [model, setModel] = useState<{ path: string; has: boolean }>()
  const [diving, setDiving] = useState<{ to: string; up: boolean }>()

  // The smoke check (and later the offline card) read this instead of visible text.
  useEffect(() => {
    const mark = (state: string) => (document.documentElement.dataset.engine = state)
    api('/health').then(() => mark('ok'), () => mark('down'))
  }, [])
  // Until a model is connected, check again on every route: First run connects one, then leaves.
  // An answer counts only for the route it was asked on, so a stale "no" can't bounce you back.
  useEffect(() => {
    if (model?.has) return
    let live = true
    const answer = (has: boolean) => live && setModel({ path: route.path, has })
    api<Provider[]>('/providers').then((p) => answer(p.length > 0), () => answer(true)) // down: let pages say so
    return () => {
      live = false
    }
  }, [route.path]) // eslint-disable-line react-hooks/exhaustive-deps
  const hasModel = model?.has ? true : model?.path === route.path ? model.has : undefined
  const gated = !OPEN_WITHOUT_A_MODEL.includes(at)
  useEffect(() => {
    if (hasModel === false && gated) location.replace('#/welcome')
  }, [hasModel, gated])
  useEffect(() => {
    const onDive = (e: Event) => setDiving({ to: (e as CustomEvent<string>).detail, up: e.type === 'ka-rise' })
    addEventListener('ka-dive', onDive)
    addEventListener('ka-rise', onDive)
    return () => {
      removeEventListener('ka-dive', onDive)
      removeEventListener('ka-rise', onDive)
    }
  }, [])
  const inSky = !['story', 'dev', 'welcome'].includes(at)
  useEffect(() => {
    if (inSky) lastSky.path = location.hash.slice(1) || '/home'
  }, [inSky, route])

  const page =
    at === 'home' ? <Home />
    : at === 'friends' && second === 'new' ? <Editor key={route.path} />
    : at === 'friends' ? <Friends />
    : at === 'friend' && third === 'edit' ? <Editor key={route.path} id={Number(second)} step={Number(route.query.get('step')) || 1} />
    : at === 'friend' && !third ? <Profile key={second} id={Number(second)} />
    : at === 'you' && second === 'new' ? <Editor key={route.path} persona />
    : at === 'you' ? <You key={route.path} id={second ? Number(second) : undefined} />
    : at === 'chats' ? <Chats selected={Number(second) || undefined} />
    : at === 'places' ? <Places />
    : at === 'settings' ? <Settings page={second} />
    : <Home />
  const view =
    route.path === '/dev/kit' ? <Kit />
    : gated && hasModel !== true ? null // until we know a model is connected
    : at === 'welcome' ? (
      <LibraryProvider>
        <FirstRun />
      </LibraryProvider>
    )
    : at === 'story' ? (
      <LibraryProvider>
        <Scene key={second} id={Number(second)} line={third === 'line' ? Number(route.parts[3]) : undefined} />
      </LibraryProvider>
    )
    : (
      <LibraryProvider>
        <Sky at={at === 'friend' ? 'friends' : at === 'settings' || RAIL.some(([r]) => r === at) ? at : 'home'}>{page}</Sky>
      </LibraryProvider>
    )
  return (
    <>
      {view}
      {diving && <Dive key={diving.to} to={diving.to} up={diving.up} onDone={() => setDiving(undefined)} />}
    </>
  )
}
