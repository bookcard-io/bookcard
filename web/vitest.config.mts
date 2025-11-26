import react from "@vitejs/plugin-react";
import { playwright } from "@vitest/browser-playwright";
import { loadEnv } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  resolve: {
    dedupe: ["react", "react-dom"],
    alias: {
      "next/navigation": new URL(
        "./src/__mocks__/next-navigation.ts",
        import.meta.url,
      ).pathname,
    },
  },
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-dom/client",
      "react/jsx-runtime",
      "next/dynamic",
      "@testing-library/react",
      "@testing-library/user-event",
      "@vitest/browser",
      "@vitest/browser-playwright",
    ],
    exclude: [
      // native/binary or Node-only deps that break optimize step in browser runner
      "lightningcss",
      "lightningcss/node",
      "playwright",
      "@playwright/test",
      "playwright-core",
      "chromium-bidi",
      "chromium-bidi/lib/cjs/bidiMapper/BidiMapper",
      "chromium-bidi/lib/cjs/cdp/CdpConnection",
    ],
  },
  test: {
    coverage: {
      include: ["src/**/*"],
      exclude: [
        "src/**/*.stories.{js,jsx,ts,tsx}",
        "src/**/*.{scss,sass,css}",
        "src/components/icons/**/*.{ts,tsx}",
        // SVG icon components (no logic to test)
        "src/icons/**/*.{ts,tsx}",
        // Next.js App Router pages and API routes (integration-tested, not unit-tested)
        "src/app/**/*",
        // React components (typically integration/E2E tested)
        "src/components/**/*",
        // React contexts (typically integration-tested with components)
        "src/contexts/**/*",
        // Type definitions (compile-time only, no runtime code)
        "src/types/**/*",
        // Next.js infrastructure files
        "src/instrumentation*.ts",
        "src/proxy.ts",
        "src/constants/inspiring_quotes.ts",
      ],
      reporter: ["text", "text-summary", "html", "json"],
      reportsDirectory: "./coverage",
    },
    projects: [
      {
        extends: true,
        test: {
          name: "unit",
          include: ["src/**/*.test.{js,ts}"],
          exclude: ["src/hooks/**/*.test.ts"],
          environment: "node",
        },
      },
      {
        extends: true,
        test: {
          name: "ui",
          include: ["**/*.test.tsx", "src/hooks/**/*.test.ts"],
          setupFiles: ["./src/setupTests.ts"],
          browser: {
            enabled: true,
            headless: true,
            provider: playwright(),
            screenshotDirectory: "vitest-test-results",
            instances: [{ browser: "chromium" }],
          },
        },
      },
    ],
    env: loadEnv("", process.cwd(), ""),
  },
});
