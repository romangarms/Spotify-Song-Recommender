import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Output to dist directory (default)
    outDir: 'dist',
    // Generate sourcemaps for debugging
    sourcemap: true,
  },
})
