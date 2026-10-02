import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'
import './ds'
import './app.css'
import { session } from './online/session'

// Kataki online asks who is signed in before the app (and its first calls) load at all.
const root = createRoot(document.getElementById('root')!)
if ((await session()) === 'signed-out') {
  const { default: SignIn } = await import('./online/SignIn')
  root.render(<StrictMode><SignIn /></StrictMode>)
} else {
  const { router } = await import('./router')
  root.render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>,
  )
}
