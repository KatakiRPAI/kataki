import { useLocation } from 'react-router'
import { K } from '../ds'
import { t } from '../strings'

/** A route the rebuild has not reached yet (docs/specs/2026-09-28-handoff-3.md). */
export default function NotBuilt({ bare }: { bare?: boolean }) {
  const { pathname } = useLocation()
  const body = (
    <main className="app__main" aria-label={t('notBuilt.title')}>
      <K.EmptyState icon="layers" title={t('notBuilt.title')} actions={<K.Button href="/home">{t('notBuilt.home')}</K.Button>}>
        {t('notBuilt.body', { path: pathname })}
      </K.EmptyState>
    </main>
  )
  return bare ? <div data-theme="night" className="app">{body}</div> : body
}
