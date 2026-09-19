import { useState, type CSSProperties } from 'react'
import sprite from './design/sprite.svg?raw'
import { Candy, Chip, Dialog, Field, Glass, Icon, Menu, Prose, Seg, Tier, type CandyColor } from './ui'

// #/dev/kit: the vendored design system rendered through the app's own components, to check the
// base layer. Temporary: removed in the final cleanup (task 38). Inline styles on purpose.

const icons = [...sprite.matchAll(/id="i-([\w-]+)"/g)].map((m) => m[1])
const candies: CandyColor[] = ['blue', 'pink', 'purple', 'green', 'orange', 'gold']
const row = { display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' } as const
const h2 = { margin: '8px 0 0', fontSize: 22, fontWeight: 800 } as const

export default function Kit() {
  const [chip, setChip] = useState('All')
  const [seg, setSeg] = useState<'auto' | 'on' | 'off'>('auto')
  const [dialog, setDialog] = useState(false)
  return (
    <main className="k-sky" style={{ minHeight: '100%', padding: '40px 64px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', gap: 18 }}>
      <h1 className="k-display" style={{ fontSize: 64, margin: 0 }}>Kataki RPAI</h1>

      <h2 style={h2}>Fonts</h2>
      <p className="k-display" style={{ fontSize: 40, margin: 0 }}>Chewy · Good evening, Aren</p>
      <p style={{ fontSize: 16, margin: 0, fontWeight: 600 }}>Figtree · Friends, Chats, Places, Activity. <i>Italic 400</i> <b>Bold 800</b></p>
      <p style={{ fontFamily: 'var(--k-font-story)', fontSize: 19, margin: 0 }}>
        Newsreader · Quickly, while he’s gone. <i>I hid the guild ledger under the third floorboard.</i>
      </p>
      <p className="k-mono" style={{ fontSize: 13, margin: 0 }}>JetBrains Mono · qwen3.5-9b · 127.0.0.1:8080 · ~7,300 / 16,384 tokens</p>

      <h2 style={h2}>Icons ({icons.length})</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(96px, 1fr))', gap: 8 }}>
        {icons.map((name) => (
          <div key={name} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, padding: '12px 4px', borderRadius: 12, background: 'rgba(255,255,255,.6)' }}>
            <Icon name={name} size={24} />
            <code style={{ fontSize: 10.5 }}>{name}</code>
          </div>
        ))}
      </div>

      <h2 style={h2}>Buttons and orb</h2>
      <div style={row}>
        <button className="k-btn k-btn--dark"><Icon name="plus" />Add a friend</button>
        <button className="k-btn k-btn--primary">Primary</button>
        <button className="k-btn"><Icon name="users" />Start a group scene</button>
        <button className="k-btn k-btn--ghost">Skip for now</button>
        <button className="k-btn k-btn--danger k-btn--sm">Remove</button>
        <button className="k-btn k-btn--lg" onClick={() => setDialog(true)}>Open a dialog</button>
        <Menu label="More">
          <button><Icon name="pushpin" />Pin</button>
          <button><Icon name="x" />Delete</button>
        </Menu>
        <button className="k-orb" aria-label="Dive in" />
        <button className="k-orb" style={{ '--s': '74px' } as CSSProperties} aria-label="Dive back in" />
      </div>

      <h2 style={h2}>Chips, tags, status, segmented</h2>
      <div style={row}>
        {['All', 'One-to-one', 'Groups'].map((c) => (
          <Chip key={c} pressed={chip === c} onClick={() => setChip(c)}>{c}</Chip>
        ))}
        <Chip icon="spark">Memories</Chip>
        <span className="k-tag">Courier</span>
        <span className="k-status">At The Gull · Year 7</span>
        <span className="k-status k-status--idle">Not in a story yet</span>
        <span className="k-status k-status--warn">key stored</span>
        <Seg label="Thinking" value={seg} onChange={setSeg} options={[['auto', 'As the model likes'], ['on', 'On'], ['off', 'Off']]} />
      </div>

      <h2 style={h2}>Candy tiles and filters</h2>
      <div style={row}>
        {candies.map((c) => <Candy key={c} icon="grid" color={c} />)}
        {candies.map((c, i) => (
          <button key={c} className="k-candy-filter" aria-pressed={i === 0}>
            <Candy icon={['grid', 'heart', 'book', 'spark', 'users', 'star'][i]} color={c} />
            {c}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
        <Glass title="Glass card" action={<button className="k-btn k-btn--sm">Edit</button>}>
          <Field label="Name"><input className="k-input" defaultValue="Mira" /></Field>
          <Field label="Pronouns">
            <select className="k-select" defaultValue="she"><option>she</option><option>he</option><option>they</option></select>
          </Field>
        </Glass>
        <div className="k-scene" style={{ borderRadius: 28, padding: 22, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={row}><Tier tier="sharp" /><Tier tier="hazy" /><Tier tier="forgotten" /></div>
          <div className="k-line__body"><Prose text={'*frowns* The lighthouse? I could have sworn…\nIt was **behind the bar**.'} /></div>
        </div>
      </div>

      <Dialog open={dialog} onClose={() => setDialog(false)} title="A native dialog">
        <p style={{ margin: 0 }}>Esc closes it and focus returns to the button that opened it.</p>
        <button className="k-btn k-btn--dark" onClick={() => setDialog(false)}>Done</button>
      </Dialog>
    </main>
  )
}
