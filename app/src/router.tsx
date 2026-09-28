// Routes (docs/handoff/kataki-handoff/ROUTES.md). One route table for both hosts: a memory router
// in the desktop app, the browser's own history on the web. Overlays are state, never routes.
import { useEffect, useState, type ReactNode } from 'react'
import { createBrowserRouter, createMemoryRouter, Outlet, useLocation, useNavigate, type RouteObject } from 'react-router'
import { api } from './api'
import { K } from './ds'
import { LibraryProvider } from './hooks'
import { Toasts } from './overlay'
import { t } from './strings'
import Home from './sky/Home'
import NotBuilt from './sky/NotBuilt'
import Stories from './sky/Stories'
import NewStory from './sky/NewStory'
import Scene from './scene/Scene'

const RAIL: Record<string, string> = {
  Home: '/home', Stories: '/stories', Characters: '/characters', World: '/world', You: '/you',
  'New character': '/characters/new', Settings: '/settings/general',
}
const ACTIVE: Record<string, string> = { home: 'Home', stories: 'Stories', characters: 'Characters', world: 'World', you: 'You', search: '', settings: '', status: 'Home' }

/** Every in-app link is an <a href="/…"> (the design system's components render real links);
 *  a plain click on one navigates here instead of loading a page. */
function Links({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  useEffect(() => {
    const on = (e: MouseEvent) => {
      const a = (e.target as Element).closest?.('a[href]')
      const to = a?.getAttribute('href')
      if (!to?.startsWith('/') || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || a!.getAttribute('target')) return
      e.preventDefault()
      navigate(to)
    }
    addEventListener('click', on)
    return () => removeEventListener('click', on)
  }, [navigate])
  return <LibraryProvider>{children}<Toasts /></LibraryProvider>
}

type Theme = 'night' | 'day'

/** The Sky: every page outside a story. Rail, the Sky behind, the Night/Day theme. */
function Sky() {
  const { pathname } = useLocation()
  const [theme, setTheme] = useState<Theme>('night')
  useEffect(() => {
    api<{ 'appearance.theme'?: Theme }>('/settings').then((s) => s['appearance.theme'] && setTheme(s['appearance.theme']), () => {})
  }, [])
  const flip = (to: string) => {
    if (to !== 'Day' && to !== 'Night') return
    const next: Theme = to === 'Day' ? 'day' : 'night'
    setTheme(next)
    api('/settings', 'PUT', { 'appearance.theme': next }).catch(() => {})
  }
  const at = pathname.split('/')[1]
  return (
    <div data-theme={theme} className="app">
      <div className="app__sky"><K.Sky /></div>
      <div className="app__rail">
        <K.Rail active={(ACTIVE[at] ?? '') as 'Home'} theme={theme} hrefs={RAIL} onNavigate={flip} />
      </div>
      <Outlet />
    </div>
  )
}

const sky = (path: string, element: ReactNode = <NotBuilt />): RouteObject => ({ path, element })

const routes: RouteObject[] = [
  {
    element: <Links><Outlet /></Links>,
    children: [
      { path: '/', element: <Start /> },
      { path: '/story/:id', element: <Scene /> },
      { path: '/opening', element: <NotBuilt bare /> },
      { path: '/welcome/*', element: <NotBuilt bare /> },
      {
        element: <Sky />,
        children: [
          sky('/home', <Home />),
          sky('/stories', <Stories />),
          sky('/stories/new', <NewStory />),
          ...['/search', '/characters', '/characters/new', '/characters/:id', '/characters/:id/edit',
            '/world', '/you', '/settings/:panel', '/status/model'].map((p) => sky(p)),
          sky('*'),
        ],
      },
    ],
  },
]

/** Launch goes to Home until Opening (A1) lands. */
function Start() {
  const navigate = useNavigate()
  useEffect(() => void navigate('/home', { replace: true }), [navigate])
  return null
}

export const router = window.kataki ? createMemoryRouter(routes, { initialEntries: ['/'] }) : createBrowserRouter(routes)
document.title = t('app.name')

// The desktop smoke test (electron/main.ts › runSmoke) waits for this mark.
api('/health').then(
  () => (document.documentElement.dataset.engine = 'ok'),
  () => (document.documentElement.dataset.engine = 'down'),
)
