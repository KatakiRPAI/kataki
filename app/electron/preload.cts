import { contextBridge, ipcRenderer } from 'electron'

function arg(name: string): string {
  const prefix = `--kataki-${name}=`
  const found = process.argv.find((a) => a.startsWith(prefix))
  if (!found) throw new Error(`missing ${prefix}`)
  return found.slice(prefix.length)
}

contextBridge.exposeInMainWorld('kataki', {
  baseUrl: `http://127.0.0.1:${arg('port')}`,
  token: arg('token'),
  crashed: process.argv.includes('--kataki-crashed'), // the last run ended without a clean quit (A3)
  restart: () => ipcRenderer.send('kataki:restart'),
  startup: (on: boolean) => ipcRenderer.send('kataki:startup', on),
  reveal: (what: string) => ipcRenderer.send('kataki:reveal', what),
})
