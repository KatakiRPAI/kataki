import { spawn, type ChildProcess } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { once } from 'node:events'
import { existsSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { createInterface } from 'node:readline'
import { setTimeout as sleep } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'
import { app, BrowserWindow, dialog, ipcMain, screen, shell } from 'electron'

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

let libraryDb = ''
async function startEngine(token: string): Promise<number> {
  // ponytail: dev layout only (the repo venv). M5 packaging swaps in the bundled runtime path.
  const python = join(repoRoot, 'engine', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
  const home = join(repoRoot, '.dev') // the dev library and downloaded models stay in the repo
  // KATAKI_DB swaps the library, e.g. .dev/demo.db (a relative path is from the repo root)
  const db = process.env.KATAKI_DB ? resolve(repoRoot, process.env.KATAKI_DB) : join(home, 'library.db')
  libraryDb = db
  const args = ['-m', 'kataki', 'serve', '--parent-watch', '--db', db]
  // The engine watches its stdin: when this process ends for any reason, the pipe closes and it exits.
  const env = { ...process.env, KATAKI_TOKEN: token, KATAKI_HOME: home }
  engine = spawn(python, args, { env, stdio: ['pipe', 'pipe', 'inherit'] })
  engine.on('error', (err) => fail(`could not start ${python}: ${err.message}`))
  engine.on('exit', (code) => fail(`engine exited with code ${code}`))
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
      additionalArguments: [`--kataki-port=${port}`, `--kataki-token=${token}`, ...(crashed ? ['--kataki-crashed'] : [])],
    },
  })
  win.on('close', () => { try { writeFileSync(boundsFile(), JSON.stringify(win.getBounds())) } catch { /* next time, the default */ } })
  // Model output is untrusted text that can contain links: never open windows or leave the app.
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))
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
ipcMain.on('kataki:restart', () => { app.relaunch(); app.quit() })
// Settings › General › Start with Windows: only when the person turns it on or off there.
ipcMain.on('kataki:startup', (_e, on: boolean) => app.setLoginItemSettings({ openAtLogin: !!on }))
// Settings › Data › Open folder: only the library's own folders, never a path the page names
ipcMain.on('kataki:reveal', (_e, what: string) => {
  const folders: Record<string, string> = { library: '', pictures: 'blobs', backups: 'backups' }
  if (Object.hasOwn(folders, what)) shell.openPath(join(dirname(libraryDb), folders[what]))
})

// No top-level await here: Electron holds `ready` until this module finishes evaluating,
// so `await app.whenReady()` at module scope deadlocks.
app
  .whenReady()
  .then(async () => {
    const crashed = !smoke && existsSync(runningMark())
    writeFileSync(runningMark(), new Date().toISOString())
    const token = randomBytes(32).toString('base64url')
    const win = await createWindow(await startEngine(token), token, crashed)
    if (smoke) await runSmoke(win)
  })
  .catch((err: Error) => fail(err.message))
