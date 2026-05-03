import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  appType: 'custom',
  plugins: [react()],
  css: {
      modules: {
          localsConvention: "camelCase"
      }
  },
  build: {
    outDir: resolve(__dirname, "../assets/dist"),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: resolve(__dirname, 'src/main.ts'),
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    // Be explicit about CORS
    cors: {
      origin: [
          "http://localhost:8000",
          "http://127.0.0.1:8000",
          "http://0.0.0.0:8000"
      ],
      credentials: false,
    },
    // Extra safety: add ACAO on all dev responses
    headers: {
      "Access-Control-Allow-Origin": "*",
    },
  },
})
