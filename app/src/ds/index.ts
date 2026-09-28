// The Kataki design system, vendored as shipped (docs/handoff/kataki-handoff/boards/ds). The
// bundle sets window.Kataki; changes the handoff asks for (COMPONENT-GAPS.md) are made in it.
import './global'
import './bundle.js'
import './tokens.css'
import './bundle.css'
import './fonts/fonts.css'
import './layout.css'
import type * as Types from './kataki'
import liv from './art/liv.png'
import mike from './art/mike.png'
import theo from './art/theo.png'
import nico from './art/nico.png'
import jae from './art/jae.png'
import cas from './art/cas.png'
import halcyon from './art/halcyon-coffee.png'
import palace from './art/corvel-palace.png'
import ardenne from './art/flat-on-ardenne.png'
import clouds from './art/clouds.svg'

type Kataki = typeof Types & { ART: Record<string, { src?: string | null; focus?: string }> }
export const K = (window as unknown as { Kataki: Kataki }).Kataki

// The sample world's art, from this app's own copies instead of the canvas's blob store.
const ART: Record<string, string> = {
  liv, mike, theo, nico, jae, cas, clouds,
  'halcyon-coffee': halcyon, 'corvel-palace': palace, 'flat-on-ardenne': ardenne,
}
for (const [k, src] of Object.entries(ART)) K.ART[k] = { ...K.ART[k], src }
K.ART.dani = { ...K.ART.dani, src: undefined }
