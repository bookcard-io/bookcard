import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defaultSearchSuggestionsService } from "./searchSuggestionsService";

describe("searchSuggestionsService", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("defaultSearchSuggestionsService (ApiSearchSuggestionsService)", () => {
    it("should return empty response for empty query", async () => {
      const result = await defaultSearchSuggestionsService.fetchSuggestions("");

      expect(result).toEqual({ books: [], authors: [], tags: [] });
    });

    it("should return empty response for whitespace-only query", async () => {
      const result =
        await defaultSearchSuggestionsService.fetchSuggestions("   ");

      expect(result).toEqual({ books: [], authors: [], tags: [] });
    });

    it("should fetch suggestions from API", async () => {
      const mockResponse = {
        books: [{ id: 1, title: "Book 1" }],
        authors: [{ id: 1, name: "Author 1" }],
        tags: [{ id: 1, name: "Tag 1" }],
      };
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result =
        await defaultSearchSuggestionsService.fetchSuggestions("test");

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/books/search/suggestions?q=test",
        { cache: "no-store" },
      );
      expect(result).toEqual(mockResponse);
    });

    it("should encode query in URL", async () => {
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({ books: [], authors: [], tags: [] }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      await defaultSearchSuggestionsService.fetchSuggestions("test query");

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/books/search/suggestions?q=test%20query",
        { cache: "no-store" },
      );
    });

    it("should return empty response on API error", async () => {
      const mockFetchResponse = {
        ok: false,
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result =
        await defaultSearchSuggestionsService.fetchSuggestions("test");

      expect(result).toEqual({ books: [], authors: [], tags: [] });
    });
  });
});
