import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  base: './', // the packaged app loads dist/index.html from file://
  plugins: [react()],
})
