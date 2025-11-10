import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BookListResponse } from "@/types/book";
import { createEmptyFilters } from "@/utils/filters";
import { useFilteredBooks } from "./useFilteredBooks";

describe("useFilteredBooks", () => {
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

  it("should not fetch when no filters are provided", () => {
    renderHook(() => useFilteredBooks({ filters: undefined }));
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should not fetch when filters are empty", () => {
    renderHook(() => useFilteredBooks({ filters: createEmptyFilters() }));
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should fetch filtered books", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() =>
      useFilteredBooks({ filters, enabled: true }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.books).toEqual(mockResponse.items);
  });

  it("should handle fetch error", async () => {
    const mockFetchResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Failed to fetch" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() => useFilteredBooks({ filters }));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch");
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

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
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

    const { result } = renderHook(() =>
      useFilteredBooks({ filters, infiniteScroll: true }),
    );

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

  it("should reset accumulated books when filters change", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters1 = {
      ...createEmptyFilters(),
      authorIds: [1],
    };
    const filters2 = {
      ...createEmptyFilters(),
      authorIds: [2],
    };

    const { result, rerender } = renderHook(
      ({ filters }) => useFilteredBooks({ filters, infiniteScroll: true }),
      { initialProps: { filters: filters1 } },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    rerender({ filters: filters2 });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should not load more when data is null", async () => {
    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() =>
      useFilteredBooks({ filters, infiniteScroll: true }),
    );

    // Before any data is loaded, data should be null
    act(() => {
      if (result.current.loadMore) {
        result.current.loadMore();
      }
    });

    // Should not cause any fetch calls since data is null
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledTimes(1); // Only initial fetch
    });
  });

  it("should not load more when already on last page", async () => {
    const lastPageResponse: BookListResponse = {
      ...mockResponse,
      page: 2,
      total_pages: 2,
    };
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(lastPageResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() =>
      useFilteredBooks({ filters, infiniteScroll: true }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.page).toBe(2);
    });

    const fetchCallCount = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls.length;

    act(() => {
      if (result.current.loadMore) {
        result.current.loadMore();
      }
    });

    // Should not cause additional fetch calls since we're on the last page
    await waitFor(() => {
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBe(fetchCallCount);
    });
  });

  it("should reset accumulated books when filters change in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters1 = {
      ...createEmptyFilters(),
      authorIds: [1],
    };
    const filters2 = {
      ...createEmptyFilters(),
      authorIds: [2],
    };

    const { result, rerender } = renderHook(
      ({ filters }) => useFilteredBooks({ filters, infiniteScroll: true }),
      { initialProps: { filters: filters1 } },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    rerender({ filters: filters2 });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should not load more when already on last page", async () => {
    const lastPageResponse: BookListResponse = {
      ...mockResponse,
      page: 2,
      total_pages: 2,
    };
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(lastPageResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() =>
      useFilteredBooks({ filters, infiniteScroll: true }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.page).toBe(2);
    });

    const fetchCallCount = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls.length;

    act(() => {
      if (result.current.loadMore) {
        result.current.loadMore();
      }
    });

    // Should not cause additional fetch calls since we're on the last page
    await waitFor(() => {
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBe(fetchCallCount);
    });
  });

  it("should use currentPage when data.page is undefined in hasMore", async () => {
    const responseWithoutPage = {
      ...mockResponse,
      page: undefined,
      total_pages: 2,
    } as BookListResponse;
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(responseWithoutPage),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() =>
      useFilteredBooks({ filters, infiniteScroll: true }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // hasMore should use currentPage when data.page is undefined
    expect(result.current.hasMore).toBe(true);
  });
});
