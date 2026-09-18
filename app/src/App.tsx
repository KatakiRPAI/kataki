import { useEffect, useState } from 'react'

export default function App() {
  const [status, setStatus] = useState('connecting to engine…')

  useEffect(() => {
    const { baseUrl, token } = window.kataki
    fetch(`${baseUrl}/health`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((h) => setStatus(`engine ok · v${h.version} · schema ${h.schema}`))
      .catch((e: Error) => setStatus(`engine unreachable: ${e.message}`))
  }, [])

  return (
    <main>
      <h1>Kataki RPAI</h1>
      <p role="status">{status}</p>
    </main>
  )
}
