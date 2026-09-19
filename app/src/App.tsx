import { useEffect } from 'react'
import { api } from './api'
import Classic from './classic/Classic'
import { useRoute } from './hooks'
import Kit from './Kit'

export default function App() {
  const route = useRoute()

  // The smoke check (and later the offline card) read this instead of visible text.
  useEffect(() => {
    const mark = (state: string) => (document.documentElement.dataset.engine = state)
    api('/health').then(() => mark('ok'), () => mark('down'))
  }, [])

  if (route.path === '/dev/kit') return <Kit />
  return (
    <div className="classic">
      <Classic />
    </div>
  )
}
