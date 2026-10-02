import { spawn, type ChildProcess } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { once } from 'node:events'
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { createInterface } from 'node:readline'
import { setTimeout as sleep } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'
import { app, BrowserWindow, dialog, ipcMain, screen, shell } from 'electron'
import { add, cleanName, current, forget, kind, load, rename, save, synced, type Profile, type Profiles } from './profiles.js'

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

/** The folder to open: the last profile's, once it is there. A library is never made at a path that went missing. */
function libraryFolder(): string {
  if (!existsSync(profilesFile())) mkdirSync(home, { recursive: true }) // the first run: the one folder made unasked
  profiles = load(profilesFile(), profiles.profiles[0])
  for (;;) {
    const me = current(profiles)
    if (kind(me.folder) !== 'missing') return me.folder
    choose(`Kataki can’t find ${me.name}`, `Its folder is not there:\n${me.folder}\n\nIf it is on a drive that isn’t plugged in, plug it in and try again.`, { retry: true, locate: true })
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
app.on('window-all-closed', () => app.quit())

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
ipcMain.handle('kataki:profiles', () => ({ current: current(profiles).id, list: profiles.profiles }))
ipcMain.handle('kataki:profile:add', (e, name: unknown) => addProfile(BrowserWindow.fromWebContents(e.sender)!, name))
ipcMain.handle('kataki:profile:rename', (_e, id: unknown, name: unknown) => keep(rename(profiles, String(id), cleanName(name))).profiles)
ipcMain.handle('kataki:profile:forget', (_e, id: unknown) => keep(forget(profiles, String(id))).profiles)
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
    const db = single ? (process.env.KATAKI_DB ? resolve(repoRoot, process.env.KATAKI_DB) : join(home, 'library.db')) : join(libraryFolder(), 'library.db')
    const win = await createWindow(await startEngine(token, db), token, crashed)
    if (smoke) await runSmoke(win)
  })
  .catch((err: Error) => fail(err.message))
