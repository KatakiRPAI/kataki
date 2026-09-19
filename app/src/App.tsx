import { useEffect, type ReactNode } from 'react'
import { api } from './api'
import { Orb } from './art'
import Classic from './classic/Classic'
import clouds from './design/clouds.svg'
import { href, LibraryProvider, useRoute } from './hooks'
import Kit from './Kit'
import Chats from './sky/Chats'
import Editor from './sky/Editor'
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
        {/* until the Scene lands (task 20), stories open in the classic view */}
        <a className="ka-rail__dive" href={href('/classic')} aria-label="Dive into your last scene">
          <Orb size={54} />
          <span aria-hidden="true">Dive in</span>
        </a>
      </nav>
      <main className="ka-sky__main">{children}</main>
    </div>
  )
}

export default function App() {
  const route = useRoute()
  const [at] = route.parts

  // The smoke check (and later the offline card) read this instead of visible text.
  useEffect(() => {
    const mark = (state: string) => (document.documentElement.dataset.engine = state)
    api('/health').then(() => mark('ok'), () => mark('down'))
  }, [])

  if (route.path === '/dev/kit') return <Kit />
  const [, second, third] = route.parts
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
    : null
  if (page)
    return (
      <LibraryProvider>
        <Sky at={at === 'friend' ? 'friends' : at}>{page}</Sky>
      </LibraryProvider>
    )
  return (
    <div className="classic">
      <Classic />
    </div>
  )
}
