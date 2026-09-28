// What you can do to a character from anywhere: CharacterMenu (OVERLAYS-AND-MENUS.md) and the
// delete dialog (E5), shared by Characters and the profile.
import { useState } from 'react'
import { api, type Item, type StorySummary } from '../api'
import { pronoun, storiesWith } from '../characters'
import { K } from '../ds'
import { Overlay, toast, type MenuItem } from '../overlay'
import { t } from '../strings'

type Go = (to: string) => void

export function characterMenu(c: Item, stories: StorySummary[] | undefined, go: Go, done: () => void, onDelete: () => void): MenuItem[] {
  const last = storiesWith(c, stories)[0]
  return [
    { label: t('menu.continueWith'), detail: t('menu.continueDetail', { name: c.name }), icon: 'play', disabled: !last, onSelect: () => last && go(`/story/${last.id}`) },
    { label: t('menu.newStoryWith', { name: c.name }), icon: 'plus', onSelect: () => go(`/stories/new?with=${c.id}`) },
    { label: t('menu.edit'), icon: 'edit', onSelect: () => go(`/characters/${c.id}/edit`) },
    { label: t(c.data.favourite ? 'menu.unfav' : 'menu.fav'), icon: 'star', onSelect: () => api(`/library/${c.id}`, 'PATCH', { data: { ...c.data, favourite: !c.data.favourite } }).then(done) },
    {
      label: t('menu.duplicate'), icon: 'layers',
      onSelect: () => api<Item>('/library', 'POST', { kind: c.kind, name: `${c.name} (2)`, description: c.description, private: c.private, data: { ...c.data, favourite: false, edits: 0 }, tags: c.tags })
        .then((copy) => { done(); toast(t('toast.copied', { name: copy.name }), {}, 4000) }),
    },
    { label: t('menu.exportCard'), detail: t('menu.exportCardDetail'), icon: 'download', onSelect: () => exportCard(c) },
    { divider: true },
    { label: t('menu.delete', { name: c.name }), icon: 'trash', danger: true, onSelect: onDelete },
  ]
}

/** A Character Card V2 as JSON: what other apps read. The portrait stays in Kataki. */
function exportCard(c: Item) {
  const card = {
    spec: 'chara_card_v2', spec_version: '2.0',
    data: {
      name: c.name, description: c.description, personality: c.data.tagline ?? '', scenario: '',
      first_mes: c.data.first_message ?? '', mes_example: c.data.example_dialogue ?? '',
      creator_notes: '', system_prompt: '', post_history_instructions: '', alternate_greetings: [], tags: c.tags,
      creator: '', character_version: '', extensions: { kataki: { secret: c.private } },
    },
  }
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([JSON.stringify(card, null, 2)], { type: 'application/json' }))
  a.download = `${c.name.replace(/[\\/:*?"<>|]/g, '')}.json`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 30_000)
}

/** E5: delete a character, and maybe their stories; soft for the length of the Undo toast. */
export function DeleteCharacter({ c, stories, onClose, onGone, onBack }: {
  c: Item; stories: StorySummary[] | undefined; onClose: () => void
  onGone: (hidden: boolean) => void // true: hide them now; false: the Undo was pressed
  onBack?: () => void
}) {
  const [also, setAlso] = useState('keep')
  const [typed, setTyped] = useState('')
  const theirs = storiesWith(c, stories)
  const ok = typed.trim() === c.name
  const go = () => {
    if (!ok) return
    onClose()
    onGone(true)
    onBack?.()
    toast(t('toast.characterDeleted', { name: c.name, n: also === 'delete' ? 0 : theirs.length, p: pronoun(c) }), { icon: 'trash',
      action: t('toast.undo'),
      onAction: () => onGone(false),
      onDone: async () => {
        if (also === 'delete') for (const s of theirs) await api(`/stories/${s.id}`, 'DELETE')
        await api(`/library/${c.id}`, 'DELETE')
      },
    })
  }
  return (
    <Overlay onClose={onClose}>
      <K.Dialog icon="trash" tone="bad" title={t('del.title', { name: c.name })} onClose={onClose}
        description={t('del.body', { stories: theirs.length })} note={t('del.note', { p: pronoun(c) })}
        actions={[
          <K.Button key="k" variant="ghost" onClick={onClose}>{t('del.keep', { p: pronoun(c) })}</K.Button>,
          <K.Button key="e" icon="download" onClick={() => exportCard(c)}>{t('del.export')}</K.Button>,
          <K.Button key="d" variant="danger" disabled={!ok} onClick={go}>{t('del.confirm', { name: c.name })}</K.Button>,
        ]}>
        {theirs.length > 0 && (
          <K.RadioGroup label={t('del.stories')} value={also} onChange={setAlso} options={[
            { value: 'keep', label: t('del.keepStories') },
            { value: 'delete', label: t('del.deleteStories', { n: theirs.length }) },
          ]} />
        )}
        <K.TextField label={t('del.type', { name: c.name })} value={typed} onChange={setTyped}
          error={typed && !ok && typed.length >= c.name.length ? t('del.mismatch') : undefined} />
      </K.Dialog>
    </Overlay>
  )
}
