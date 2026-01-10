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
import {
  getPreferredReadableFormat,
  getReadableFormatForReader,
} from "./bookFormats";

describe("bookFormats utils", () => {
  describe("getPreferredReadableFormat", () => {
    it("should return null when formats are empty", () => {
      expect(getPreferredReadableFormat([])).toBeNull();
    });

    it.each([
      [{ format: "cbz" }, "CBZ"],
      [{ format: "CBR" }, "CBR"],
      [{ format: "cb7" }, "CB7"],
      [{ format: "cbc" }, "CBC"],
    ])("should prefer native comic formats (%s -> %s)", (format, expected) => {
      expect(getPreferredReadableFormat([format])).toBe(expected);
    });

    it("should prefer EPUB when no comic formats are available", () => {
      expect(
        getPreferredReadableFormat([{ format: "pdf" }, { format: "epub" }]),
      ).toBe("EPUB");
    });

    it("should prefer PDF when no comic formats or EPUB are available", () => {
      expect(getPreferredReadableFormat([{ format: "pdf" }])).toBe("PDF");
    });

    it("should return null when no readable formats are available", () => {
      expect(getPreferredReadableFormat([{ format: "mobi" }])).toBeNull();
    });
  });

  describe("getReadableFormatForReader", () => {
    it("should return null when no formats are available", () => {
      expect(getReadableFormatForReader([], "EPUB")).toBeNull();
    });

    it("should honor a preferred comic format when available", () => {
      expect(
        getReadableFormatForReader(
          [{ format: "cbz" }, { format: "cbr" }, { format: "epub" }],
          "cbr",
        ),
      ).toBe("CBR");
    });

    it("should prefer comics even when a non-comic preferred format is provided", () => {
      expect(
        getReadableFormatForReader(
          [{ format: "pdf" }, { format: "cbr" }],
          "pdf",
        ),
      ).toBe("CBR");
    });

    it("should honor a preferred readable non-comic format when no comics are available", () => {
      expect(
        getReadableFormatForReader(
          [{ format: "epub" }, { format: "pdf" }],
          "pdf",
        ),
      ).toBe("PDF");
    });

    it("should fall back to best readable format when preferred format is not available", () => {
      expect(getReadableFormatForReader([{ format: "epub" }], "pdf")).toBe(
        "EPUB",
      );
    });

    it("should ignore unreadable preferred formats and fall back", () => {
      expect(getReadableFormatForReader([{ format: "epub" }], "mobi")).toBe(
        "EPUB",
      );
    });
  });
});
