import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig(({command})=>({
  define:command==='build'?{'process.env.NODE_ENV':'"production"'}:{},
  base: './', plugins:[react()],
  build: {outDir:'dist',emptyOutDir:true,sourcemap:false,
    lib:{entry:'src/main.tsx',name:'ResearchCompanion',formats:['iife'],fileName:()=> 'app.js'},
    rollupOptions:{output:{assetFileNames:'assets/[name][extname]'}}},
  test:{environment:'jsdom',globals:true},
}));
