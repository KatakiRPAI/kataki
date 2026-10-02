// The profile picker's bridge (picker.html): which profiles there are, and choosing one.
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('picker', {
  list: () => ipcRenderer.invoke('kataki:picker:list'),
  choose: (id: string, pin?: string) => ipcRenderer.invoke('kataki:picker:choose', id, pin),
})
