import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'
import './ds'
import './app.css'
import { session } from './online/session'
import { t } from './strings'

// Kataki online asks who is signed in before the app (and its first calls) load at all.
const root = createRoot(document.getElementById('root')!)
const who = await session()
if (who !== 'none') { // Kataki online on the test processor: say so on every page, so no one mistakes it for real
  fetch('/api/providers').then((r) => r.json()).then((p: { payments?: { test?: boolean } | null }) => {
    if (p.payments?.test) document.body.insertAdjacentHTML('beforeend', `<div class="testpay" role="note">${t('cr.testRibbon')}</div>`)
  }, () => {})
}
if (who === 'signed-out') {
  const { default: SignIn } = await import('./online/SignIn')
  root.render(<StrictMode><SignIn /></StrictMode>)
} else if (who !== 'none' && who.deleteAt) {
  const { default: Deleting } = await import('./online/Deleting')
  root.render(<StrictMode><Deleting me={who} /></StrictMode>)
} else if (who !== 'none' && new URLSearchParams(location.search).get('link')) {
  // the desktop app sent the person here to link that computer to this account
  const { default: Link } = await import('./online/Link')
  root.render(<StrictMode><Link me={who} code={new URLSearchParams(location.search).get('link')!} /></StrictMode>)
} else {
  const { router } = await import('./router')
  root.render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>,
  )
}
