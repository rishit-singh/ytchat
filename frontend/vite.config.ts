import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"
import mkcert from 'vite-plugin-mkcert'

export default defineConfig({
  plugins: [react(), mkcert()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
