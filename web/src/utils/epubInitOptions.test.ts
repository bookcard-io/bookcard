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

import { describe, expect, it } from "vitest";
import { createEpubInitOptions } from "./epubInitOptions";

describe("epubInitOptions", () => {
  describe("createEpubInitOptions", () => {
    it("should return options with openAs binary", () => {
      const options = createEpubInitOptions();
      expect(options.openAs).toBe("binary");
    });

    it("should return requestMethod function", () => {
      const options = createEpubInitOptions();
      expect(typeof options.requestMethod).toBe("function");
    });

    describe("requestMethod", () => {
      const getRequestMethod = () => {
        const options = createEpubInitOptions();
        if (!options.requestMethod) {
          throw new Error("requestMethod is not defined");
        }
        return options.requestMethod;
      };

      it.each([
        { url: "http://example.com/resource", description: "HTTP URL" },
        { url: "https://example.com/resource", description: "HTTPS URL" },
        { url: "/absolute/path/resource", description: "absolute path" },
      ])("should reject $description with archive error", async ({ url }) => {
        const requestMethod = getRequestMethod();
        await expect(requestMethod(url, "type", {}, {})).rejects.toThrow(
          "Resource should be loaded from EPUB archive",
        );
      });

      it("should reject non-http URLs with archive error", async () => {
        const requestMethod = getRequestMethod();
        await expect(
          requestMethod("epub://internal/resource", "type", {}, {}),
        ).rejects.toThrow("All EPUB resources must come from the archive");
      });

      it("should reject non-string URLs with archive error", async () => {
        const requestMethod = getRequestMethod();
        await expect(
          requestMethod(123 as unknown as string, "type", {}, {}),
        ).rejects.toThrow("All EPUB resources must come from the archive");
      });
    });
  });
});
