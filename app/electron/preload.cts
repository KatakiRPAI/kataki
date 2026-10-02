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
  openOnline: (url: string) => ipcRenderer.send('kataki:open-online', url),
  edit: (what: string, word?: string) => ipcRenderer.send('kataki:edit', what, word),
  onTextMenu: (f: (m: unknown) => void) => ipcRenderer.on('kataki:textmenu', (_e, m) => f(m)),
  // Settings › Profiles: only when the shell keeps a list (not the smoke test, not KATAKI_DB)
  ...(process.argv.includes('--kataki-profiles') && {
    profiles: () => ipcRenderer.invoke('kataki:profiles'),
    profileAdd: (name: string) => ipcRenderer.invoke('kataki:profile:add', name),
    profileRename: (id: string, name: string) => ipcRenderer.invoke('kataki:profile:rename', id, name),
    profileForget: (id: string) => ipcRenderer.invoke('kataki:profile:forget', id),
    profileSwitch: (id: string) => ipcRenderer.send('kataki:profile:switch', id),
    profileAsk: (on: boolean) => ipcRenderer.invoke('kataki:profile:ask', on),
    profilePin: (id: string, was: string | undefined, next: string | null) => ipcRenderer.invoke('kataki:profile:pin', id, was, next),
    profileMove: () => ipcRenderer.invoke('kataki:profile:move'),
    profileMoved: (what: 'keep' | 'delete') => ipcRenderer.invoke('kataki:profile:moved', what),
  }),
})
