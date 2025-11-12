// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

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

// Ensure JSON is available in browser test environment
if (typeof globalThis.JSON === "undefined") {
  if (typeof window !== "undefined" && window.JSON) {
    vi.stubGlobal("JSON", window.JSON);
  } else {
    // Fallback: provide a minimal JSON implementation if neither is available
    // This should not happen in normal browser environments
    vi.stubGlobal("JSON", {
      stringify: (_value: unknown) => {
        // This is a minimal implementation - in practice, browsers always have JSON
        throw new Error(
          "JSON.stringify not available - this should not happen",
        );
      },
      parse: (_text: string) => {
        throw new Error("JSON.parse not available - this should not happen");
      },
    });
  }
}

// ensure cleanup runs after each test in Vitest (browser and node)
afterEach(() => cleanup());
