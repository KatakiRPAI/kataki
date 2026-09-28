// Shortcuts (K14, K15): every shortcut; click one and press the new keys.
import { useEffect, useState } from 'react'
import { K } from '../../ds'
import { setPref, usePrefs } from '../../prefs'
import { combo, holder, keysOf, parts, reserved, SHORTCUTS } from '../../shortcuts'
import { toast } from '../../overlay'
import { t, type Key } from '../../strings'

export default function Shortcuts() {
  const [prefs] = usePrefs()
  const [q, setQ] = useState('')
  const [recording, setRecording] = useState<string>()
  const [clash, setClash] = useState<{ id: string; keys: string; other?: string; reserved?: boolean }>()
  const own = (prefs.shortcuts ?? {}) as Record<string, string>
  const label = (id: string) => t(`sc.${id}` as Key)
  const assign = (id: string, keys: string, unset?: string) => {
    const before = own
    const next = { ...own, [id]: keys, ...(unset ? { [unset]: '' } : {}) }
    setPref('shortcuts', next)
    toast(t('toast.shortcut', { action: label(id), keys }), { action: t('toast.undo'), onAction: () => setPref('shortcuts', before) }, 6000)
  }
  useEffect(() => {
    if (!recording) return
    const on = (e: KeyboardEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (e.key === 'Escape') return setRecording(undefined)
      const keys = combo(e)
      if (!keys) return
      setRecording(undefined)
      if (reserved(keys)) return setClash({ id: recording, keys, reserved: true })
      const other = holder(keys, recording)
      if (other) return setClash({ id: recording, keys, other: other[0] })
      assign(recording, keys)
    }
    addEventListener('keydown', on, true)
    return () => removeEventListener('keydown', on, true)
  }) // eslint-disable-line react-hooks/exhaustive-deps
  const shown = SHORTCUTS.filter(([id]) => !q.trim() || label(id).toLowerCase().includes(q.trim().toLowerCase()))
  const column = (where: 'anywhere' | 'story', title: Key) => (
    <K.SettingsSection title={t(title)}>
      <K.Panel flush>
        {shown.filter((s) => s[2] === where).map(([id]) => (
          <K.ShortcutRow key={id} label={label(id)} keys={parts(keysOf(id))} unset={t('sh.unset')}
            recording={recording === id ? t('sh.press') : undefined} onClick={() => setRecording(recording === id ? undefined : id)} />
        ))}
      </K.Panel>
    </K.SettingsSection>
  )
  return (
    <>
      <div className="row" style={{ justifyContent: 'space-between', gap: 16 }}>
        <span className="t-body">{t('sh.intro')}</span>
        <K.Button variant="ghost" disabled={!Object.keys(own).length} onClick={() => setPref('shortcuts', {})}>{t('sh.reset')}</K.Button>
      </div>
      <div style={{ maxWidth: 360 }}><K.SearchField placeholder={t('sh.find')} label={t('sh.find')} shortcut={false} value={q} onChange={setQ} /></div>
      {clash && (clash.reserved ? (
        <K.Callout tone="bad" title={t('sh.reserved', { keys: clash.keys })} action={<K.Button size="sm" onClick={() => { setRecording(clash.id); setClash(undefined) }}>{t('sh.pickOther')}</K.Button>}>{t('sh.reservedBody')}</K.Callout>
      ) : (
        <K.Callout tone="warm" title={t('sh.taken', { keys: clash.keys, action: label(clash.other!) })}
          action={<div className="row" style={{ gap: 8 }}>
            <K.Button size="sm" onClick={() => { assign(clash.id, clash.keys, clash.other); setClash(undefined) }}>{t('sh.useHere')}</K.Button>
            <K.Button size="sm" variant="ghost" onClick={() => { setRecording(clash.id); setClash(undefined) }}>{t('sh.pickOther')}</K.Button>
          </div>}>
          {t('sh.takenBody', { mine: label(clash.id) })}
        </K.Callout>
      ))}
      <div className="sh-grid">
        {column('anywhere', 'sh.anywhere')}
        {column('story', 'sh.story')}
      </div>
    </>
  )
}
