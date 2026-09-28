// Routes (docs/handoff/kataki-handoff/ROUTES.md). One route table for both hosts: a memory router
// in the desktop app, the browser's own history on the web. Overlays are state, never routes.
import { useEffect, type ReactNode } from 'react'
import { createBrowserRouter, createMemoryRouter, Outlet, useLocation, useNavigate, type RouteObject } from 'react-router'
import { api } from './api'
import { K } from './ds'
import { LibraryProvider } from './hooks'
import { Menus, Toasts } from './overlay'
import { loadPrefs, setPref, skyTheme, usePrefs } from './prefs'
import { t } from './strings'
import Home from './sky/Home'
import NotBuilt from './sky/NotBuilt'
import Stories from './sky/Stories'
import NewStory from './sky/NewStory'
import Characters from './sky/Characters'
import Profile from './sky/Profile'
import Editor from './sky/Editor'
import Settings, { last as lastSettings } from './sky/Settings'
import World from './sky/World'
import You from './sky/You'
import Search from './sky/Search'
import FirstRun, { ModelGone, Opening } from './sky/FirstRun'
import { Palette } from './sky/Palette'
import { Feedback, openFeedback } from './sky/Feedback'
import Scene from './scene/Scene'

const RAIL: Record<string, string> = {
  Home: '/home', Stories: '/stories', Characters: '/characters', World: '/world', You: '/you',
  'New character': '/characters/new', Settings: '/settings/general',
}
const ACTIVE: Record<string, string> = { home: 'Home', stories: 'Stories', characters: 'Characters', world: 'World', you: 'You', search: 'none', settings: 'Settings', status: 'Home' }

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
  return <LibraryProvider>{children}<Palette /><Feedback /><Toasts /><Menus /></LibraryProvider>
}

/** The Sky: every page outside a story. Rail, the Sky behind, the Night/Day theme. */
function Sky() {
  const { pathname } = useLocation()
  const [prefs] = usePrefs()
  const theme = skyTheme(prefs)
  const flip = (to: string) => {
    if (to === 'Day' || to === 'Night') setPref('appearance.theme', to === 'Day' ? 'day' : 'night')
    if (to === 'Feedback') openFeedback('feedback')
  }
  const at = pathname.split('/')[1]
  return (
    <div data-theme={theme} className="app">
      <div className="app__sky"><K.Sky stars={prefs['appearance.stars'] === false ? 0 : undefined} /></div>
      <div className="app__rail">
        <K.Rail active={(ACTIVE[at] ?? 'none') as 'Home'} theme={theme} hrefs={{ ...RAIL, Settings: `/settings/${lastSettings.panel}` }} onNavigate={flip} />
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
      { path: '/', element: <Opening /> },
      { path: '/story/:id', element: <Scene /> },
      { path: '/opening', element: <Opening /> },
      { path: '/welcome/*', element: <FirstRun /> },
      {
        element: <Sky />,
        children: [
          sky('/home', <Home />),
          sky('/stories', <Stories />),
          sky('/stories/new', <NewStory />),
          sky('/characters', <Characters />),
          sky('/characters/new', <Editor key="new" />),
          sky('/characters/:id', <Profile />),
          sky('/characters/:id/edit', <Editor key="edit" />),
          sky('/settings/:panel', <Settings />),
          sky('/world', <World />),
          sky('/you', <You />),
          sky('/search', <Search />),
          sky('/status/model', <ModelGone />),
          sky('*'),
        ],
      },
    ],
  },
]

export const router = window.kataki ? createMemoryRouter(routes, { initialEntries: ['/'] }) : createBrowserRouter(routes)
document.title = t('app.name')



loadPrefs() // pages opened straight from a link still get the settings

// The desktop smoke test (electron/main.ts › runSmoke) waits for this mark.
api('/health').then(
  () => (document.documentElement.dataset.engine = 'ok'),
  () => (document.documentElement.dataset.engine = 'down'),
)
