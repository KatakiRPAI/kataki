// F5 crop and focus, for character portraits and persona pictures: a fixed frame over the picture;
// drag to move it, wheel, pinch or the slider to zoom (1–4×), arrows and + − from the keyboard.
// Saved as data.focus ("x% y%") and data.zoom, and drawn everywhere by K.framed.
import { useEffect, useRef, useState, type PointerEvent } from 'react'
import { K } from '../ds'
import { Overlay } from '../overlay'
import { t } from '../strings'
import type { Shown } from '../errors'

/** A picture as it is saved on a character or persona. */
export type Picture = { portrait?: string; focus?: string; zoom?: number; alt?: string }

const MAX = 4
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))

export function Crop({ src, bad, focus, zoom, alt, name, onClose, onChoose, onUse }: {
  src: string; bad?: Shown; focus?: string; zoom?: number; alt?: string; name: string
  onClose: () => void; onChoose?: () => void; onUse: (focus: string, zoom: number, alt: string) => void
}) {
  const [x0, y0] = (focus ?? '50% 40%').split(' ').map((v) => parseFloat(v))
  const [at, setAt] = useState({ x: x0, y: y0, z: clamp(zoom ?? 1, 1, MAX) })
  const [text, setText] = useState(alt ?? '')
  const frame = useRef<HTMLDivElement>(null)
  const img = useRef<HTMLImageElement>(null)
  const pointers = useRef(new Map<number, { x: number; y: number }>())

  // Moving the focus by d (0–1) moves the picture by d·(w − z·W) px, W the covered width (K.framed's maths)
  const pan = (dx: number, dy: number) => setAt((a) => {
    const f = frame.current!, i = img.current!
    const s = Math.max(f.clientWidth / (i.naturalWidth || 1), f.clientHeight / (i.naturalHeight || 1))
    const spanX = a.z * i.naturalWidth * s - f.clientWidth, spanY = a.z * i.naturalHeight * s - f.clientHeight
    return { ...a, x: spanX > 0.5 ? clamp(a.x - (dx / spanX) * 100, 0, 100) : a.x, y: spanY > 0.5 ? clamp(a.y - (dy / spanY) * 100, 0, 100) : a.y }
  })
  const zoomBy = (k: number) => setAt((a) => ({ ...a, z: clamp(a.z * k, 1, MAX) }))
  useEffect(() => {
    const f = frame.current
    if (!f) return
    const wheel = (e: WheelEvent) => { e.preventDefault(); zoomBy(Math.exp(-e.deltaY * 0.0015)) } // non-passive, so the page doesn't scroll
    f.addEventListener('wheel', wheel, { passive: false })
    return () => f.removeEventListener('wheel', wheel)
  }, [bad])

  const move = (e: PointerEvent) => {
    const ps = pointers.current, was = ps.get(e.pointerId)
    if (!was) return
    const others = [...ps].filter(([id]) => id !== e.pointerId).map(([, p]) => p)
    if (others.length) { // pinch: the distance between two fingers
      const o = others[0], before = Math.hypot(was.x - o.x, was.y - o.y), after = Math.hypot(e.clientX - o.x, e.clientY - o.y)
      if (before > 0) zoomBy(after / before)
    } else pan(e.clientX - was.x, e.clientY - was.y)
    ps.set(e.pointerId, { x: e.clientX, y: e.clientY })
  }
  const lift = (e: PointerEvent) => pointers.current.delete(e.pointerId)

  const pos = `${Math.round(at.x * 10) / 10}% ${Math.round(at.y * 10) / 10}%`
  const z = Math.round(at.z * 100) / 100
  const style = K.framed(pos, z)
  return (
    <Overlay onClose={onClose}>
      <section className="dlg dlg--xl" role="dialog" aria-modal="true" aria-labelledby="focus-title">
        <div className="dlg__head">
          <div className="dlg__titles"><h2 className="dlg__title" id="focus-title">{t('focus.title')}</h2><p className="dlg__desc">{t('focus.body')}</p></div>
          <K.IconButton icon="x" label="Close" size="sm" onClick={onClose} />
        </div>
        <div className="dlg__body">
          {bad ? (
            <K.Callout tone="bad" title={bad.title} action={onChoose && <K.Button size="sm" onClick={() => { onClose(); onChoose() }}>{t('ed.chooseFile')}</K.Button>}>{bad.body} <span className="errcode">{bad.code}</span></K.Callout>
          ) : (
            <div className="ed-focus">
              <div className="col" style={{ gap: 12 }}>
                <div ref={frame} className="ed-focus__frame" tabIndex={0} role="group" aria-label={t('focus.frame')} aria-describedby="focus-hint"
                  onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY }) }}
                  onPointerMove={move} onPointerUp={lift} onPointerCancel={lift}
                  onKeyDown={(e) => {
                    const step = e.shiftKey ? 40 : 8
                    const d = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key]
                    if (d) { e.preventDefault(); pan(d[0], d[1]) }
                    else if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomBy(1.1) }
                    else if (e.key === '-' || e.key === '_') { e.preventDefault(); zoomBy(1 / 1.1) }
                  }}>
                  <img ref={img} src={src} alt="" draggable={false} style={style} />
                </div>
                <K.Slider label={t('focus.zoom')} min={100} max={MAX * 100} value={Math.round(at.z * 100)} valueText={`${z.toFixed(1)}×`}
                  onChange={(v) => setAt((a) => ({ ...a, z: v / 100 }))} />
                <span className="t-meta" id="focus-hint">{t('focus.hint')}</span>
              </div>
              <div className="col" style={{ gap: 14 }}>
                <K.Eyebrow>{t('focus.crops')}</K.Eyebrow>
                <div className="row" style={{ gap: 14, alignItems: 'flex-end' }}>
                  {[20, 40, 64].map((s) => <K.Avatar key={s} src={src} focus={pos} zoom={z} size={s} />)}
                </div>
                <div className="ed-focus__card"><img src={src} alt="" style={style} /></div>
                <span className="t-meta" aria-live="polite">{t('focus.value', { x: Math.round(at.x), y: Math.round(at.y), z: z.toFixed(1) })}</span>
                <K.TextField label={t('focus.alt')} hint={t('focus.altHint')} value={text} onChange={setText} placeholder={name} />
              </div>
            </div>
          )}
        </div>
        <div className="dlg__foot">
          <span />
          <div className="k-btngroup">
            <K.Button variant="ghost" onClick={onClose}>{t('focus.cancel')}</K.Button>
            {!bad && <K.Button variant="primary" onClick={() => onUse(pos, z, text.trim())}>{t('focus.use')}</K.Button>}
          </div>
        </div>
      </section>
    </Overlay>
  )
}
