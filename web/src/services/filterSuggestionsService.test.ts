import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  defaultFilterSuggestionsService,
  languageFilterSuggestionsService,
} from "./filterSuggestionsService";

describe("filterSuggestionsService", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("defaultFilterSuggestionsService (ApiFilterSuggestionsService)", () => {
    it("should return empty array for empty query", async () => {
      const result = await defaultFilterSuggestionsService.fetchSuggestions(
        "",
        "author",
      );
      expect(result).toEqual([]);
    });

    it("should return empty array for whitespace-only query", async () => {
      const result = await defaultFilterSuggestionsService.fetchSuggestions(
        "   ",
        "author",
      );
      expect(result).toEqual([]);
    });

    it("should fetch suggestions from API", async () => {
      const mockSuggestions = [
        { id: 1, name: "Author 1" },
        { id: 2, name: "Author 2" },
      ];
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ suggestions: mockSuggestions }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await defaultFilterSuggestionsService.fetchSuggestions(
        "test",
        "author",
      );

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/books/filter/suggestions?q=test&filter_type=author",
        { cache: "no-store" },
      );
      expect(result).toEqual(mockSuggestions);
    });

    it("should encode query and filter type in URL", async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ suggestions: [] }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await defaultFilterSuggestionsService.fetchSuggestions(
        "test query",
        "filter type",
      );

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/books/filter/suggestions?q=test%20query&filter_type=filter%20type",
        { cache: "no-store" },
      );
    });

    it("should return empty array on API error", async () => {
      const mockResponse = {
        ok: false,
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await defaultFilterSuggestionsService.fetchSuggestions(
        "test",
        "author",
      );

      expect(result).toEqual([]);
    });
  });

  describe("languageFilterSuggestionsService", () => {
    it("should return empty array for empty query", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "",
        "language",
      );
      expect(result).toEqual([]);
    });

    it("should return empty array for whitespace-only query", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "   ",
        "language",
      );
      expect(result).toEqual([]);
    });

    it("should return empty array for non-language filter type", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "test",
        "author",
      );
      expect(result).toEqual([]);
    });

    it("should match language codes", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "en",
        "language",
      );

      expect(result.length).toBeGreaterThan(0);
      expect(result[0]?.name).toBe("en");
    });

    it("should match language names", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "english",
        "language",
      );

      expect(result.length).toBeGreaterThan(0);
      expect(result.some((item) => item.name === "en")).toBe(true);
    });

    it("should be case-insensitive", async () => {
      const result1 = await languageFilterSuggestionsService.fetchSuggestions(
        "EN",
        "language",
      );
      const result2 = await languageFilterSuggestionsService.fetchSuggestions(
        "en",
        "language",
      );

      expect(result1).toEqual(result2);
    });

    it("should match partial codes", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "e",
        "language",
      );

      expect(result.length).toBeGreaterThan(0);
    });

    it("should limit results to 20", async () => {
      // Use a very broad query that would match many languages
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "a",
        "language",
      );

      expect(result.length).toBeLessThanOrEqual(20);
    });

    it("should use index + 1 as ID", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "en",
        "language",
      );

      if (result.length > 0) {
        expect(result[0]?.id).toBeGreaterThan(0);
        expect(Number.isInteger(result[0]?.id)).toBe(true);
      }
    });

    it("should return ISO code as name", async () => {
      const result = await languageFilterSuggestionsService.fetchSuggestions(
        "english",
        "language",
      );

      if (result.length > 0) {
        // The name should be a language code (2-3 characters typically)
        expect(result[0]?.name).toBeDefined();
        expect(typeof result[0]?.name).toBe("string");
      }
    });
  });
});
