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
        const [code, expectedName] = POPULAR_LANGUAGES[0];
        const name = getLanguageName(code);
        expect(name).toBe(expectedName);
      }
    });
  });

  describe("getAllLanguageCodes", () => {
    it("should return array of language codes", () => {
      const codes = getAllLanguageCodes();
      expect(Array.isArray(codes)).toBe(true);
      expect(codes.length).toBeGreaterThan(0);
    });

    it("should return all codes from POPULAR_LANGUAGES", () => {
      const codes = getAllLanguageCodes();
      expect(codes.length).toBe(POPULAR_LANGUAGES.length);
    });

    it("should return ISO codes only (first element of each tuple)", () => {
      const codes = getAllLanguageCodes();
      codes.forEach((code, index) => {
        expect(code).toBe(POPULAR_LANGUAGES[index][0]);
      });
    });
  });
});
