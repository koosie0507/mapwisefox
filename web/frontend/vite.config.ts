import {defineConfig} from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    css: {
        modules: {
            localsConvention: "camelCase",
        },
    },
    build: {
        outDir: "dist",
        emptyOutDir: true,
    },
    server: {
        port: 5173,
        strictPort: true,
        proxy: {
            "/api": "http://localhost:8000",
            "/auth": "http://localhost:8000",
        },
    },
    test: {
        environment: "jsdom",
        setupFiles: ["./src/test/setup.ts"],
        coverage: {
            provider: "v8",
            include: ["src/**/*.{ts,tsx}"],
            exclude: ["src/main.ts", "src/vite-env.d.ts"],
            thresholds: {
                lines: 90,
            },
        },
    },
});
