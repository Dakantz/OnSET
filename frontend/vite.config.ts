import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import prism from 'vite-plugin-prismjs';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    prism({
      languages: ['sparql'],
      // plugins: ['line-numbers'],
      // theme: 'tomorrow',
      css: true,
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      "plotly.js-basic-dist": fileURLToPath(new URL("node_modules/plotly.js-dist/plotly.js", import.meta.url))

    }
  },
  // base: "/demo",
  envPrefix: 'ONSET_',
  server:{
    port: 5174,
  }
})
