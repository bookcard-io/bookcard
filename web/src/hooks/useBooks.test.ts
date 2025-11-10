import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BookListResponse } from "@/types/book";
import { useBooks } from "./useBooks";

describe("useBooks", () => {
  const mockResponse: BookListResponse = {
    items: [
      {
        id: 1,
        title: "Book 1",
        authors: ["Author 1"],
        author_sort: "Author 1",
        pubdate: null,
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid-1",
        thumbnail_url: null,
        has_cover: false,
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
    total_pages: 1,
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should fetch books on mount", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.books).toEqual(mockResponse.items);
    expect(result.current.total).toBe(1);
  });

  it("should not fetch when enabled is false", () => {
    renderHook(() => useBooks({ enabled: false }));
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should include search query in request", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    renderHook(() => useBooks({ search: "test query" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining("search=test+query"),
        expect.any(Object),
      );
    });
  });

  it("should handle fetch error", async () => {
    const mockFetchResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Failed to fetch" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch");
    expect(result.current.books).toEqual([]);
  });

  it("should update query parameters", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setQuery({ search: "new query" });
    });

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining("search=new+query"),
        expect.any(Object),
      );
    });
  });

  it("should accumulate books in infinite scroll mode", async () => {
    const page1Response: BookListResponse = {
      ...mockResponse,
      items: [{ ...mockResponse.items[0], id: 1 }],
      page: 1,
      total_pages: 2,
    };
    const page2Response: BookListResponse = {
      ...mockResponse,
      items: [{ ...mockResponse.items[0], id: 2 }],
      page: 2,
      total_pages: 2,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(page1Response),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(page2Response),
      });

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }));

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    act(() => {
      result.current.loadMore?.();
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(2);
    });
  });

  it("should reset accumulated books when search changes in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result, rerender } = renderHook(
      ({ search }) => useBooks({ infiniteScroll: true, search }),
      { initialProps: { search: "query1" } },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    rerender({ search: "query2" });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should provide hasMore when infinite scroll is enabled", async () => {
    const multiPageResponse: BookListResponse = {
      ...mockResponse,
      total_pages: 3,
    };
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(multiPageResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }));

    await waitFor(() => {
      expect(result.current.hasMore).toBe(true);
    });
  });
});
