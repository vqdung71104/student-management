import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Use VITE_DEV_BACKEND to make the dev proxy target configurable.
const devBackend =
  process.env.VITE_DEV_BACKEND ||
  'http://student-management-backend:8000'

export default defineConfig({
  plugins: [react()],

  server: {
    host: '0.0.0.0',

    allowedHosts: [
      'learnbuild.dev',
      'www.learnbuild.dev',
    ],

    proxy: {
      '/api': {
        target: devBackend,
        changeOrigin: true,
        secure: false,

        timeout: 60000,
        proxyTimeout: 60000,
      },
    },
  },
})