import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      // Proxy search requests to the backend server
      "/app/search": {
        target: "http://127.0.0.1:2024", // Updated to match your backend port
        changeOrigin: true,
        // Optionally rewrite path if needed (e.g., remove /app prefix if backend doesn't expect it)
        // rewrite: (path) => path.replace(/^\/app/, ''),
      },
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  plugins: [
    react(),
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
