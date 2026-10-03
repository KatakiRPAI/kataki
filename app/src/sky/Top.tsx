// The Sky's top bar: who you are playing as (opens the persona menu, C4) and search (opens the
// palette, C5). One place, so every page behaves the same. Online it also carries the balance (T1).
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { api } from '../api'
import { K } from '../ds'
import { face, useLibrary } from '../hooks'
import { account } from '../online/session'
import { usePrefs } from '../prefs'
import { t } from '../strings'
import { openPalette, personaMenu } from './Palette'

const LOW = 1_000_000 // micro-dollars: under $1 the chip turns amber (docs/decisions.md)

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
      <K.TopBar {...face(persona)}>
        {account() ? <div className="row" style={{ gap: 12 }}><Balance /><K.SearchField /></div> : undefined}
      </K.TopBar>
    </div>
  )
}

/** T1: what is left, quietly; amber when low, red at nothing. Opens Add credit. */
function Balance() {
  const navigate = useNavigate()
  const [left, setLeft] = useState<number>()
  useEffect(() => {
    const load = () => api<{ balance: number }>('/api/me').then((m) => setLeft(m.balance), () => {})
    load()
    addEventListener('focus', load)
    return () => removeEventListener('focus', load)
  }, [])
  if (left === undefined) return null
  const usd = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(Math.max(0, left) / 1e6)
  const tone = left <= 0 ? ' bal--out' : left < LOW ? ' bal--low' : ''
  return (
    <a className={`k-chip k-chip--sm bal${tone}`} href={`${import.meta.env.BASE_URL}settings/account?add=1`} title={t('cr.balanceTip', { amount: usd })} aria-label={t('cr.balanceTip', { amount: usd })}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); navigate('/settings/account?add=1') }}>
      {usd}
    </a>
  )
}
