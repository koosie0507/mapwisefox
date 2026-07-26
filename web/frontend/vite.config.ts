import {defineConfig} from "vitest/config";
import react from "@vitejs/plugin-react";
import {readFileSync} from "node:fs";

function frontendVersion(): string {
    const packageJson: unknown = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8"));
    if (typeof packageJson !== "object" || packageJson === null || !("version" in packageJson) || typeof packageJson.version !== "string") {
        throw new Error("package.json must define a version.");
    }
    return packageJson.version;
}

export default defineConfig({
    plugins: [react()],
    define: {
        __FRONTEND_VERSION__: JSON.stringify(frontendVersion()),
    },
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
        reporters: process.env.GITHUB_ACTIONS === 'true'
            ? ['default', 'github-actions', 'junit']
            : ['default', 'junit'],
        coverage: {
            provider: "v8",
            reporter: ['text', 'json-summary', 'json'],
            reportOnFailure: true,
            include: ["src/**/*.{ts,tsx}"],
            exclude: ["src/main.ts", "src/vite-env.d.ts"],
            thresholds: {
                lines: 90,
                branches: 80,
            },
        },
    },
});
