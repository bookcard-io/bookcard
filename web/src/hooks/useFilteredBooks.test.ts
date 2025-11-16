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

import { QueryClient } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { BookListResponse } from "@/types/book";
import { createEmptyFilters } from "@/utils/filters";
import { createQueryClientWrapper } from "./test-utils";
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

  let queryClient: QueryClient;
  let wrapper: ReturnType<typeof createQueryClientWrapper>;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });
    wrapper = createQueryClientWrapper(queryClient);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    queryClient.clear();
  });

  it("should not fetch when no filters are provided", async () => {
    renderHook(() => useFilteredBooks({ filters: undefined }), { wrapper });
    // React Query may still initialize, so wait a bit
    await waitFor(
      () => {
        expect(globalThis.fetch).not.toHaveBeenCalled();
      },
      { timeout: 100 },
    );
  });

  it("should not fetch when filters are empty", async () => {
    renderHook(() => useFilteredBooks({ filters: createEmptyFilters() }), {
      wrapper,
    });
    // React Query may still initialize, so wait a bit
    await waitFor(
      () => {
        expect(globalThis.fetch).not.toHaveBeenCalled();
      },
      { timeout: 100 },
    );
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, enabled: true }),
      { wrapper },
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

    const { result } = renderHook(() => useFilteredBooks({ filters }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch");
  });

  it("should accumulate books in infinite scroll mode", async () => {
    const firstItem = mockResponse.items[0];
    if (!firstItem) {
      throw new Error("mockResponse.items[0] is undefined");
    }
    const page1Response: BookListResponse = {
      ...mockResponse,
      items: [{ ...firstItem, id: 1 }],
      page: 1,
      total_pages: 2,
    };
    const page2Response: BookListResponse = {
      ...mockResponse,
      items: [{ ...firstItem, id: 2 }],
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
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
      {
        wrapper,
        initialProps: { filters: filters1 },
      },
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
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
      {
        wrapper,
        initialProps: { filters: filters1 },
      },
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
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
    } as unknown as BookListResponse;
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // hasMore should use currentPage when data.page is undefined
    expect(result.current.hasMore).toBe(true);
  });

  it("should include full parameter in query when full is true", async () => {
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

    renderHook(() => useFilteredBooks({ filters, full: true }), { wrapper });

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalled();
    });

    const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const url = fetchCall?.[0] as string;
    expect(url).toContain("full=true");
  });

  it("should remove book from accumulated books in infinite scroll", async () => {
    const firstItem = mockResponse.items[0];
    if (!firstItem) {
      throw new Error("mockResponse.items[0] is undefined");
    }
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    act(() => {
      result.current.removeBook?.(1);
    });

    // Wait for React Query to update the cache and component to re-render
    await waitFor(() => {
      expect(result.current.books).toHaveLength(0);
    });
  });

  it("should remove book from data items and update total", async () => {
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: false }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    act(() => {
      result.current.removeBook?.(1);
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(0);
    });
    expect(result.current.total).toBe(0);
  });

  it("should add book to accumulated books in infinite scroll", async () => {
    const firstItem = mockResponse.items[0];
    if (!firstItem) {
      throw new Error("mockResponse.items[0] is undefined");
    }
    const newBook = {
      ...firstItem,
      id: 2,
      title: "Book 2",
    };
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const bookFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(newBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(bookFetchResponse);

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(2);
    });

    // Wait for React Query to update the cache and component to re-render
    await waitFor(() => {
      expect(result.current.books).toHaveLength(2);
      expect(result.current.books[0]?.id).toBe(2); // New book should be prepended
    });
  });

  it("should not add duplicate book to accumulated books", async () => {
    const firstItem = mockResponse.items[0];
    if (!firstItem) {
      throw new Error("mockResponse.items[0] is undefined");
    }
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const bookFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(firstItem),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(bookFetchResponse);

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(1);
    });

    // Wait for React Query to update (or confirm it didn't change)
    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Should not add duplicate
    });
  });

  it("should add book to data items and update total", async () => {
    const firstItem = mockResponse.items[0];
    if (!firstItem) {
      throw new Error("mockResponse.items[0] is undefined");
    }
    const newBook = {
      ...firstItem,
      id: 2,
      title: "Book 2",
    };
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const bookFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(newBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(bookFetchResponse);

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(2);
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(2);
    });
    expect(result.current.total).toBe(2);
  });

  it("should not add duplicate book to data items", async () => {
    const firstItem = mockResponse.items[0];
    if (!firstItem) {
      throw new Error("mockResponse.items[0] is undefined");
    }
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const bookFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(firstItem),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(bookFetchResponse);

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(1);
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Should not add duplicate
    });
    expect(result.current.total).toBe(1);
  });

  it("should handle addBook error silently", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const bookFetchResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Book not found" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(bookFetchResponse);

    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(999);
    });

    expect(result.current.books).toHaveLength(1); // Should not change
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it("should not add book when infiniteScroll is false", async () => {
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: false }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(2);
    });

    // Should not fetch or add book
    expect(globalThis.fetch).toHaveBeenCalledTimes(1); // Only initial fetch
    expect(result.current.books).toHaveLength(1);
  });

  it("should return empty result when no active filters", async () => {
    const emptyFilters = createEmptyFilters();
    const { result } = renderHook(
      () => useFilteredBooks({ filters: emptyFilters }),
      { wrapper },
    );

    // When there are no active filters, the query is disabled
    // so it should return empty results immediately
    await waitFor(() => {
      expect(result.current.books).toEqual([]);
      expect(result.current.total).toBe(0);
    });

    // Verify that no fetch was called (query is disabled)
    expect(globalThis.fetch).not.toHaveBeenCalled();

    // Note: isLoading might be true initially even for disabled queries
    // because listQueryEnabled is true, but the query itself is disabled
    // The important thing is that no fetch happens and results are empty
  });

  it("should handle fetch error with detail message", async () => {
    const mockFetchResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Custom error message" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() => useFilteredBooks({ filters }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Custom error message");
  });

  it("should handle fetch error without detail message", async () => {
    const mockFetchResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({}),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() => useFilteredBooks({ filters }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch filtered books");
  });

  it("should refetch books in regular mode", async () => {
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

    const { result } = renderHook(() => useFilteredBooks({ filters }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls.length;

    await act(async () => {
      await result.current.refetch();
    });

    expect(
      (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length,
    ).toBeGreaterThan(initialCallCount);
  });

  it("should refetch books in infinite scroll mode", async () => {
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

    const { result } = renderHook(
      () => useFilteredBooks({ filters, infiniteScroll: true }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls.length;

    await act(async () => {
      await result.current.refetch();
    });

    expect(
      (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length,
    ).toBeGreaterThan(initialCallCount);
  });
});
