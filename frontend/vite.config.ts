import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import path from 'path'

export default defineConfig({
  base: '/',
  plugins: [
    vue(),
    Components({
      dirs: ['src/components/ui', 'src/components', 'src/components/contracts'],
      extensions: ['vue'],
      deep: true,
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    assetsInlineLimit: 0,
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        manualChunks: undefined,
        assetFileNames: 'assets/[name][extname]',
        chunkFileNames: 'assets/[name].js',
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
