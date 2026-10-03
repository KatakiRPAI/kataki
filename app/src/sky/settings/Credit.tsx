// Adding credit (design brief 3 T2, T3; docs/specs/2026-10-02-kataki-online.md G7): pick an
// amount, pay on the processor's own page, come back and hear how it went.
import { useEffect, useState } from 'react'
import { api } from '../../api'
import { K } from '../../ds'
import { useLoad } from '../../hooks'
import { Overlay, toast } from '../../overlay'
import { t } from '../../strings'

const usd = (n: number) => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

/** "Add credit", when there is a way to pay; and the word on a checkout just come back from. */
export default function Credit({ onChange }: { onChange: () => void }) {
  const [offer] = useLoad(() => fetch('/api/providers').then((r) => r.json()).then((p: { payments: { amounts: number[] } | null }) => p.payments, () => null), [])
  const [open, setOpen] = useState(() => new URLSearchParams(location.search).has('add')) // T4: sent here by "Add credit"
  useEffect(() => { // T3: back from the processor's page
    const said = new URLSearchParams(location.search)
    if (said.has('add')) history.replaceState(null, '', location.pathname)
    const id = said.get('topup')
    if (!id) return
    history.replaceState(null, '', location.pathname)
    api<{ status: 'open' | 'paid' | 'cancelled'; dollars: number }>(`/api/topup/${encodeURIComponent(id)}`).then((c) => {
      toast(t(c.status === 'paid' ? 'cr.paid' : c.status === 'cancelled' ? 'cr.cancelled' : 'cr.waiting', { amount: usd(c.dollars) }), { icon: c.status === 'paid' ? 'check' : 'alert' }, 8000)
      onChange()
    }, () => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  if (!offer) return null
  return (
    <>
      <K.Button size="sm" icon="plus" onClick={() => setOpen(true)}>{t('cr.add')}</K.Button>
      {open && <Amounts amounts={offer.amounts} onClose={() => setOpen(false)} />}
    </>
  )
}

function Amounts({ amounts, onClose }: { amounts: number[]; onClose: () => void }) {
  const [picked, setPicked] = useState(amounts[1] ?? amounts[0])
  const [busy, setBusy] = useState(false)
  const go = async () => {
    setBusy(true)
    try {
      const { url } = await api<{ url: string }>('/api/topup', 'POST', { dollars: picked })
      location.assign(url) // the processor's own page; it sends the person back here
    } catch (e) {
      toast((e as Error).message, { icon: 'alert' }, 8000)
      setBusy(false)
    }
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog size="sm" icon="plus" title={t('cr.title')} description={t('cr.body')} onClose={onClose}
        actions={[<K.Button key="c" variant="ghost" onClick={onClose}>{t('ep.cancel')}</K.Button>,
          <K.Button key="g" variant="primary" loading={busy} onClick={go}>{t('cr.go', { amount: usd(picked) })}</K.Button>]}>
        <K.Segmented label={t('cr.amount')} options={amounts.map(usd)} value={usd(picked)} onChange={(v) => setPicked(amounts.find((a) => usd(a) === v) ?? picked)} />
      </K.Dialog>
    </Overlay>
  )
}
