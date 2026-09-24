import { useState } from 'react'
import { api, type Book, type StorySummary } from '../api'
import { Avatar, AvatarStack } from '../art'
import { dive, diveLink, go, href, useAction, useLibrary, useLoad } from '../hooks'
import { Dialog, ErrorLine, Field, Icon, Menu, SkyHeader } from '../ui'
import NewChat from './NewChat'

/** The stories of one book, in the order it reads. */
const inOrder = (stories: StorySummary[], book: Book) =>
  stories
    .filter((s) => s.book?.id === book.id)
    .sort((a, b) => (a.book!.order - b.book!.order) || a.id - b.id)

/** #/books and #/books/:id — shelves of stories, and the order they read in. */
export default function Books({ selected }: { selected?: number }) {
  const { byId } = useLibrary()
  const [books, reloadBooks, booksError] = useLoad(() => api<Book[]>('/books'), [])
  const [stories, reloadStories, storiesError] = useLoad(() => api<StorySummary[]>('/stories'), [])
  const [run, actionError, busy, forget] = useAction()
  const [naming, setNaming] = useState<{ book?: Book; open: boolean }>({ open: false })
  const [adding, setAdding] = useState(false)
  const [deleting, setDeleting] = useState<Book>()
  const [starting, setStarting] = useState(0) // n > 0: the new-story dialog, fresh each time

  const all = books ?? []
  const current = all.find((b) => b.id === selected) ?? all[0]
  const reload = () => {
    reloadBooks()
    reloadStories()
  }

  const save = (form: HTMLFormElement) =>
    run(async () => {
      const data = new FormData(form)
      const body = { title: String(data.get('title') ?? '').trim(), blurb: String(data.get('blurb') ?? '').trim() }
      if (!body.title) return
      const book = naming.book
        ? await api<Book>(`/books/${naming.book.id}`, 'PATCH', body)
        : await api<Book>('/books', 'POST', body)
      setNaming({ open: false })
      reloadBooks()
      if (!naming.book) go(`/books/${book.id}`)
    })

  const remove = (book: Book) =>
    run(async () => {
      await api(`/books/${book.id}`, 'DELETE')
      setDeleting(undefined)
      reload()
      go('/books')
    })

  const put = (story: StorySummary, book_id: number | null) =>
    run(async () => {
      await api(`/stories/${story.id}`, 'PATCH', { book_id })
      setAdding(false)
      reload()
    })

  /** Swap a story with the one above or below it, and save the whole order. The next click has to
   *  read the order this one wrote, so the arrows stay disabled until the fresh list lands. */
  const move = (book: Book, story: StorySummary, by: -1 | 1) =>
    run(async () => {
      const order = inOrder(stories ?? [], book).map((s) => s.id)
      const at = order.indexOf(story.id)
      if (at + by < 0 || at + by >= order.length) return
      order.splice(at + by, 0, ...order.splice(at, 1))
      await api(`/books/${book.id}/stories`, 'POST', { story_ids: order })
      await reloadStories()
    })

  const shelf = current ? inOrder(stories ?? [], current) : []
  const loose = (stories ?? []).filter((s) => s.book?.id !== current?.id)

  return (
    <>
      <SkyHeader title="Books">
        <button type="button" className="k-btn k-btn--dark k-btn--lg" onClick={() => setNaming({ open: true })}>
          <Icon name="plus" size={17} />
          New book
        </button>
      </SkyHeader>
      <ErrorLine error={booksError || storiesError || actionError} />

      {books && all.length === 0 && (
        <p className="ka-muted ka-empty-note">
          No books yet. A book gathers stories that belong together, and says what order they read in.
        </p>
      )}

      <div className="ka-books">
        {all.length > 0 && (
          <section className="k-glass ka-books__shelf" aria-label="Books">
            <ul className="ka-booklist">
              {all.map((b) => (
                <li key={b.id}>
                  <a
                    className="ka-booklist__item"
                    href={href(`/books/${b.id}`)}
                    aria-current={b.id === current?.id ? 'true' : undefined}
                  >
                    <span className="ka-booklist__spine" aria-hidden="true">
                      <Icon name="book" size={18} />
                    </span>
                    <span className="ka-booklist__text">
                      <span className="ka-ellipsis">{b.title}</span>
                      <span className="ka-muted ka-small">
                        {b.stories} {b.stories === 1 ? 'story' : 'stories'}
                      </span>
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}

        {current && (
          <section className="k-glass ka-book" aria-label={current.title}>
            <div className="ka-book__head">
              <div className="ka-stack ka-stack--tight">
                <h2 className="k-display ka-book__title">{current.title}</h2>
                {current.blurb && <p className="ka-muted">{current.blurb}</p>}
              </div>
              <Menu label={`More for ${current.title}`}>
                <button type="button" onClick={() => setNaming({ book: current, open: true })}>
                  <Icon name="edit" />
                  Rename this book
                </button>
                <button type="button" onClick={() => setDeleting(current)}>
                  <Icon name="x" />
                  Delete the book
                </button>
              </Menu>
            </div>

            <ol className="ka-shelf">
              {shelf.map((s, i) => (
                <li key={s.id} className="ka-shelf__row">
                  <span className="ka-shelf__n" aria-hidden="true">{i + 1}</span>
                  {s.cast.length > 1 ? (
                    <AvatarStack people={s.cast.map((c) => ({ item: byId.get(c.lib_item_id ?? -1), name: c.name }))} size={34} />
                  ) : (
                    <Avatar item={byId.get(s.cast[0]?.lib_item_id ?? -1)} name={s.cast[0]?.name ?? s.title} size={40} />
                  )}
                  <span className="ka-shelf__text">
                    <a className="ka-shelf__title ka-ellipsis" {...diveLink(`/story/${s.id}`)}>{s.title}</a>
                    <span className="ka-muted ka-small">
                      {[s.clock, `${s.messages} ${s.messages === 1 ? 'line' : 'lines'}`].join(' · ')}
                    </span>
                  </span>
                  <span className="ka-row">
                    <button
                      type="button" className="k-btn k-btn--ghost k-btn--sm" disabled={busy || i === 0}
                      aria-label={`Move ${s.title} earlier`} onClick={() => move(current, s, -1)}
                    >
                      <Icon name="up" size={14} />
                    </button>
                    <button
                      type="button" className="k-btn k-btn--ghost k-btn--sm" disabled={busy || i === shelf.length - 1}
                      aria-label={`Move ${s.title} later`} onClick={() => move(current, s, 1)}
                    >
                      <Icon name="down" size={14} />
                    </button>
                    <Menu label={`More for ${s.title}`}>
                      <button type="button" onClick={() => go(`/chats/${s.id}`)}>
                        <Icon name="chat" />
                        Open in Chats
                      </button>
                      <button type="button" onClick={() => put(s, null)}>
                        <Icon name="x" />
                        Take out of this book
                      </button>
                    </Menu>
                  </span>
                </li>
              ))}
            </ol>

            {stories && shelf.length === 0 && <p className="ka-muted">Nothing on this shelf yet.</p>}
            <button
              type="button"
              className="k-btn ka-self-start"
              onClick={() => setAdding(true)}
              disabled={!stories || loose.length === 0}
            >
              <Icon name="plus" size={16} />
              Add a story
            </button>
            <button type="button" className="k-btn k-btn--dark ka-self-start" onClick={() => setStarting((n) => Math.abs(n) + 1)}>
              <Icon name="ff" size={16} />
              Start a new story in this book
            </button>
          </section>
        )}
      </div>

      <Dialog
        open={naming.open}
        onClose={() => { setNaming({ open: false }); forget() }}
        title={naming.book ? 'Rename this book' : 'New book'}
      >
        <form
          className="ka-form"
          onSubmit={(e) => {
            e.preventDefault()
            save(e.currentTarget)
          }}
        >
          <Field label="Title">
            <input name="title" className="k-input" defaultValue={naming.book?.title ?? ''} required maxLength={200} />
          </Field>
          <Field label="What it is about">
            <textarea name="blurb" className="k-input ka-textarea-sm" defaultValue={naming.book?.blurb ?? ''} rows={2} />
          </Field>
          <div className="ka-row ka-row--end">
            <button type="button" className="k-btn" onClick={() => setNaming({ open: false })}>Cancel</button>
            <button type="submit" className="k-btn k-btn--dark" disabled={busy}>
              {naming.book ? 'Save' : 'Make the book'}
            </button>
          </div>
        </form>
      </Dialog>

      <Dialog open={adding} onClose={() => { setAdding(false); forget() }} title={`Add a story to ${current?.title ?? 'this book'}`}>
        <ul className="ka-threads ka-pick">
          {loose.map((s) => (
            <li key={s.id}>
              <button type="button" className="ka-pick__row" disabled={busy} onClick={() => current && put(s, current.id)}>
                <Avatar item={byId.get(s.cast[0]?.lib_item_id ?? -1)} name={s.cast[0]?.name ?? s.title} size={36} />
                <span className="ka-shelf__text">
                  <span className="ka-ellipsis">{s.title}</span>
                  <span className="ka-muted ka-small">{s.book ? `in ${s.book.title}` : 'in no book'}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </Dialog>

      <Dialog open={!!deleting} onClose={() => { setDeleting(undefined); forget() }} title="Delete this book?">
        <p className="ka-muted">
          “{deleting?.title}” goes. Its stories stay exactly where they are — they just stop being a book.
        </p>
        <div className="ka-row ka-row--end">
          <button type="button" className="k-btn" onClick={() => setDeleting(undefined)}>Keep it</button>
          <button type="button" className="k-btn k-btn--dark" disabled={busy} onClick={() => deleting && remove(deleting)}>
            Delete the book
          </button>
        </div>
      </Dialog>
      {current && (
        <NewChat key={`new-${Math.abs(starting)}`} open={starting > 0} preset={{ book: current.id }}
          onClose={() => setStarting((n) => -Math.abs(n))} onCreated={(story) => dive(`/story/${story.id}`)} />
      )}
    </>
  )
}
