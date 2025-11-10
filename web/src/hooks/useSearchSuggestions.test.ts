import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { SearchSuggestionsService } from "@/services/searchSuggestionsService";
import type { SearchSuggestionsResponse } from "@/types/search";
import { useSearchSuggestions } from "./useSearchSuggestions";

describe("useSearchSuggestions", () => {
  let mockService: SearchSuggestionsService;

  beforeEach(() => {
    vi.useFakeTimers();
    mockService = {
      fetchSuggestions: vi.fn().mockResolvedValue({
        books: [],
        authors: [],
        tags: [],
        series: [],
      }),
    };
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should initialize with empty suggestions", () => {
    const { result } = renderHook(() =>
      useSearchSuggestions({
        query: "",
        service: mockService,
      }),
    );
    expect(result.current.suggestions).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it("should fetch suggestions when query is provided", async () => {
    const mockResponse: SearchSuggestionsResponse = {
      books: [{ id: 1, name: "Book 1" }],
      authors: [{ id: 2, name: "Author 1" }],
      tags: [],
      series: [],
    };
    mockService.fetchSuggestions = vi.fn().mockResolvedValue(mockResponse);

    const { result } = renderHook(() =>
      useSearchSuggestions({
        query: "test",
        service: mockService,
        debounceDelay: 0,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(0);
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.suggestions.length).toBeGreaterThan(0);
  });

  it("should debounce query", async () => {
    mockService.fetchSuggestions = vi.fn().mockResolvedValue({
      books: [],
      authors: [],
      tags: [],
      series: [],
    });
    const { rerender } = renderHook(
      ({ query }) =>
        useSearchSuggestions({
          query,
          service: mockService,
          debounceDelay: 300,
        }),
      { initialProps: { query: "t" } },
    );

    // Clear any initial calls
    vi.clearAllMocks();

    rerender({ query: "te" });
    rerender({ query: "tes" });
    rerender({ query: "test" });

    act(() => {
      vi.advanceTimersByTime(300);
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(mockService.fetchSuggestions).toHaveBeenCalledTimes(1);
    expect(mockService.fetchSuggestions).toHaveBeenCalledWith("test");
  });

  it("should not fetch when enabled is false", () => {
    renderHook(() =>
      useSearchSuggestions({
        query: "test",
        enabled: false,
        service: mockService,
        debounceDelay: 0,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(0);
    });
    expect(mockService.fetchSuggestions).not.toHaveBeenCalled();
  });

  it("should handle fetch error", async () => {
    mockService.fetchSuggestions = vi
      .fn()
      .mockRejectedValue(new Error("Fetch failed"));

    const { result } = renderHook(() =>
      useSearchSuggestions({
        query: "test",
        service: mockService,
        debounceDelay: 0,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(0);
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.error).toBe("Fetch failed");
    expect(result.current.suggestions).toEqual([]);
  });

  it("should refetch suggestions", async () => {
    const mockResponse: SearchSuggestionsResponse = {
      books: [{ id: 1, name: "Book 1" }],
      authors: [],
      tags: [],
      series: [],
    };
    mockService.fetchSuggestions = vi.fn().mockResolvedValue(mockResponse);

    const { result } = renderHook(() =>
      useSearchSuggestions({
        query: "test",
        service: mockService,
        debounceDelay: 0,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(0);
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.suggestions.length).toBeGreaterThan(0);

    await act(async () => {
      await result.current.refetch();
    });
    expect(mockService.fetchSuggestions).toHaveBeenCalledTimes(2);
  });
});
