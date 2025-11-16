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
import { createQueryClientWrapper } from "./test-utils";
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

  it("should fetch books on mount", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.books).toEqual(mockResponse.items);
    expect(result.current.total).toBe(1);
  });

  it("should not fetch when enabled is false", async () => {
    renderHook(() => useBooks({ enabled: false }), { wrapper });
    // React Query may still initialize, so wait a bit
    await waitFor(
      () => {
        // With enabled: false, React Query won't fetch
        expect(globalThis.fetch).not.toHaveBeenCalled();
      },
      { timeout: 100 },
    );
  });

  it("should include search query in request", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    renderHook(() => useBooks({ search: "test query" }), { wrapper });

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

    const { result } = renderHook(() => useBooks(), { wrapper });

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

    const { result } = renderHook(() => useBooks(), { wrapper });

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

    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(page1Response),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(page2Response),
      });

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

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
      {
        wrapper,
        initialProps: { search: "query1" },
      },
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

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.hasMore).toBe(true);
    });
  });

  it("should reset accumulated books when sort_order changes in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result, rerender } = renderHook(
      ({ sort_order }) => useBooks({ infiniteScroll: true, sort_order }),
      {
        wrapper,
        initialProps: { sort_order: "asc" as "asc" | "desc" },
      },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    rerender({ sort_order: "desc" as "asc" | "desc" });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should reset accumulated books when sort_by changes via setQuery in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setQuery({ sort_by: "title" });
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should reset accumulated books when sort_order changes via setQuery in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setQuery({ sort_order: "asc" });
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should not load more when infinite scroll is disabled", async () => {
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

    const { result } = renderHook(() => useBooks({ infiniteScroll: false }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialPage = result.current.page;
    const fetchCallCount = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls.length;

    act(() => {
      // loadMore should not exist when infiniteScroll is false
      expect(result.current.loadMore).toBeUndefined();
    });

    await waitFor(() => {
      // Page should not have changed
      expect(result.current.page).toBe(initialPage);
      // No additional fetch calls
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBe(fetchCallCount);
    });
  });

  it("should not load more when data is null", async () => {
    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

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

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

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

  it("should not update sort_by when sort_by is undefined", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result, rerender } = renderHook(
      ({ sort_by }) => useBooks({ sort_by }),
      {
        wrapper,
        initialProps: {
          sort_by: "title" as
            | "timestamp"
            | "pubdate"
            | "title"
            | "author_sort"
            | "series_index"
            | undefined,
        },
      },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Change to undefined
    rerender({ sort_by: undefined });

    // Should not cause issues
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it("should reset accumulated books when page_size changes via setQuery in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setQuery({ page_size: 40 });
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should reset accumulated books when search changes via setQuery in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setQuery({ search: "new search" });
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should reset accumulated books when sort_by changes in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result, rerender } = renderHook(
      ({ sort_by }) => useBooks({ infiniteScroll: true, sort_by }),
      {
        wrapper,
        initialProps: {
          sort_by: "title" as
            | "timestamp"
            | "pubdate"
            | "title"
            | "author_sort"
            | "series_index"
            | undefined,
        },
      },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Change sort_by
    rerender({
      sort_by: "pubdate" as
        | "timestamp"
        | "pubdate"
        | "title"
        | "author_sort"
        | "series_index"
        | undefined,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should update page_size when page_size changes", async () => {
    const responseWithPageSize40: BookListResponse = {
      ...mockResponse,
      page_size: 40,
    };
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(responseWithPageSize40),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result, rerender } = renderHook(
      ({ page_size }) => useBooks({ page_size }),
      {
        wrapper,
        initialProps: { page_size: 20 },
      },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Clear previous calls
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockClear();

    // Change page_size
    rerender({ page_size: 40 });

    // Wait for the fetch to complete with new page_size
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining("page_size=40"),
        expect.any(Object),
      );
    });

    // The pageSize should reflect the new value from the response
    await waitFor(() => {
      expect(result.current.pageSize).toBe(40);
    });
  });

  it("should update page when setQuery is called with page", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        ...mockResponse,
        page: 2,
        total_pages: 3,
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setQuery({ page: 2 });
    });

    await waitFor(() => {
      expect(result.current.page).toBe(2);
    });
  });

  it("should reset accumulated books when sort_order changes via setQuery in infinite scroll", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setQuery({ sort_order: "asc" });
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1); // Reset
    });
  });

  it("should use page fallback when data.page is undefined in loadMore", async () => {
    const responseWithoutPage = {
      ...mockResponse,
      page: undefined,
      total_pages: 3,
    } as unknown as BookListResponse;
    const page2Response = {
      ...mockResponse,
      page: 2,
      total_pages: 3,
    };
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(responseWithoutPage),
    };
    const page2FetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(page2Response),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(page2FetchResponse);

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Load more - React Query's infinite query will use getNextPageParam
    // which uses lastPage.page ?? 1, so if page is undefined, it uses 1, then increments to 2
    act(() => {
      if (result.current.loadMore) {
        result.current.loadMore();
      }
    });

    // Should load page 2 (since first page had undefined page, getNextPageParam uses 1, then increments)
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining("page=2"),
        expect.any(Object),
      );
    });
  });

  it("should use page fallback when data.page is undefined in hasMore", async () => {
    const responseWithoutPage = {
      ...mockResponse,
      page: undefined,
      total_pages: 3,
    } as unknown as BookListResponse;
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(responseWithoutPage),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Set page to 2
    act(() => {
      result.current.setQuery({ page: 2 });
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // hasMore should use page (2) as fallback since data.page is undefined
    // 2 < 3, so hasMore should be true
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

    renderHook(() => useBooks({ full: true }), { wrapper });

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining("full=true"),
        expect.any(Object),
      );
    });
  });

  it("should remove book from accumulated books and data", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    act(() => {
      result.current.removeBook?.(1);
    });

    // Wait for React Query to update the cache and component to re-render
    await waitFor(() => {
      // Should remove from accumulated books
      expect(result.current.books).toHaveLength(0);
      // Should also update data
      expect(result.current.total).toBe(0);
    });
  });

  it("should update data when removing book even if prev is null", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockFetchResponse,
    );

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    // Remove the book
    act(() => {
      result.current.removeBook?.(1);
    });

    // Wait for React Query to update the cache and component to re-render
    await waitFor(() => {
      // Now data should be updated (since we removed the only book)
      // The removeBook function should handle prev being null
      // This tests the data update path
      expect(result.current.total).toBe(0);
    });
  });

  it("should add book to accumulated books and data", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const newBookResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        id: 2,
        title: "New Book",
        authors: ["New Author"],
        author_sort: "New Author",
        pubdate: null,
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid-2",
        thumbnail_url: null,
        has_cover: false,
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(newBookResponse);

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(2);
    });

    // Should add to accumulated books (lines 323-329)
    await waitFor(() => {
      expect(result.current.books).toHaveLength(2);
    });
    // Should also update data (lines 332-343)
    expect(result.current.total).toBe(2);
  });

  it("should not add duplicate book when adding existing book", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const existingBookResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse.items[0]),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(existingBookResponse);

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    const initialBooks = [...result.current.books];

    await act(async () => {
      await result.current.addBook?.(1); // Add existing book
    });

    // Should not add duplicate (lines 325-327, 335-337)
    expect(result.current.books).toEqual(initialBooks);
  });

  it("should handle addBook error gracefully", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const errorResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Not found" }),
    };
    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(mockFetchResponse)
      .mockResolvedValueOnce(errorResponse);

    const { result } = renderHook(() => useBooks({ infiniteScroll: true }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    await act(async () => {
      await result.current.addBook?.(999);
    });

    // Should log error but not crash (lines 344-346)
    expect(consoleErrorSpy).toHaveBeenCalled();
    // Books should remain unchanged
    expect(result.current.books).toHaveLength(1);

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

    const { result } = renderHook(() => useBooks({ infiniteScroll: false }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // addBook should not exist when infiniteScroll is false (line 305-307)
    expect(result.current.addBook).toBeUndefined();
  });
});
