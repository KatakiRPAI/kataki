// Lines waiting for the turn to free up (SCENE.md › A turn › Queued), shown at the end of the
// story the way they will read once sent. Each can be edited, read another way, moved one
// place earlier, or taken out. An edit in progress holds the queue (Scene keeps `editing`).
import { useState } from 'react'
import { K } from '../ds'
import { t } from '../strings'
import { Bubbles } from './Lines'
import { force, type Mode } from './modes'
import { change, drop, sooner, type Waiting } from './waiting'

const compose = () => document.querySelector<HTMLElement>('.k-chat__composer textarea')?.focus()

export default function Queue({ queue, set, editing, onEditing, name, to, texting, pickMode }: {
  queue: Waiting[]
  set: (f: (q: Waiting[]) => Waiting[]) => void
  editing?: number
  onEditing: (id?: number) => void
  name?: string // the persona; without one you direct, and every line is narration
  to?: string // who a whisper is for
  texting: boolean
  pickMode: (at: Element, now: Mode, pick: (m: Mode) => void) => void
}) {
  if (!queue.length) return null
  return (
    <div className="queue" role="group" aria-label={t('queue.label')}>
      {queue.map((w, i) => {
        if (w.id === editing) return <Edit key={w.id} w={w} name={name} onDone={(text) => { if (text !== undefined) set((q) => change(q, w.id, { text })); onEditing(); compose() }} />
        const how = force(w.text, w.mode)
        const mode = how.mode === 'Narrate' || !name ? 'narrate' : how.mode === 'Whisper' ? 'whisper' : how.mode === 'Think' ? 'think' : undefined
        const bubbles = texting && !mode
        return (
          <div key={w.id} className={bubbles ? 'txt txt--me' : undefined}>
            <K.ChatLine speaker="user" color="var(--speaker-liv)" name={name ?? t('scene.narrator')} time={t('queue.waiting')} text={bubbles ? '' : how.text} dim
              mode={mode} modeNote={mode === 'whisper' && to ? t('line.whisper', { names: to }) : mode === 'think' ? t('line.thought') : undefined}>
              {bubbles && <Bubbles text={how.text} />}
              <span className="queue__tools">
                <button type="button" className="k-scenechip" aria-haspopup="menu" aria-label={`${t('mode.label')}: ${how.detected}`}
                  onClick={(e) => pickMode(e.currentTarget, w.mode, (m) => set((q) => change(q, w.id, { mode: m })))}>
                  {w.mode === 'Auto' ? `${t('mode.auto')} · ${how.detected}` : w.mode}<K.Icon name="down" size={14} />
                </button>
                {i > 0 && <button type="button" className="k-scenechip" aria-label={t('queue.sooner')} title={t('queue.sooner')} onClick={() => set((q) => sooner(q, w.id))}><K.Icon name="up" size={14} /></button>}
                <button type="button" className="k-scenechip" onClick={() => onEditing(w.id)}><K.Icon name="edit" size={14} />{t('line.edit')}</button>
                <button type="button" className="k-scenechip" onClick={() => { set((q) => drop(q, w.id)); compose() }}><K.Icon name="x" size={14} />{t('queue.remove')}</button>
              </span>
            </K.ChatLine>
          </div>
        )
      })}
    </div>
  )
}

function Edit({ w, name, onDone }: { w: Waiting; name?: string; onDone: (text?: string) => void }) {
  const [draft, setDraft] = useState(w.text)
  return <K.EditLine speaker="user" color="var(--speaker-liv)" name={name ?? t('scene.narrator')} time={t('queue.waiting')} text={w.text}
    value={draft} onChange={setDraft} onCancel={() => onDone()} onSave={() => onDone(draft)} />
}
