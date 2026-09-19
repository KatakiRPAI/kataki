import { useEffect, type ReactNode } from 'react'
import { api } from './api'
import { Orb } from './art'
import Classic from './classic/Classic'
import clouds from './design/clouds.svg'
import { href, LibraryProvider, useRoute } from './hooks'
import Kit from './Kit'
import Friends from './sky/Friends'
import { Icon } from './ui'

// The rail grows as each Sky screen lands: [route, icon, label].
const RAIL: [string, string, string][] = [['friends', 'users', 'Friends']]

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
        {/* until Settings lands (task 14), the classic Models page */}
        <a className="k-rail__item ka-rail__small" href={href('/classic')}>
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
  if (at === 'friends')
    return (
      <LibraryProvider>
        <Sky at={at}>
          <Friends />
        </Sky>
      </LibraryProvider>
    )
  return (
    <div className="classic">
      <Classic />
    </div>
  )
}
