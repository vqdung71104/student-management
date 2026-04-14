import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Use VITE_DEV_BACKEND to make the dev proxy target configurable.
const devBackend = process.env.VITE_DEV_BACKEND || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: devBackend,
        changeOrigin: true,
        secure: false,
        timeout: 60000,      // Cho phép chờ tối đa 60 giây
        proxyTimeout: 60000, // Thời gian chờ phản hồi từ Backend
      }
    }
  }
})
