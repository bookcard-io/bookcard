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
  extensionFromMimeType,
  isImageMimeType,
  isValidImageExtension,
  normalizeMimeType,
} from "./mimeTypes";

describe("mimeTypes utils", () => {
  describe("normalizeMimeType", () => {
    it.each([
      { input: "image/jpeg", expected: "image/jpeg" },
      { input: "image/jpeg; charset=utf-8", expected: "image/jpeg" },
      { input: " Image/PNG ; q=0.9", expected: "image/png" },
      { input: "text/html; charset=utf-8", expected: "text/html" },
    ])("should normalize '$input' -> '$expected'", ({ input, expected }) => {
      expect(normalizeMimeType(input)).toBe(expected);
    });
  });

  describe("extensionFromMimeType", () => {
    it.each([
      { mimeType: "image/jpeg", expected: "jpg" },
      { mimeType: "image/jpg", expected: "jpg" },
      { mimeType: "image/png", expected: "png" },
      { mimeType: "image/avif", expected: "avif" },
      { mimeType: "image/unknown", expected: null },
    ])("should return $expected for mime '$mimeType'", ({
      mimeType,
      expected,
    }) => {
      expect(extensionFromMimeType(mimeType)).toBe(expected);
    });
  });

  describe("isImageMimeType", () => {
    it.each([
      { mimeType: "image/jpeg", expected: true },
      { mimeType: "image/svg+xml", expected: true },
      { mimeType: "text/html", expected: false },
      { mimeType: "application/json", expected: false },
    ])("should return $expected for mime '$mimeType'", ({
      mimeType,
      expected,
    }) => {
      expect(isImageMimeType(mimeType)).toBe(expected);
    });
  });

  describe("isValidImageExtension", () => {
    it.each([
      { ext: "jpg", expected: true },
      { ext: "JPG", expected: true },
      { ext: "jpeg", expected: true },
      { ext: "png", expected: true },
      { ext: "svg", expected: true },
      { ext: "webp", expected: true },
      { ext: "exe", expected: false },
      { ext: "html", expected: false },
      { ext: "", expected: false },
    ])("should return $expected for ext '$ext'", ({ ext, expected }) => {
      expect(isValidImageExtension(ext)).toBe(expected);
    });
  });
});
