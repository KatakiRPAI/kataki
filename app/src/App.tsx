import { useEffect, useState } from 'react'
import { api, type Provider, type StorySummary } from './api'
import Library from './Library'
import Models from './Models'
import { NewStory } from './Stories'
import StoryView from './Story'
import { ErrorLine, useLoad } from './ui'

type Page = { name: 'models' } | { name: 'library' } | { name: 'new-story' } | { name: 'story'; id: number }

export default function App() {
  const [page, setPage] = useState<Page>({ name: 'library' })
  const [stories, reloadStories, error] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [health, , healthError] = useLoad(() => api<{ version: string; schema: number }>('/health'), [])

  // First run: nothing works until a model is connected, so start where that happens.
  useEffect(() => {
    api<Provider[]>('/providers').then((providers) => {
      if (!providers.length) setPage({ name: 'models' })
    }, () => {})
  }, [])

  const is = (name: Page['name'], id?: number) =>
    page.name === name && (id === undefined || (page.name === 'story' && page.id === id)) ? 'active' : ''

  return (
    <div className="app">
      <nav className="nav" aria-label="Main">
        <div className="brand">Kataki RPAI</div>
        <button className={is('new-story')} onClick={() => setPage({ name: 'new-story' })}>+ New story</button>
        <div className="stories">
          {stories?.map((s) => (
            <button key={s.id} className={is('story', s.id)} onClick={() => setPage({ name: 'story', id: s.id })}>
              {s.title}
            </button>
          ))}
        </div>
        <hr style={{ borderColor: 'var(--line)', margin: '1rem 0' }} />
        <button className={is('library')} onClick={() => setPage({ name: 'library' })}>Library</button>
        <button className={is('models')} onClick={() => setPage({ name: 'models' })}>Models</button>
        <ErrorLine error={error} />
        <p role="status" style={{ marginTop: '1rem' }}>
          <small>
            {health ? `engine ok · v${health.version} · schema ${health.schema}` : healthError ? `engine unreachable: ${healthError}` : 'connecting…'}
          </small>
        </p>
      </nav>
      <main className="page">
        {page.name === 'models' && <Models />}
        {page.name === 'library' && <Library />}
        {page.name === 'new-story' && (
          <NewStory
            onCreated={(id) => {
              reloadStories()
              setPage({ name: 'story', id })
            }}
          />
        )}
        {page.name === 'story' && (
          <StoryView
            key={page.id}
            id={page.id}
            onDeleted={() => {
              reloadStories()
              setPage({ name: 'library' })
            }}
          />
        )}
      </main>
    </div>
  )
}
