import { spawn, type ChildProcess } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { once } from 'node:events'
import { dirname, join, resolve } from 'node:path'
import { createInterface } from 'node:readline'
import { setTimeout as sleep } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'
import { app, BrowserWindow, dialog } from 'electron'

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

async function startEngine(token: string): Promise<number> {
  // ponytail: dev layout only (the repo venv). M5 packaging swaps in the bundled runtime path.
  const python = join(repoRoot, 'engine', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
  const home = join(repoRoot, '.dev') // the dev library and downloaded models stay in the repo
  // KATAKI_DB swaps the library, e.g. .dev/demo.db (a relative path is from the repo root)
  const db = process.env.KATAKI_DB ? resolve(repoRoot, process.env.KATAKI_DB) : join(home, 'library.db')
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

async function createWindow(port: number, token: string): Promise<BrowserWindow> {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    show: !smoke,
    webPreferences: {
      preload: join(here, 'preload.cjs'),
      additionalArguments: [`--kataki-port=${port}`, `--kataki-token=${token}`],
    },
  })
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

// No top-level await here: Electron holds `ready` until this module finishes evaluating,
// so `await app.whenReady()` at module scope deadlocks.
app
  .whenReady()
  .then(async () => {
    const token = randomBytes(32).toString('base64url')
    const win = await createWindow(await startEngine(token), token)
    if (smoke) await runSmoke(win)
  })
  .catch((err: Error) => fail(err.message))
