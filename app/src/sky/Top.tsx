// The Sky's top bar: who you are playing as (opens the persona menu, C4) and search (opens the
// palette, C5). One place, so every page behaves the same.
import { useNavigate } from 'react-router'
import { K } from '../ds'
import { face, useLibrary } from '../hooks'
import { usePrefs } from '../prefs'
import { openPalette, personaMenu } from './Palette'

export default function Top() {
  const navigate = useNavigate()
  const { items, byId } = useLibrary()
  const [prefs] = usePrefs()
  const persona = typeof prefs.persona === 'number' ? byId.get(prefs.persona) : undefined
  return (
    <div className="top"
      onClick={(e) => {
        const el = e.target as Element
        const who = el.closest('.k-persona')
        if (who) personaMenu(who, items, prefs.persona as number | null | undefined, navigate)
        else if (el.closest('.k-search')) { e.preventDefault(); openPalette() }
      }}
      onFocus={(e) => { if ((e.target as Element).classList.contains('k-search__input')) { (e.target as HTMLElement).blur(); openPalette() } }}>
      <K.TopBar {...face(persona)} />
    </div>
  )
}
