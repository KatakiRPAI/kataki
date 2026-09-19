import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './design/tokens.css'
import './design/components.css'
import './design/fonts/fonts.css'
import './app.css'
import sprite from './design/sprite.svg?raw'
import App from './App'

document.body.insertAdjacentHTML('afterbegin', sprite) // <use href="#i-name"> finds the icons here

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
