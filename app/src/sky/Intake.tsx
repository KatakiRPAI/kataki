import { useEffect, useState } from 'react'
import { api, sendFile, type Item, type Look, type StorySummary } from '../api'
import { arrived, go, useAction, useLoad } from '../hooks'
import { Dialog, ErrorLine, Field, Icon } from '../ui'

/** Hand a file to the reader from anywhere — Settings' Import button does. */
let hand: ((file: File) => void) | null = null
export const bringIn = (file: File) => hand?.(file)

const WHAT: Record<Look['kind'], string> = {
  card: 'A character card',
  chat: 'A chat from another app',
  lorebook: 'A lorebook',
  kataki: 'A Kataki library',
}

/** Bringing something in: drop a file anywhere in the app, see what it would become, and only
 *  then let it be made. Nothing the engine reads here writes anything. */
export default function Intake() {
  // Its own, not the Sky's: this lives above every LibraryProvider, so that it is there wherever
  // a file lands. Both are re-read as a file is read, so the lists are what they are right now.
  const [items, reloadItems] = useLoad(() => api<Item[]>('/library'), [])
  const [stories, reloadStories] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [run, error, busy] = useAction()
  const [over, setOver] = useState(false) // a file is being dragged across the window
  const [file, setFile] = useState<File>()
  const [look, setLook] = useState<Look>()
  const [reading, setReading] = useState(false)
  const [about, setAbout] = useState<{ character: string; persona: string; story: string }>({
    character: '',
    persona: '',
    story: '',
  })

  const close = () => {
    setFile(undefined)
    setLook(undefined)
  }

  /** Read the file, and say what it would become. */
  const read = (picked: File) =>
    run(async () => {
      setFile(picked)
      setLook(undefined)
      setReading(true)
      reloadItems()
      reloadStories()
      try {
        setLook(await sendFile<Look>('/import/look', picked))
      } finally {
        setReading(false)
      }
    })

  useEffect(() => {
    hand = read
    // Without these the window would simply navigate to the file, losing the app.
    const dragged = (e: DragEvent) => !!e.dataTransfer?.types.includes('Files')
    const onOver = (e: DragEvent) => {
      if (!dragged(e)) return
      e.preventDefault()
      setOver(true)
    }
    const onLeave = (e: DragEvent) => {
      if (e.relatedTarget === null) setOver(false) // left the window, not just an element
    }
    const onDrop = (e: DragEvent) => {
      if (!dragged(e)) return
      e.preventDefault()
      setOver(false)
      const dropped = e.dataTransfer?.files[0]
      if (dropped) read(dropped)
    }
    addEventListener('dragover', onOver)
    addEventListener('dragleave', onLeave)
    addEventListener('drop', onDrop)
    return () => {
      hand = null
      removeEventListener('dragover', onOver)
      removeEventListener('dragleave', onLeave)
      removeEventListener('drop', onDrop)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const friends = (items ?? []).filter((i) => i.kind === 'character' && !i.data.persona)
  const personas = (items ?? []).filter((i) => i.kind === 'character' && i.data.persona)

  /** Make it, at last. Every kind lands somewhere you can see what arrived. */
  const bring = () =>
    run(async () => {
      if (!file || !look) return
      if (look.kind === 'card') {
        const made = await sendFile<{ item: Item }>('/import/card', file)
        close()
        arrived()
        go(`/friend/${made.item.id}`)
      } else if (look.kind === 'chat') {
        const query = new URLSearchParams()
        if (about.character) query.set('character_id', about.character)
        if (about.persona) query.set('persona_id', about.persona)
        const made = await sendFile<{ story_id: number }>(`/import/chat?${query}`, file)
        close()
        arrived()
        go(`/chats/${made.story_id}`)
      } else if (look.kind === 'lorebook') {
        if (!about.story) return
        await sendFile(`/stories/${about.story}/lorebook`, file)
        close()
        arrived()
        go(`/chats/${about.story}`)
      } else {
        await sendFile('/import/kataki', file)
        close()
        arrived()
        go('/home')
      }
    })

  const ready = look && (look.kind !== 'lorebook' || !!about.story)

  return (
    <>
      {over && (
        <div className="ka-drop" aria-hidden="true">
          <div className="ka-drop__note">
            <Icon name="download" size={22} />
            Drop it anywhere
            <small>A character card, a chat, a lorebook or a Kataki library</small>
          </div>
        </div>
      )}

      <Dialog
        open={!!file}
        onClose={close}
        title={look ? `Bring in ${look.title}?` : reading ? 'Reading…' : 'This file can’t come in'}
      >
        {reading && <p className="ka-muted">Reading {file?.name}…</p>}
        {look && (
          <>
            <p className="ka-muted ka-small">
              {WHAT[look.kind]} · {file?.name}
            </p>
            <ul className="ka-intake__what">
              {look.what.map((line) => (
                <li key={line}>
                  <Icon name="check" size={14} />
                  {line}
                </li>
              ))}
            </ul>
            {look.notes.map((note) => (
              <p key={note} className="ka-muted ka-small">
                {note}
              </p>
            ))}

            {look.kind === 'chat' && (
              <div className="ka-row ka-row--gap16">
                <Field label="Who it is about">
                  <select className="k-select" value={about.character}
                    onChange={(e) => setAbout((a) => ({ ...a, character: e.target.value }))}>
                    <option value="">Make a new friend</option>
                    {friends.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                  </select>
                </Field>
                <Field label="Who you were">
                  <select className="k-select" value={about.persona}
                    onChange={(e) => setAbout((a) => ({ ...a, persona: e.target.value }))}>
                    <option value="">Make a new persona</option>
                    {personas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </Field>
              </div>
            )}
            {look.kind === 'lorebook' && (
              <Field label="The story that learns it">
                <select className="k-select" value={about.story}
                  onChange={(e) => setAbout((a) => ({ ...a, story: e.target.value }))}>
                  <option value="">Pick a story…</option>
                  {(stories ?? []).map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
                </select>
              </Field>
            )}
          </>
        )}
        <ErrorLine error={error} />
        <div className="ka-row ka-row--end">
          <button type="button" className="k-btn" onClick={close}>{look ? 'Not now' : 'Close'}</button>
          {/* nothing to offer until we know what the file is */}
          {look && (
            <button type="button" className="k-btn k-btn--dark" disabled={busy || !ready} onClick={bring}>
              Bring it in
            </button>
          )}
        </div>
      </Dialog>
    </>
  )
}
