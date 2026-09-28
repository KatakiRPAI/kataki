// Side-by-side check (handoff README › Definition of done): renders each board and the app screen
// it stands for at the same size, and writes board | app | difference as one picture.
//   node node_modules/electron/cli.js checks/boards/shoot.cjs <jobs.json> <outDir>
//   env: SHOOT_APP (default http://localhost:5174), SHOOT_PORT (engine, 8765), SHOOT_TOKEN (dev) — Electron
//   won't start with a URL among its arguments
// jobs.json: [{ "id": "C1-night", "board": "Home", "props": { "theme": "night" }, "app": "/home",
//              "theme": "night", "h": 1360, "js": "optional code run in the app before the shot" }]
// Needs the dev app (vite) and an engine with the sample library; boards come from the handoff.
const { app, BrowserWindow, nativeImage } = require('electron')
const http = require('node:http')
const fs = require('node:fs')
const path = require('node:path')

const [jobsFile, outDir] = process.argv.slice(2).filter((a) => !a.startsWith('--') && !a.endsWith('shoot.cjs') && a !== '.')
const { SHOOT_APP: appOrigin = 'http://localhost:5174', SHOOT_PORT: enginePort = '8765', SHOOT_TOKEN: token = 'dev' } = process.env
const root = path.resolve(__dirname, '../../..')
const BOARDS = path.join(root, 'docs/handoff/kataki-handoff/boards')
const ART = path.join(root, 'app/src/ds/art')
const BLOBS = { e49764b15e9de5d49d4bc2bbf8c90f65: 'liv.png', '0b9fe4d5e949fe7395d2dc331675abe8': 'mike.png', '24f537101f1220b0706482e827c12368': 'theo.png', '98b8803c4f86e4c451df752de430a773': 'jae.png', '88294483e380df3b0fb980ee2c0b5d07': 'nico.png', '6ee3bde163b8abc870ce59996374605d': 'cas.png', '1e023859469874b847f3f6c9eb3831a9': 'halcyon-coffee.png', f9ee926a93a1e0c21681768006f8293a: 'corvel-palace.png', '27e72542c91efd72118b0f88c6bac4a7': 'flat-on-ardenne.png', e207af2b3e316bdbc66fc7d1e4f92cc4: 'clouds.svg' }
// Electron's stdout doesn't reach a Windows shell; everything also goes to <outDir>/log.txt
const log = (...a) => { console.log(...a); fs.appendFileSync(path.join(outDir, 'log.txt'), a.join(' ') + '\n') }
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.json': 'application/json' }

function serve() {
  return new Promise((ok) => {
    const s = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split('?')[0])
      let file = url === '/support.js' ? path.join(__dirname, 'dist/support.js')
        : url.startsWith('/_blob/') ? path.join(ART, BLOBS[url.slice(7)] || 'none')
        : path.join(BOARDS, url)
      if (!file.startsWith(BOARDS) && !file.startsWith(ART) && !file.startsWith(__dirname)) file = ''
      fs.readFile(file, (e, data) => {
        if (e) { res.writeHead(404); return res.end() }
        res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' })
        res.end(data)
      })
    })
    s.listen(0, '127.0.0.1', () => ok(s.address().port))
  })
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms))
async function shot(url, h, js, ready) {
  const w = new BrowserWindow({ show: false, width: 1440, height: h, useContentSize: true, enableLargerThanScreen: true, webPreferences: { offscreen: true } })
  w.webContents.setFrameRate(10)
  w.setContentSize(1440, h)
  await w.loadURL(url)
  for (let i = 0; i < 60 && !(await w.webContents.executeJavaScript(ready).catch(() => false)); i++) await wait(250)
  if (js) { await w.webContents.executeJavaScript(`(async () => { ${js} })()`).catch((e) => log('js failed', e.message)); await wait(700) }
  await wait(900)
  const img = await w.webContents.capturePage({ x: 0, y: 0, width: 1440, height: h })
  w.destroy()
  return img
}

async function theme(t) {
  await fetch(`http://127.0.0.1:${enginePort}/settings`, { method: 'PUT', headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' }, body: JSON.stringify({ 'appearance.theme': t }) })
}

// board | app | difference (red where they differ), each at half size, and the share that differs
async function compare(a, b, h, file) {
  const w = new BrowserWindow({ show: false, width: 2160, height: Math.ceil(h / 2) + 24, enableLargerThanScreen: true, webPreferences: { offscreen: true } })
  await w.loadURL('data:text/html,<body style="margin:0;background:%23222;font:14px sans-serif;color:%23fff"><canvas id=c></canvas></body>')
  const [pct, png] = await w.webContents.executeJavaScript(`(async () => {
    const load = (src) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = src })
    const [A, B] = await Promise.all([load(${JSON.stringify(a.toDataURL())}), load(${JSON.stringify(b.toDataURL())})])
    const W = 1440, H = ${h}, c = document.getElementById('c'), x = c.getContext('2d')
    const px = (img) => { const k = new OffscreenCanvas(W, H).getContext('2d'); k.drawImage(img, 0, 0, W, H); return k.getImageData(0, 0, W, H) }
    const da = px(A), db = px(B), d = new ImageData(W, H); let n = 0
    for (let i = 0; i < da.data.length; i += 4) {
      const diff = Math.abs(da.data[i] - db.data[i]) + Math.abs(da.data[i + 1] - db.data[i + 1]) + Math.abs(da.data[i + 2] - db.data[i + 2])
      const g = (da.data[i] + da.data[i + 1] + da.data[i + 2]) / 9
      if (diff > 60) { n++; d.data.set([255, 40, 40, 255], i) } else d.data.set([g, g, g, 255], i)
    }
    const k = new OffscreenCanvas(W, H).getContext('2d'); k.putImageData(d, 0, 0)
    c.width = 2160; c.height = H / 2 + 24
    x.fillStyle = '#222'; x.fillRect(0, 0, c.width, c.height)
    x.drawImage(A, 0, 24, 720, H / 2); x.drawImage(B, 720, 24, 720, H / 2); x.drawImage(k.canvas, 1440, 24, 720, H / 2)
    x.fillStyle = '#fff'; x.font = '14px sans-serif'
    x.fillText('board', 8, 17); x.fillText('app', 728, 17); x.fillText('difference', 1448, 17)
    return [(100 * n / (W * H)).toFixed(1), c.toDataURL()]
  })()`)
  const img = nativeImage.createFromDataURL(png)
  w.destroy()
  fs.writeFileSync(file, img.toPNG())
  return pct
}

app.on('window-all-closed', () => {}) // each shot closes its window; the script quits when done
app.whenReady().then(async () => {
  process.on('unhandledRejection', (e) => { fs.mkdirSync(outDir, { recursive: true }); log('failed', e.stack); app.quit() })
  const port = await serve()
  const jobs = JSON.parse(fs.readFileSync(jobsFile, 'utf8'))
  fs.mkdirSync(outDir, { recursive: true })
  let current = null
  for (const j of jobs) {
    const h = j.h || 900
    const q = new URLSearchParams(Object.entries(j.props || {}).map(([k, v]) => [k, JSON.stringify(v)]))
    const board = await shot(`http://127.0.0.1:${port}/${j.board}.dc.html?${q}`, h, j.boardJs, `document.documentElement.dataset.board === 'ready'`)
    fs.writeFileSync(path.join(outDir, `${j.id}.board.png`), board.toPNG())
    if (!j.app) { log(j.id, 'board only'); continue }
    if (j.theme && j.theme !== current) { await theme(j.theme); current = j.theme }
    const sep = j.app.includes('?') ? '&' : '?'
    const shown = await shot(`${appOrigin}${j.app}${sep}port=${enginePort}&token=${token}`, h, j.js, `document.documentElement.dataset.engine === 'ok' && !!document.querySelector('main, .scene, [role=dialog]')`)
    fs.writeFileSync(path.join(outDir, `${j.id}.app.png`), shown.toPNG())
    log(j.id, await compare(board, shown, h, path.join(outDir, `${j.id}.png`)) + '% differs')
  }
  app.quit()
})
