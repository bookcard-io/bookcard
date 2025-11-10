import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { FilterSuggestionsService } from "@/services/filterSuggestionsService";
import type { SearchSuggestionItem } from "@/types/search";
import { useFilterSuggestions } from "./useFilterSuggestions";

describe("useFilterSuggestions", () => {
  let mockService: FilterSuggestionsService;

  beforeEach(() => {
    vi.useFakeTimers();
    mockService = {
      fetchSuggestions: vi.fn().mockResolvedValue([]),
    };
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should initialize with empty suggestions", () => {
    const { result } = renderHook(() =>
      useFilterSuggestions({
        query: "",
        filterType: "author",
        service: mockService,
      }),
    );
    expect(result.current.suggestions).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it("should fetch suggestions when query is provided", async () => {
    const mockSuggestions: SearchSuggestionItem[] = [
      { id: 1, name: "Author 1" },
    ];
    mockService.fetchSuggestions = vi.fn().mockResolvedValue(mockSuggestions);

    const { result } = renderHook(() =>
      useFilterSuggestions({
        query: "test",
        filterType: "author",
        service: mockService,
        debounceDelay: 0,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(0);
    });
    // Flush promises
    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.suggestions).toEqual(mockSuggestions);
  });

  it("should debounce query", async () => {
    mockService.fetchSuggestions = vi.fn().mockResolvedValue([]);
    const { rerender } = renderHook(
      ({ query }) =>
        useFilterSuggestions({
          query,
          filterType: "author",
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
    expect(mockService.fetchSuggestions).toHaveBeenCalledWith("test", "author");
  });

  it("should not fetch when enabled is false", () => {
    renderHook(() =>
      useFilterSuggestions({
        query: "test",
        filterType: "author",
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

  it("should not fetch when query is empty", () => {
    renderHook(() =>
      useFilterSuggestions({
        query: "",
        filterType: "author",
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
      useFilterSuggestions({
        query: "test",
        filterType: "author",
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
    const mockSuggestions: SearchSuggestionItem[] = [
      { id: 1, name: "Author 1" },
    ];
    mockService.fetchSuggestions = vi.fn().mockResolvedValue(mockSuggestions);

    const { result } = renderHook(() =>
      useFilterSuggestions({
        query: "test",
        filterType: "author",
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
    expect(result.current.suggestions).toEqual(mockSuggestions);

    await act(async () => {
      await result.current.refetch();
    });
    expect(mockService.fetchSuggestions).toHaveBeenCalledTimes(2);
  });

  it("should handle non-Error exceptions", async () => {
    mockService.fetchSuggestions = vi.fn().mockRejectedValue("String error");

    const { result } = renderHook(() =>
      useFilterSuggestions({
        query: "test",
        filterType: "author",
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
    expect(result.current.error).toBe("Unknown error");
    expect(result.current.suggestions).toEqual([]);
  });
});
