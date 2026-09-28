// Builds runtime.ts into the boards' support.js: `vite build -c checks/boards/vite.config.ts`
import { resolve } from 'node:path'
import { defineConfig } from 'vite'

export default defineConfig({
  define: { 'process.env.NODE_ENV': '"development"' },
  build: {
    outDir: resolve(import.meta.dirname, 'dist'),
    emptyOutDir: true,
    minify: false,
    lib: { entry: resolve(import.meta.dirname, 'runtime.ts'), formats: ['iife'], name: 'DCRuntime', fileName: () => 'support.js' },
  },
})
