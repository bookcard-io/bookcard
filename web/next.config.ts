import fs from "node:fs";
import path from "node:path";
import withBundleAnalyzer from "@next/bundle-analyzer";
import { withSentryConfig } from "@sentry/nextjs";
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

// Define the base Next.js configuration
const baseConfig: NextConfig = {
  devIndicators: {
    position: "bottom-right",
  },
  poweredByHeader: false,
  reactStrictMode: true,
  reactCompiler: true,
  outputFileTracingIncludes: {
    "/": ["./migrations/**/*"],
  },
  experimental: {
    turbopackFileSystemCacheForDev: true,
  },
};

// Initialize the Next-Intl plugin
const i18nConfigPath = path.resolve(__dirname, "src/libs/I18n.ts");
let configWithPlugins = fs.existsSync(i18nConfigPath)
  ? createNextIntlPlugin("./src/libs/I18n.ts")(baseConfig)
  : baseConfig;

// Conditionally enable bundle analysis
if (process.env.ANALYZE === "true") {
  configWithPlugins = withBundleAnalyzer()(configWithPlugins);
}

// Conditionally enable Sentry configuration
if (!process.env.NEXT_PUBLIC_SENTRY_DISABLED) {
  configWithPlugins = withSentryConfig(configWithPlugins, {
    // For all available options, see:
    // https://www.npmjs.com/package/@sentry/webpack-plugin#options
    org: process.env.SENTRY_ORGANIZATION,
    project: process.env.SENTRY_PROJECT,

    // Only print logs for uploading source maps in CI
    silent: !process.env.CI,

    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    reactComponentAnnotation: {
      enabled: true,
    },

    // Route browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers.
    // This can increase your server load as well as your hosting bill.
    // Note: Check that the configured route will not match with your Next.js middleware, otherwise reporting of client-
    // side errors will fail.
    tunnelRoute: "/monitoring",

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    disableLogger: true,

    // Disable Sentry telemetry
    telemetry: false,
  });
}

const nextConfig = configWithPlugins;
export default nextConfig;
