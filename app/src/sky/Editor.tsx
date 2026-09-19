import { useEffect, useRef, useState, type CSSProperties } from 'react'
import { api, upload, type Item, type ItemData, type Pronouns } from '../api'
import { nextPalette, Portrait } from '../art'
import { go, href, useAction, useLibrary } from '../hooks'
import { Chip, Dialog, ErrorLine, Icon, Seg } from '../ui'

// Add a friend (or a persona) in six steps, saved as you go.

type Draft = {
  name: string
  description: string
  private: string
  example_dialogue: string
  first_message: string
  aliases: string // comma separated while editing
  tags: string
  pronouns: Pronouns
  favourite: boolean
  persona: boolean
  portrait?: string
}

export function draftOf(item?: Item, persona = false): Draft {
  return {
    name: item?.name ?? '',
    description: item?.description ?? '',
    private: item?.private ?? '',
    example_dialogue: item?.data.example_dialogue ?? '',
    first_message: item?.data.first_message ?? '',
    aliases: (item?.data.aliases ?? []).join(', '),
    tags: (item?.tags ?? []).join(', '),
    pronouns: item?.data.pronouns ?? 'they',
    favourite: !!item?.data.favourite,
    persona: item ? !!item.data.persona : persona,
    portrait: item?.data.portrait,
  }
}

type Step = { title: string; short: string; icon: string; done: (d: Draft) => boolean; nudge: [string, string] }

const STEPS: Step[] = [
  { title: 'Name and portrait', short: 'Name and portrait', icon: 'user', done: (d) => !!d.name.trim(),
    nudge: ['Give them a name to start', 'A name is enough; the rest can wait.'] },
  { title: 'Who they are', short: 'Who they are', icon: 'quote', done: (d) => !!d.description.trim(),
    nudge: ['Say who {name} is', 'A line or two gives the model someone to play.'] },
  { title: 'Their secret', short: 'Secret', icon: 'lock', done: (d) => !!d.private.trim(),
    nudge: ['Add a secret to make {name} more real', 'Characters with secrets hold back, and it shows.'] },
  { title: 'How they talk', short: 'How they talk', icon: 'chat', done: (d) => !!d.example_dialogue.trim(),
    nudge: ['Show how {name} talks', 'A few lines in their voice beat any description.'] },
  { title: 'How they say hi', short: 'How they say hi', icon: 'hand', done: (d) => !!d.first_message.trim(),
    nudge: ['Give {name} a way to say hi', 'Their first line sets the tone of every new story.'] },
  { title: 'Other names and tags', short: 'Other names and tags', icon: 'star', done: (d) => !!(d.aliases.trim() || d.tags.trim()),
    nudge: ['Add other names and tags', 'So {name} is recognised, and easy to find later.'] },
]

/** How much of the profile is filled in, 0..1. */
export const completeness = (item: Item) => STEPS.filter((s) => s.done(draftOf(item))).length / STEPS.length

// "Stuck? Start from": each chip starts a sentence in the box.
const STARTERS: Record<number, [string, string][]> = {
  1: [['Their work', '{name} works as '], ['How they look', '{name} is '], ['What they care about', '{name} cares most about '], ['A habit', '{name} always ']],
  2: [['A fear', '{name} is afraid of '], ['A debt', '{name} owes '], ['Something they did', 'Years ago, {name} '], ['Someone they protect', '{name} would do anything to protect '], ['What they want', 'More than anything, {name} wants ']],
  3: [['Short and blunt', '{name}: '], ['A question back', '{name}: And why would I tell you that?'], ['A saying of theirs', '{name}: As my mother used to say, ']],
  4: [['An action', '*'], ['A question', 'Well? '], ['A complaint', "You're late. "]],
}

const HELP = [
  'Who are we meeting? A name is enough to start; everything else can wait.',
  'What they do and what they are like. The first line becomes their tagline.',
  'Something only {name} knows. Other characters never see it, but {name} acts on it, and you can reveal it as the author.',
  'A few lines in their voice, one per line. They reach the model only when {name} speaks.',
  'The first thing {name} says or does when a new story starts with them.',
  'Other names let {name} be recognised when someone uses them. Tags help you find them later.',
]

const list = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean)

function payload(d: Draft, base: ItemData) {
  return {
    name: d.name.trim(),
    description: d.description,
    private: d.private,
    tags: list(d.tags),
    data: {
      ...base,
      aliases: list(d.aliases),
      example_dialogue: d.example_dialogue,
      first_message: d.first_message,
      pronouns: d.pronouns,
      favourite: d.favourite,
      persona: d.persona,
      portrait: d.portrait, // undefined drops the key: the portrait is removed
    },
  }
}

/** #/friends/new, #/you/new and #/friend/:id/edit?step=n */
export default function Editor({ id, persona = false, step = 1 }: { id?: number; persona?: boolean; step?: number }) {
  const { byId, loaded } = useLibrary()
  if (!loaded) return null
  const item = id === undefined ? undefined : byId.get(id)
  if (id !== undefined && !item) return <p className="ka-muted">There's no one here. They may have been deleted.</p>
  return <Form item={item} persona={persona} initialStep={Math.min(Math.max(step, 1), 6) - 1} />
}

function Form({ item, persona, initialStep }: { item?: Item; persona: boolean; initialStep: number }) {
  const { items, reload } = useLibrary()
  const [draft, setDraft] = useState(() => draftOf(item, persona))
  const [step, setStep] = useState(initialStep)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [run, error] = useAction()
  const draftRef = useRef(draft)
  const idRef = useRef(item?.id)
  const baseRef = useRef<ItemData>(item?.data ?? { palette: nextPalette(items) }) // keys the editor doesn't own
  const dirty = useRef(false)
  const chain = useRef(Promise.resolve())
  const box = useRef<HTMLTextAreaElement>(null)
  const stepRef = useRef(step)
  stepRef.current = step
  draftRef.current = draft

  const name = draft.name.trim() || (draft.persona ? 'you' : 'them')
  const fill = (s: string) => s.replaceAll('{name}', name)
  const home = draft.persona ? '/you' : '/friends'

  // Saves run one at a time, so a quick second edit can never create the item twice.
  const save = () => {
    chain.current = chain.current.then(async () => {
      const d = draftRef.current
      if (!d.name.trim()) return
      dirty.current = false
      setSaving(true)
      try {
        if (idRef.current === undefined) {
          const created = await api<Item>('/library', 'POST', { kind: 'character', ...payload(d, baseRef.current) })
          idRef.current = created.id
          history.replaceState(null, '', href(`/friend/${created.id}/edit?step=${stepRef.current + 1}`))
        } else {
          await api(`/library/${idRef.current}`, 'PATCH', payload(d, baseRef.current))
        }
        setSaveError('')
        reload()
      } catch (e) {
        setSaveError((e as Error).message)
      } finally {
        setSaving(false)
      }
    })
    return chain.current
  }

  const set = (patch: Partial<Draft>) => {
    dirty.current = true
    setDraft((d) => ({ ...d, ...patch }))
  }
  useEffect(() => {
    if (!dirty.current) return
    const t = setTimeout(save, 700)
    return () => clearTimeout(t)
  }, [draft]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => void (dirty.current && save()), []) // eslint-disable-line react-hooks/exhaustive-deps

  const goStep = (n: number) => {
    if (dirty.current) save()
    setStep(n)
    if (idRef.current !== undefined) history.replaceState(null, '', href(`/friend/${idRef.current}/edit?step=${n + 1}`))
  }
  const finish = async () => {
    await save()
    go(idRef.current === undefined ? home : `${draft.persona ? '/you' : '/friend'}/${idRef.current}`) // their profile
  }
  const start = (text: string) => {
    const field = (['description', 'private', 'example_dialogue', 'first_message'] as const)[step - 1]
    const now = draft[field]
    set({ [field]: (now && !now.endsWith('\n') ? now + '\n' : now) + fill(text) })
    box.current?.focus()
  }

  const done = STEPS.map((s) => s.done(draft))
  const pct = Math.round((100 * done.filter(Boolean).length) / STEPS.length)
  const missing = STEPS.findIndex((_, i) => !done[i])
  const next = STEPS[step + 1]
  const named = !!draft.name.trim()

  const field = (label: string, key: 'description' | 'private' | 'example_dialogue' | 'first_message', placeholder: string) => (
    <label className="ka-label">
      {fill(label)}
      <textarea ref={box} className="k-textarea" rows={6} value={draft[key]} placeholder={fill(placeholder)} onChange={(e) => set({ [key]: e.target.value })} onBlur={save} />
    </label>
  )

  return (
    <>
      <div className="ka-editor-top">
        <a className="ka-back" href={href(home)}>
          <Icon name="left" size={16} />
          {draft.persona ? 'You' : 'Friends'}
        </a>
        <span className="ka-muted ka-small" role="status">{saving ? 'Saving…' : 'Saved as you go'}</span>
      </div>
      <ErrorLine error={error || saveError} />
      <div className="ka-editor">
        <nav className="k-glass ka-steps" aria-label="Steps">
          <span className="k-display ka-steps__title">{item ? `Edit ${item.name}` : draft.persona ? 'Make a persona' : 'Add a friend'}</span>
          {STEPS.map((s, i) => (
            <button key={s.title} type="button" className={`k-step${done[i] && i !== step ? ' is-done' : ''}`} aria-current={i === step ? 'step' : undefined} disabled={!named && i > 0} onClick={() => goStep(i)}>
              <span className="k-step__dot">{done[i] && i !== step ? <Icon name="check" size={16} /> : i + 1}</span>
              {s.title}
            </button>
          ))}
          {item && (
            <button type="button" className="k-btn k-btn--danger k-btn--sm ka-steps__delete" onClick={() => setDeleting(true)}>
              <Icon name="x" size={15} />
              Delete {item.name}
            </button>
          )}
        </nav>

        <section className="k-glass ka-editor__main" aria-labelledby="ka-step-title">
          <span className="ka-step-eyebrow">Step {step + 1} of 6</span>
          <h2 id="ka-step-title" className="k-display ka-step-title">{STEPS[step].title}</h2>
          <p className="ka-step-help">{fill(HELP[step])}</p>

          {step === 0 && (
            <div className="ka-form">
              <label className="ka-label">
                Name
                <input className="k-input ka-input-lg" value={draft.name} placeholder={draft.persona ? 'Your name in the story' : 'Wren'} autoFocus onChange={(e) => set({ name: e.target.value })} onBlur={save} />
              </label>
              <div className="ka-upload">
                <Portrait item={{ data: { palette: baseRef.current.palette, portrait: draft.portrait } } as Item} name={draft.name || '?'} className="ka-upload__preview" />
                <div className="ka-stack">
                  <label className="k-btn">
                    <Icon name="image" size={17} />
                    {draft.portrait ? 'Change the portrait' : 'Upload a portrait'}
                    <input type="file" className="k-sr" accept="image/png,image/jpeg,image/gif,image/webp" onChange={(e) => {
                      const file = e.target.files?.[0]
                      e.target.value = ''
                      if (file) run(async () => set({ portrait: (await upload(file)).name }))
                    }} />
                  </label>
                  {draft.portrait && <button type="button" className="k-btn k-btn--ghost k-btn--sm" onClick={() => set({ portrait: undefined })}>Remove the portrait</button>}
                  <span className="ka-muted ka-small">PNG, JPEG, GIF or WebP, up to 10 MB. Without one, their initials stand in.</span>
                </div>
              </div>
              <div className="k-field">
                <span>Pronouns</span>
                <Seg label="Pronouns" value={draft.pronouns} onChange={(pronouns) => set({ pronouns })} options={[['she', 'she / her'], ['he', 'he / him'], ['they', 'they / them']]} />
              </div>
              <div className="ka-row ka-row--gap">
                <Chip icon="heart" pressed={draft.favourite} onClick={() => set({ favourite: !draft.favourite })}>Favourite</Chip>
                <Chip icon="user" pressed={draft.persona} onClick={() => set({ persona: !draft.persona })}>This is me</Chip>
              </div>
            </div>
          )}
          {step === 1 && field('{name} is…', 'description', 'A lamplighter’s apprentice who talks to gulls.')}
          {step === 2 && field('Only {name} knows…', 'private', 'Write it the way {name} would never say it out loud.')}
          {step === 3 && field('{name} says…', 'example_dialogue', '{name}: Coin first. Questions after.')}
          {step === 4 && field('{name} opens with…', 'first_message', '*slides a sealed letter across the table* You’re late.')}
          {step === 5 && (
            <div className="ka-form">
              <label className="ka-label">
                Other names
                <input className="k-input" value={draft.aliases} placeholder="the courier, Mir" onChange={(e) => set({ aliases: e.target.value })} onBlur={save} />
              </label>
              <label className="ka-label">
                Tags
                <input className="k-input" value={draft.tags} placeholder="Courier, Loyal, Wary" onChange={(e) => set({ tags: e.target.value })} onBlur={save} />
              </label>
            </div>
          )}

          {STARTERS[step] && (
            <div className="ka-starters">
              <span>Stuck? Start from</span>
              <div className="ka-row ka-row--gap">
                {STARTERS[step].map(([label, text]) => (
                  <button key={label} type="button" className="ka-starter" onClick={() => start(text)}>{label}</button>
                ))}
              </div>
            </div>
          )}

          <div className="ka-editor__foot">
            <button type="button" className="k-btn" disabled={step === 0} onClick={() => goStep(step - 1)}>
              <Icon name="left" size={17} />
              Back
            </button>
            <div className="ka-row ka-row--gap">
              {next && <button type="button" className="k-btn k-btn--ghost" disabled={!named} onClick={() => goStep(step + 1)}>Skip for now</button>}
              {next ? (
                <button type="button" className="k-btn k-btn--dark k-btn--lg" disabled={!named} onClick={() => goStep(step + 1)}>
                  <Icon name="arrow" size={17} />
                  Next: {next.title}
                </button>
              ) : (
                <button type="button" className="k-btn k-btn--dark k-btn--lg" disabled={!named} onClick={finish}>
                  <Icon name="check" size={17} />
                  Done
                </button>
              )}
            </div>
          </div>
        </section>

        <aside className="ka-editor__aside" aria-label="Live profile preview">
          <Portrait item={{ data: { palette: baseRef.current.palette, portrait: draft.portrait } } as Item} name={draft.name || '?'} className="ka-live">
            <div className="k-nameplate">
              <span className="k-display ka-live__name">{draft.name || 'New friend'}</span>
              <span className="ka-live__tagline">{draft.description.split('\n')[0] || 'Just added. Finish their profile.'}</span>
            </div>
          </Portrait>
          <div className="k-glass ka-nudge">
            <span className="k-ring" style={{ '--p': pct, '--s': '62px' } as CSSProperties}>{pct}%</span>
            <span className="ka-stack ka-stack--tight">
              <span className="ka-nudge__title">{missing < 0 ? `${name} is ready` : fill(STEPS[missing].nudge[0])}</span>
              <span className="ka-muted ka-small">{missing < 0 ? 'Start a story whenever you like.' : STEPS[missing].nudge[1]}</span>
            </span>
          </div>
          <ul className="k-glass ka-checklist">
            {STEPS.slice(0, Math.max(step + 2, 2)).map((s, i) => (
              <li key={s.title} className={i === step ? 'is-now' : done[i] ? 'is-done' : ''}>
                <Icon name={done[i] && i !== step ? 'check' : s.icon} size={15} />
                {i === step ? `${s.short} · writing now` : s.short}
              </li>
            ))}
          </ul>
        </aside>
      </div>

      {item && (
        <Dialog open={deleting} onClose={() => setDeleting(false)} title={`Delete ${item.name}?`}>
          <p className="ka-muted">Stories {item.name} is in keep their own copy. Only this profile goes. This can't be undone.</p>
          <div className="ka-row ka-row--end">
            <button type="button" className="k-btn" onClick={() => setDeleting(false)}>Keep {item.name}</button>
            <button
              type="button"
              className="k-btn k-btn--dark"
              onClick={() =>
                run(async () => {
                  dirty.current = false
                  await api(`/library/${item.id}`, 'DELETE')
                  reload()
                  go(home)
                })
              }
            >
              Delete {item.name}
            </button>
          </div>
        </Dialog>
      )}
    </>
  )
}
