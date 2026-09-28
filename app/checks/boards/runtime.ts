// A stand-in for the Claude Design canvas runtime, so the handoff boards
// (docs/handoff/kataki-handoff/boards/*.dc.html) render in a plain browser for the side-by-side
// check (README.md › Definition of done). Served as the boards' ./support.js by shoot.cjs.
// It covers what the boards use: <x-import>, <dc-import>, <sc-if>, <sc-for>, {{path}} values, and
// a DCLogic class with renderVals(), props and state.
import * as React from 'react'
import * as ReactDOM from 'react-dom'
import { createRoot } from 'react-dom/client'

const W = window as any
W.React = React
W.ReactDOM = ReactDOM

class DCLogic extends React.Component<any, any> {
  state: any = {}
  renderVals(): any { return {} }
  render() { return build((this.constructor as any).__template, this.renderVals() || {}) }
}

type Board = { template: Element; Component: any; defaults: Record<string, any> }
const boards: Record<string, Board> = {}

function parseBoard(doc: Document): Board {
  const script = doc.querySelector('script[data-dc-script]')!
  const Component = new Function('DCLogic', `${script.textContent}; return Component`)(DCLogic)
  const spec = JSON.parse(script.getAttribute('data-props') || '{}')
  const defaults: Record<string, any> = {}
  for (const [k, v] of Object.entries<any>(spec)) if (!k.startsWith('$') && 'default' in v) defaults[k] = v.default
  const template = doc.querySelector('x-dc')!
  Component.__template = template
  return { template, Component, defaults }
}

async function load(name: string, doc?: Document) {
  if (boards[name]) return
  if (!doc) {
    doc = new DOMParser().parseFromString(await (await fetch(`${name}.dc.html`)).text(), 'text/html')
    doc.querySelectorAll('helmet > style').forEach((n) => document.head.appendChild(n)) // an embedded board's own styles
  }
  boards[name] = parseBoard(doc)
  for (const d of doc.querySelectorAll('dc-import')) await load(d.getAttribute('name')!)
}

const get = (vals: any, path: string) => path.trim().split('.').reduce((o, k) => (o == null ? o : o[k]), vals)
const ONE = /^\{\{([^}]+)\}\}$/
const value = (raw: string, vals: any) => {
  const m = raw.match(ONE)
  if (m) return get(vals, m[1])
  return raw.replace(/\{\{([^}]+)\}\}/g, (_, p) => { const v = get(vals, p); return v == null || v === false ? '' : String(v) })
}
const camel = (s: string) => s.replace(/-([a-z])/g, (_, c) => c.toUpperCase())
const styleObject = (s: string) => Object.fromEntries(s.split(';').map((d) => d.split(/:(.*)/s)).filter(([k, v]) => k.trim() && v != null)
  .map(([k, v]) => [k.trim().startsWith('--') ? k.trim() : camel(k.trim()), v.trim()]))
const BOOL = new Set(['disabled', 'checked', 'hidden', 'readonly', 'selected', 'multiple', 'autofocus', 'open', 'required'])
const RENAME: Record<string, string> = { class: 'className', for: 'htmlFor', tabindex: 'tabIndex', readonly: 'readOnly', autofocus: 'autoFocus', colspan: 'colSpan', rowspan: 'rowSpan', maxlength: 'maxLength', viewbox: 'viewBox' }

function props(el: Element, vals: any, component: boolean) {
  const out: Record<string, any> = {}
  for (const a of el.attributes) {
    const n = a.name
    if (n === 'component-from-global-scope' || n.startsWith('hint-') || (el.localName === 'dc-import' && n === 'name')) continue
    let v: any = value(a.value, vals)
    let key = RENAME[n] ?? n
    if (typeof v === 'function' || /^on-?[a-z]/.test(n) && n !== 'on') key = 'on' + camel(n.replace(/^on-?/, '')).replace(/^./, (c) => c.toUpperCase())
    else if (component && !n.startsWith('aria-') && !n.startsWith('data-')) key = RENAME[n] ?? camel(n)
    if (key === 'style' && typeof v === 'string') v = styleObject(v)
    if (!component && BOOL.has(n) && v === '') v = true
    out[key] = v
  }
  return out
}

function kids(el: Element, vals: any): React.ReactNode[] {
  const out: React.ReactNode[] = []
  el.childNodes.forEach((n) => { const r = build(n, vals); if (r !== null) out.push(r) })
  return out
}

function build(node: Node, vals: any): React.ReactNode {
  if (node.nodeType === Node.TEXT_NODE) {
    const s = node.textContent!
    if (!s.trim() && s.includes('\n')) return null
    const m = s.trim().match(ONE)
    if (m) return get(vals, m[1]) ?? null
    return value(s, vals) as string
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return null
  const el = node as Element
  const tag = el.localName
  if (tag === 'x-dc') return React.createElement(React.Fragment, null, ...kids(el, vals))
  if (tag === 'helmet' || tag === 'script') return null
  if (tag === 'sc-if') return value(el.getAttribute('value') || '', vals) ? React.createElement(React.Fragment, null, ...kids(el, vals)) : null
  if (tag === 'sc-for') {
    const list = value(el.getAttribute('list') || '', vals) || []
    const as = el.getAttribute('as') || 'item'
    return (list as any[]).map((item, i) => React.createElement(React.Fragment, { key: i }, ...kids(el, { ...vals, [as]: item, $index: i })))
  }
  if (tag === 'x-import') {
    const type = get(W, el.getAttribute('component-from-global-scope')!)
    if (!type) { console.warn('missing component', el.getAttribute('component-from-global-scope')); return null }
    const c = kids(el, vals)
    return React.createElement(type, props(el, vals, true), ...c)
  }
  if (tag === 'dc-import') {
    const b = boards[el.getAttribute('name')!]
    return React.createElement(b.Component, { ...b.defaults, ...props(el, vals, true) })
  }
  const c = kids(el, vals)
  return React.createElement(tag, props(el, vals, false), ...(c.length ? c : []))
}

const query = () => {
  const out: Record<string, any> = {}
  new URLSearchParams(location.search).forEach((v, k) => { try { out[k] = JSON.parse(v) } catch { out[k] = v } })
  return out
}

document.addEventListener('DOMContentLoaded', async () => {
  const x = document.querySelector('x-dc')!
  x.querySelectorAll('helmet > *').forEach((n) => document.head.appendChild(n))
  const name = location.pathname.split('/').pop()!.replace(/\.dc\.html$/, '')
  await load(name, document)
  x.remove()
  const root = document.createElement('div')
  root.id = 'board'
  document.body.appendChild(root)
  const b = boards[name]
  createRoot(root).render(React.createElement(b.Component, { ...b.defaults, ...query() }))
  await document.fonts.ready
  setTimeout(() => (document.documentElement.dataset.board = 'ready'), 300)
})
