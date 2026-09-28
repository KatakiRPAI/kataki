// StoryMenu (OVERLAYS-AND-MENUS.md, M1): a story card's ··· and right-click, on Home, Stories and Search.
import { api, type Book, type StorySummary } from '../api'
import { openMenu, toast, type MenuItem } from '../overlay'
import { t } from '../strings'

type Do = 'rename' | 'export' | 'delete'

/** `open` shows a dialog for the story; Stories has them, other pages send you there. */
export function storyMenu(s: StorySummary, go: (to: string) => void, done: () => void, open?: (what: Do) => void): MenuItem[] {
  const dialog = (what: Do) => () => (open ? open(what) : go(`/stories?story=${s.id}&do=${what}`))
  return [
    { label: t('stm.continue'), icon: 'play', onSelect: () => go(`/story/${s.id}`) },
    { label: t('stories.rename'), icon: 'edit', shortcut: ['F2'], onSelect: dialog('rename') },
    { label: t(s.pinned ? 'sm.unpin' : 'sm.pin'), icon: 'pushpin', onSelect: () => api(`/stories/${s.id}`, 'PATCH', { pinned: !s.pinned }).then(done) },
    { label: t('stm.move'), icon: 'book', onSelect: () => moveTo(s, done) },
    {
      label: t('stm.branch'), icon: 'swap', disabled: !s.last_line,
      onSelect: () => api<{ story_id: number }>(`/messages/${s.last_line!.id}/branch`, 'POST').then((b) => {
        toast(t('toast.branched', { story: `${s.title} · branch` }), { action: t('stm.open'), onAction: () => go(`/story/${b.story_id}`) }, 6000)
        done()
      }),
    },
    { label: t('sm.export'), icon: 'download', onSelect: dialog('export') },
    { divider: true },
    { label: t('sm.delete'), icon: 'trash', danger: true, onSelect: dialog('delete') },
  ]
}

/** Move to a book…: every book, and "not in a book". */
async function moveTo(s: StorySummary, done: () => void) {
  const books = await api<Book[]>('/books')
  const at = document.activeElement ?? document.body
  const file = (id: number | null) => api(`/stories/${s.id}`, 'PATCH', { book_id: id }).then(done)
  openMenu(at, [
    ...books.map((b): MenuItem => ({ label: b.title, icon: 'book', checked: s.book?.id === b.id, onSelect: () => file(b.id) })),
    { divider: true },
    { label: t('home.noBook'), checked: !s.book, onSelect: () => file(null) },
  ], t('stm.moveTitle'))
}
