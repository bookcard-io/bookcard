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
  getAllLanguageCodes,
  getLanguageName,
  POPULAR_LANGUAGES,
} from "./languages";

describe("languages", () => {
  describe("getLanguageName", () => {
    it("should return language name for valid code", () => {
      const name = getLanguageName("en");
      expect(name).toBeDefined();
      expect(typeof name).toBe("string");
    });

    it("should return undefined for invalid code", () => {
      const name = getLanguageName("invalid-code");
      expect(name).toBeUndefined();
    });

    it("should return undefined for empty string", () => {
      const name = getLanguageName("");
      expect(name).toBeUndefined();
    });

    it("should find language name from POPULAR_LANGUAGES", () => {
      if (POPULAR_LANGUAGES.length > 0) {
        const language = POPULAR_LANGUAGES[0];
        if (language) {
          const code = language.code;
          const expectedName = language.name;
          const name = getLanguageName(code);
          expect(name).toBe(expectedName);
        }
      }
    });
  });

  describe("getAllLanguageCodes", () => {
    it("should return array of language codes", () => {
      const codes = getAllLanguageCodes();
      expect(Array.isArray(codes)).toBe(true);
      expect(codes.length).toBeGreaterThan(0);
    });

    it("should return unique base codes from POPULAR_LANGUAGES", () => {
      const codes = getAllLanguageCodes();
      // getAllLanguageCodes returns deduplicated base codes (part before dash)
      // So the length should be less than or equal to POPULAR_LANGUAGES.length
      expect(codes.length).toBeLessThanOrEqual(POPULAR_LANGUAGES.length);
      // Verify all codes are unique
      expect(codes.length).toBe(new Set(codes).size);
    });

    it("should return ISO base codes only (part before dash)", () => {
      const codes = getAllLanguageCodes();
      // Verify each code is a base code (no dashes) and exists in POPULAR_LANGUAGES
      codes.forEach((code) => {
        expect(code).not.toContain("-");
        // Find at least one language entry that has this base code
        const hasMatchingLanguage = POPULAR_LANGUAGES.some(
          (lang) => lang.code.split("-")[0] === code,
        );
        expect(hasMatchingLanguage).toBe(true);
      });
    });
  });
});
