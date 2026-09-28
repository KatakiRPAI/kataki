/// <reference types="vite/client" />

// Exposed by electron/preload.cts
interface Window {
  kataki?: { baseUrl: string; token: string; crashed?: boolean; restart?: () => void; startup?: (on: boolean) => void; reveal?: (what: 'library' | 'pictures' | 'backups') => void
    edit?: (what: 'cut' | 'copy' | 'paste' | 'selectAll' | 'replace' | 'learn', word?: string) => void
    onTextMenu?: (f: (m: { x: number; y: number; editable: boolean; selection: boolean; word: string; suggestions: string[] }) => void) => void }
}
