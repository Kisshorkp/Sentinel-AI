import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // 8000 is occupied by a stale Windows ghost listener on this machine
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
        // Analyzer + Google Ads pipeline often takes 45–90s
        timeout: 300_000,
        proxyTimeout: 300_000,
      },
    },
  },
})
