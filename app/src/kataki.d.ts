/// <reference types="vite/client" />

// Exposed by electron/preload.cts
interface Window {
  kataki?: { baseUrl: string; token: string; crashed?: boolean; restart?: () => void; startup?: (on: boolean) => void; reveal?: (what: 'library' | 'pictures' | 'backups') => void
    edit?: (what: 'cut' | 'copy' | 'paste' | 'selectAll' | 'replace' | 'learn', word?: string) => void
    onTextMenu?: (f: (m: { x: number; y: number; editable: boolean; selection: boolean; word: string; suggestions: string[] }) => void) => void
    // desktop profiles (electron/profiles.ts): absent on the web and when the shell opens one fixed library
    profiles?: () => Promise<{ current: string; list: DesktopProfile[] }>
    profileAdd?: (name: string) => Promise<DesktopProfile | null>
    profileRename?: (id: string, name: string) => Promise<DesktopProfile[]>
    profileForget?: (id: string) => Promise<DesktopProfile[]>
    profileSwitch?: (id: string) => void }
}
type DesktopProfile = { id: string; name: string; folder: string }
