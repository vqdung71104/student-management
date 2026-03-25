import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
  proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // Dùng IP cứng để tránh trễ DNS
        changeOrigin: true,
        secure: false,
        timeout: 60000,      // Cho phép chờ tối đa 60 giây
        proxyTimeout: 60000, // Thời gian chờ phản hồi từ Backend
      }
    }
  }
})
