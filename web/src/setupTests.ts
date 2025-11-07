import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Provide process.env for browser tests (Next.js requires it)
// This must be done before any Next.js modules are imported
if (typeof globalThis.process === "undefined") {
  Object.defineProperty(globalThis, "process", {
    value: {
      env: {},
    },
    writable: true,
    configurable: true,
  });
}

// ensure cleanup runs after each test in Vitest (browser and node)
afterEach(() => cleanup());
