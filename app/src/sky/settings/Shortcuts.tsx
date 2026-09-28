// Shortcuts (K14, K15): every shortcut; click one and press the new keys.
import { useEffect, useState } from 'react'
import { K } from '../../ds'
import { setPref, usePrefs } from '../../prefs'
import { combo, holder, keysOf, parts, reserved } from '../../shortcuts'
import { toast } from '../../overlay'
import { t, type Key } from '../../strings'

// The board's order. A string is a shortcut you can change; [label, keys] is one that stays as it is.
type Entry = string | [Key, string[]]
const LAYOUT: [Key, Entry[]][] = [
  ['sh.anywhere', ['search', 'newStory', 'newCharacter', 'persona', 'settings', 'focusSearch', 'feedback', ['sc.fixed.close', ['Esc']]]],
  ['sh.moving', ['goHome', 'goStories', 'goCharacters', 'goWorld', 'goYou', ['sc.fixed.next', ['Tab']]]],
  ['sh.story', [['sc.fixed.send', ['Enter']], ['sc.fixed.newLine', ['Shift', 'Enter']], 'sendPass', ['sc.fixed.editLast', ['↑']], 'regenerate', ['sc.fixed.stop', ['Esc']],
    ['sc.fixed.takes', ['Alt', '←', '→']], 'continue', 'backstage', 'find', 'mute', 'widgets', 'reading', ['sc.fixed.widget', ['Space', 'then', 'arrows']]]],
]

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
  const match = (text: string) => !q.trim() || text.toLowerCase().includes(q.trim().toLowerCase())
  const column = ([title, entries]: [Key, Entry[]]) => {
    const rows = entries.filter((e) => match(typeof e === 'string' ? label(e) : t(e[0])))
    return !rows.length ? null : (
      <K.SettingsSection key={title} title={t(title)}>
        <K.Panel flush>
          {rows.map((e) => typeof e === 'string'
            ? <K.ShortcutRow key={e} label={label(e)} keys={parts(keysOf(e))} unset={t('sh.unset')}
                recording={recording === e ? t('sh.press') : undefined} onClick={() => setRecording(recording === e ? undefined : e)} />
            : <K.ShortcutRow key={e[0]} label={t(e[0])} keys={e[1]} />)}
        </K.Panel>
      </K.SettingsSection>
    )
  }
  return (
    <>
      <div className="row" style={{ gap: 16 }}>
        <span className="t-body" style={{ flex: 1 }}>{t('sh.intro')}</span>
        <div style={{ width: 220 }}><K.SearchField placeholder={t('sh.find')} label={t('sh.find')} shortcut={false} value={q} onChange={setQ} /></div>
        <K.Button size="sm" variant="ghost" icon="refresh" disabled={!Object.keys(own).length} onClick={() => setPref('shortcuts', {})}>{t('sh.reset')}</K.Button>
      </div>
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
        <div className="col" style={{ gap: 22 }}>{LAYOUT.slice(0, 2).map(column)}</div>
        <div className="col" style={{ gap: 22 }}>{column(LAYOUT[2])}</div>
      </div>
    </>
  )
}
