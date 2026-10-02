import { spawn, type ChildProcess } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { once } from 'node:events'
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { createInterface } from 'node:readline'
import { setTimeout as sleep } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'
import { app, BrowserWindow, dialog, ipcMain, screen, shell } from 'electron'
import { add, cleanName, current, forget, kind, load, lost, moveLibrary, needsPicker, pinOk, rename, save, setPin, shown, synced, type Profile, type Profiles } from './profiles.js'

const here = dirname(fileURLToPath(import.meta.url)) // app/dist-electron
const appRoot = join(here, '..')
const repoRoot = join(appRoot, '..')
const smoke = process.argv.includes('--smoke')

let engine: ChildProcess | undefined
let quitting = false

function fail(message: string): void {
  if (quitting) return
  if (smoke) console.log(`SMOKE FAIL: ${message}`)
  else dialog.showErrorBox('Kataki engine stopped', message)
  app.exit(1)
}

// The dev library and downloaded models stay in the repo (KATAKI_HOME moves them, e.g. for a scratch run).
const home = process.env.KATAKI_HOME ? resolve(process.env.KATAKI_HOME) : join(repoRoot, '.dev')

// Profiles (docs/specs/2026-10-02-profiles-and-accounts.md §2): each is a name and the folder that
// holds its library; the list is ours, the engine opens one library. The smoke test and KATAKI_DB
// (e.g. .dev/demo.db; a relative path is from the repo root) open one library and skip the list.
const single = smoke || !!process.env.KATAKI_DB
const profilesFile = () => join(app.getPath('userData'), 'profiles.json')
let profiles: Profiles = { last: 'main', profiles: [{ id: 'main', name: 'Main', folder: home }] }
const keep = (p: Profiles): Profiles => { save(profilesFile(), (profiles = p)); return p }

/** The open profile's library can't be used. Ask what to do; returns once there is something new to try. */
function choose(message: string, detail: string, can: { retry?: boolean; locate?: boolean }): void {
  for (;;) {
    const me = current(profiles)
    const others = profiles.profiles.filter((p) => p.id !== me.id).slice(0, 3)
    const options: [string, Profile?][] = [...(can.retry ? [['Try again']] : []), ...(can.locate ? [['Find the folder…']] : []), ...others.map((p) => [`Open ${p.name}`, p]), ['Quit']] as [string, Profile?][]
    const [hit, other] = options[dialog.showMessageBoxSync({ type: 'warning', message, detail, buttons: options.map(([label]) => label), cancelId: options.length - 1, noLink: true })]
    if (other) { keep({ ...profiles, last: other.id }); return }
    if (hit === 'Try again') return
    if (hit === 'Quit') { quitting = true; app.exit(0); process.exit(0) }
    const folder = dialog.showOpenDialogSync({ title: `Where is ${me.name}?`, properties: ['openDirectory'] })?.[0]
    if (!folder) continue
    if (kind(folder) !== 'library') { dialog.showMessageBoxSync({ type: 'info', message: 'There is no Kataki library in that folder', detail: 'Choose the folder that holds library.db.' }); continue }
    const listed = add(profiles, me.name, folder) // already another profile's folder: open that one
    keep(listed.existing ? { ...profiles, last: listed.profile.id } : { ...profiles, profiles: profiles.profiles.map((p) => (p.id === me.id ? { ...p, folder } : p)) })
    return
  }
}

/** A library asked to be moved (Settings › Profiles) moves now, while nothing has it open. */
function moveIfAsked(): void {
  const { move, ...rest } = profiles
  if (!move) return
  const me = profiles.profiles.find((p) => p.id === move.id)
  try {
    if (!me) throw new Error('that profile is gone')
    moveLibrary(me.folder, move.to)
    keep({ ...rest, profiles: rest.profiles.map((p) => (p.id === me.id ? { ...p, folder: move.to, movedFrom: me.folder } : p)) })
  } catch (e) {
    keep(rest) // it stays where it was
    dialog.showMessageBoxSync({ type: 'warning', message: 'The library was not moved', detail: `It is still in its old folder, untouched.\n\n${e instanceof Error ? e.message : e}` })
  }
}

/** Ask which profile, and for its PIN if it has one (picker.html). Resolves once one is chosen; closing the window quits. */
function pick(): Promise<void> {
  return new Promise((chosen) => {
    const win = new BrowserWindow({ width: 440, height: 560, resizable: false, backgroundColor: '#0b1230', autoHideMenuBar: true, webPreferences: { preload: join(here, 'picker-preload.cjs') } })
    let done = false
    ipcMain.handle('kataki:picker:list', () => ({ last: current(profiles).id, profiles: profiles.profiles.map(shown).map(({ id, name, locked }) => ({ id, name, locked })) }))
    ipcMain.handle('kataki:picker:choose', async (_e, id: unknown, pin: unknown) => {
      const p = profiles.profiles.find((x) => x.id === id)
      if (!p) return false
      if (!pinOk(p, pin)) { await sleep(1000); return false } // a wrong guess costs a second
      keep({ ...profiles, last: p.id })
      done = true
      ipcMain.removeHandler('kataki:picker:list')
      ipcMain.removeHandler('kataki:picker:choose')
      chosen()
      win.close()
      return true
    })
    win.on('closed', () => { if (!done) { quitting = true; app.exit(0) } })
    void win.loadFile(join(appRoot, 'electron', 'picker.html'))
  })
}

/** The folder to open: the last profile's, once it is there. A library is never made at a path that went missing. */
async function libraryFolder(): Promise<string> {
  if (!existsSync(profilesFile())) mkdirSync(home, { recursive: true }) // the first run: the one folder made unasked
  profiles = load(profilesFile(), profiles.profiles[0])
  moveIfAsked()
  if (needsPicker(profiles)) await pick()
  for (;;) {
    const me = current(profiles)
    if (!lost(me)) {
      // remember that the library has been seen here, so an empty folder later reads as a loss
      if (!me.opened && kind(me.folder) === 'library') keep({ ...profiles, profiles: profiles.profiles.map((p) => (p.id === me.id ? { ...p, opened: true } : p)) })
      return me.folder
    }
    choose(`Kataki can’t find ${me.name}`, `Its library is not in:\n${me.folder}\n\nIf it is on a drive that isn’t plugged in, plug it in and try again.`, { retry: true, locate: true })
  }
}

/** The engine would not open the library (3: made by a newer Kataki, 4: open in another one). */
function libraryTrouble(code: number): void {
  if (quitting) return
  const me = current(profiles)
  if (code === 4) choose(`${me.name} is open in another Kataki`, 'Close the other one and try again, or open another profile.', { retry: true })
  else choose(`${me.name} was made by a newer Kataki`, 'Update Kataki to open it, or open another profile.', {})
  quitting = true
  app.relaunch()
  app.exit(0)
}

/** Settings › Profiles › Add: the shell asks for the folder, so the page never names a path. */
async function addProfile(win: BrowserWindow, name: unknown): Promise<Profile | null> {
  for (;;) {
    const folder = (await dialog.showOpenDialog(win, { title: 'Choose a folder for this profile', buttonLabel: 'Use this folder', properties: ['openDirectory', 'createDirectory'] })).filePaths[0]
    if (!folder) return null
    if (kind(folder) === 'other') {
      await dialog.showMessageBox(win, { type: 'info', message: 'That folder has other things in it', detail: 'Choose an empty folder for a new library, or a folder that already holds a Kataki library.' })
      continue
    }
    const where = synced(folder)
    if (where) {
      const { response } = await dialog.showMessageBox(win, { type: 'warning', message: `That folder is in ${where}`, detail: 'A folder that syncs or sits on a network can damage a library while Kataki has it open. A folder on this computer is safer.', buttons: ['Choose another folder', 'Use it anyway'], cancelId: 0, noLink: true })
      if (response === 0) continue
    }
    const added = add(profiles, cleanName(name), folder)
    keep(added.profiles)
    return added.profile
  }
}

let libraryDb = ''
async function startEngine(token: string, db: string): Promise<number> {
  // ponytail: dev layout only (the repo venv). M5 packaging swaps in the bundled runtime path.
  const python = join(repoRoot, 'engine', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
  libraryDb = db
  const args = ['-m', 'kataki', 'serve', '--parent-watch', '--db', db]
  // The engine watches its stdin: when this process ends for any reason, the pipe closes and it exits.
  const env = { ...process.env, KATAKI_TOKEN: token, KATAKI_HOME: home }
  engine = spawn(python, args, { env, stdio: ['pipe', 'pipe', 'inherit'] })
  engine.on('error', (err) => fail(`could not start ${python}: ${err.message}`))
  engine.on('exit', (code) => (!single && (code === 3 || code === 4) ? libraryTrouble(code) : fail(`engine exited with code ${code}`)))
  const [hello] = await once(createInterface({ input: engine.stdout! }), 'line')
  engine.stdout!.resume() // keep draining so the engine can never block on a full pipe
  return JSON.parse(hello).port
}

// The window comes back where it was (ROUTES.md › Window), if that place is still on a screen.
const boundsFile = () => join(app.getPath('userData'), 'window.json')
function keptBounds(): Partial<Electron.Rectangle> {
  try {
    const b = JSON.parse(readFileSync(boundsFile(), 'utf8')) as Electron.Rectangle
    const on = screen.getAllDisplays().some((d) => b.x >= d.workArea.x - 50 && b.y >= d.workArea.y - 50 && b.x < d.workArea.x + d.workArea.width && b.y < d.workArea.y + d.workArea.height)
    return on ? b : { width: b.width, height: b.height }
  } catch {
    return {}
  }
}

async function createWindow(port: number, token: string, crashed = false): Promise<BrowserWindow> {
  const work = screen.getPrimaryDisplay().workAreaSize // the design's 1440x900, capped to the screen
  const kept = keptBounds()
  const win = new BrowserWindow({
    width: Math.min(1440, work.width),
    height: Math.min(900, work.height),
    ...kept,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: '#c3dafc', // the Sky, so the first frame isn't white
    show: !smoke,
    webPreferences: {
      preload: join(here, 'preload.cjs'),
      additionalArguments: [`--kataki-port=${port}`, `--kataki-token=${token}`, ...(crashed ? ['--kataki-crashed'] : []), ...(single ? [] : ['--kataki-profiles'])],
    },
  })
  win.on('close', () => { try { writeFileSync(boundsFile(), JSON.stringify(win.getBounds())) } catch { /* next time, the default */ } })
  // Model output is untrusted text that can contain links: never open windows or leave the app.
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))
  // TextMenu (M1): Electron has no right-click menu in text; the page draws one, with spelling from here
  win.webContents.on('context-menu', (_e, p) => {
    if (!p.isEditable && !p.selectionText) return
    win.webContents.send('kataki:textmenu', { x: p.x, y: p.y, editable: p.isEditable, selection: !!p.selectionText, word: p.misspelledWord, suggestions: p.dictionarySuggestions.slice(0, 4) })
  })
  win.webContents.on('will-navigate', (event, url) => {
    if (new URL(url).origin !== new URL(win.webContents.getURL()).origin) event.preventDefault()
  })

  if (app.isPackaged) {
    await win.loadFile(join(appRoot, 'dist', 'index.html'))
  } else {
    const { createServer } = await import('vite')
    const vite = await createServer({ root: appRoot })
    await vite.listen()
    await win.loadURL(vite.resolvedUrls!.local[0])
  }
  return win
}

async function runSmoke(win: BrowserWindow): Promise<void> {
  // The renderer marks <html data-engine="ok|down"> after its health check.
  let state = ''
  for (let i = 0; i < 60 && !state; i++) {
    await sleep(250)
    state = await win.webContents.executeJavaScript('document.documentElement.dataset.engine ?? ""')
  }
  const ok = state === 'ok'
  console.log(`SMOKE ${ok ? 'PASS' : 'FAIL'}: engine ${state || 'never answered'}`)
  process.exitCode = ok ? 0 : 1
  app.quit() // the normal quit path, so engine shutdown is exercised too
}

app.on('before-quit', () => {
  quitting = true
  engine?.stdin?.end()
})
let starting = true // the picker closes before the main window opens: that is not the app closing
app.on('window-all-closed', () => { if (!starting) app.quit() })

// One Kataki at a time (ROUTES.md › Where the app starts): a second launch hands over to the
// first, which comes to the front, and quits.
if (!smoke && !app.requestSingleInstanceLock()) app.exit(0)
app.on('second-instance', () => {
  const win = BrowserWindow.getAllWindows()[0]
  if (win?.isMinimized()) win.restore()
  win?.focus()
})

// A3: a `running` mark lives in userData while Kataki is open and goes on a clean quit, so a
// mark found at launch means the last run ended without one.
const runningMark = () => join(app.getPath('userData'), 'running')
app.on('will-quit', () => rmSync(runningMark(), { force: true }))
// A restored backup is swapped in as the engine starts, so restoring ends in a restart (K12).
const EDITS = new Set(['cut', 'copy', 'paste', 'selectAll'])
ipcMain.on('kataki:edit', (e, what: string, word?: string) => {
  const wc = e.sender
  if (EDITS.has(what)) wc[what as 'cut']()
  else if (what === 'replace' && typeof word === 'string') wc.replaceMisspelling(word)
  else if (what === 'learn' && typeof word === 'string') wc.session.addWordToSpellCheckerDictionary(word)
})
ipcMain.on('kataki:restart', () => { app.relaunch(); app.quit() })
// Settings › General › Start with Windows: only when the person turns it on or off there.
ipcMain.on('kataki:startup', (_e, on: boolean) => app.setLoginItemSettings({ openAtLogin: !!on }))
// Settings › Data › Open folder: only the library's own folders, never a path the page names
ipcMain.on('kataki:reveal', (_e, what: string) => {
  const folders: Record<string, string> = { library: '', pictures: 'blobs', backups: 'backups' }
  if (Object.hasOwn(folders, what)) shell.openPath(join(dirname(libraryDb), folders[what]))
})
// Settings › Profiles. Forgetting a profile takes it off the list; its folder is never touched.
// The page is told a profile's name, folder and whether it has a PIN: never the PIN's hash.
const listing = () => ({ current: current(profiles).id, list: profiles.profiles.map(shown), ask: !!profiles.ask })
ipcMain.handle('kataki:profiles', listing)
ipcMain.handle('kataki:profile:add', async (e, name: unknown) => { const made = await addProfile(BrowserWindow.fromWebContents(e.sender)!, name); return made && shown(made) })
ipcMain.handle('kataki:profile:rename', (_e, id: unknown, name: unknown) => { keep(rename(profiles, String(id), cleanName(name))); return listing().list })
ipcMain.handle('kataki:profile:forget', (_e, id: unknown) => { keep(forget(profiles, String(id))); return listing().list })
ipcMain.handle('kataki:profile:ask', (_e, on: unknown) => { keep({ ...profiles, ask: !!on }); return listing() })
// set, change or remove a PIN: the one it has, if any, is needed
ipcMain.handle('kataki:profile:pin', (_e, id: unknown, was: unknown, next: unknown) => {
  const changed = setPin(profiles, String(id), was, typeof next === 'string' ? next : null)
  if (changed) keep(changed)
  return !!changed
})
// Move the open library: the shell asks for the folder, and the move happens at the restart, with nothing open.
ipcMain.handle('kataki:profile:move', async (e) => {
  const win = BrowserWindow.fromWebContents(e.sender)!
  for (;;) {
    const folder = (await dialog.showOpenDialog(win, { title: 'Choose an empty folder for this library', buttonLabel: 'Move it here', properties: ['openDirectory', 'createDirectory'] })).filePaths[0]
    if (!folder) return false
    if (kind(folder) !== 'empty') { await dialog.showMessageBox(win, { type: 'info', message: 'That folder is not empty', detail: 'Choose an empty folder: the library is copied into it.' }); continue }
    const where = synced(folder)
    if (where) {
      const { response } = await dialog.showMessageBox(win, { type: 'warning', message: `That folder is in ${where}`, detail: 'A folder that syncs or sits on a network can damage a library while Kataki has it open. A folder on this computer is safer.', buttons: ['Choose another folder', 'Use it anyway'], cancelId: 0, noLink: true })
      if (response === 0) continue
    }
    keep({ ...profiles, move: { id: current(profiles).id, to: folder } })
    // the copy is made at the next start, so the engine must have let go of the library first
    quitting = true
    if (engine && engine.exitCode === null) {
      engine.stdin?.end()
      await Promise.race([once(engine, 'exit'), sleep(10_000)])
    }
    app.relaunch()
    app.exit(0)
    return true
  }
})
// After a move the old folder is still there. Keep it, or (asked once more, natively) delete it.
ipcMain.handle('kataki:profile:moved', async (e, what: unknown) => {
  const me = current(profiles)
  const old = me.movedFrom
  if (!old) return listing()
  if (what === 'delete') {
    const { response } = await dialog.showMessageBox(BrowserWindow.fromWebContents(e.sender)!, { type: 'warning', message: 'Delete the old copy?', detail: `${old}\n\nThe library now lives in:\n${me.folder}`, buttons: ['Keep it', 'Delete the old copy'], cancelId: 0, defaultId: 0, noLink: true })
    if (response !== 1) return listing()
    if (kind(old) === 'library' && resolve(old) !== resolve(me.folder)) rmSync(old, { recursive: true, force: true }) // only ever a folder that holds a library, never the one in use
  }
  keep({ ...profiles, profiles: profiles.profiles.map((p) => { if (p.id !== me.id) return p; const { movedFrom: _gone, ...rest } = p; return rest }) })
  return listing()
})
ipcMain.on('kataki:profile:switch', (_e, id: unknown) => {
  if (!profiles.profiles.some((p) => p.id === id)) return
  keep({ ...profiles, last: String(id) })
  app.relaunch()
  app.quit()
})

// No top-level await here: Electron holds `ready` until this module finishes evaluating,
// so `await app.whenReady()` at module scope deadlocks.
app
  .whenReady()
  .then(async () => {
    const crashed = !smoke && existsSync(runningMark())
    writeFileSync(runningMark(), new Date().toISOString())
    const token = randomBytes(32).toString('base64url')
    const db = single ? (process.env.KATAKI_DB ? resolve(repoRoot, process.env.KATAKI_DB) : join(home, 'library.db')) : join(await libraryFolder(), 'library.db')
    const win = await createWindow(await startEngine(token, db), token, crashed)
    starting = false
    if (smoke) await runSmoke(win)
  })
  .catch((err: Error) => fail(err.message))
