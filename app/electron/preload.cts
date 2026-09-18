import { contextBridge } from 'electron'

function arg(name: string): string {
  const prefix = `--kataki-${name}=`
  const found = process.argv.find((a) => a.startsWith(prefix))
  if (!found) throw new Error(`missing ${prefix}`)
  return found.slice(prefix.length)
}

contextBridge.exposeInMainWorld('kataki', {
  baseUrl: `http://127.0.0.1:${arg('port')}`,
  token: arg('token'),
})
