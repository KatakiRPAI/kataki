// The Sky's top bar: who you are playing as, and search. One place, so the persona menu (C4)
// and the palette (C5) hang off every page the same way.
import { K } from '../ds'
import { face, useLibrary } from '../hooks'
import { usePrefs } from '../prefs'

export default function Top() {
  const { byId } = useLibrary()
  const [prefs] = usePrefs()
  const persona = typeof prefs.persona === 'number' ? byId.get(prefs.persona) : undefined
  return <K.TopBar {...face(persona)} />
}
