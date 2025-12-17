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
import type { AuthorListResponse, AuthorWithMetadata } from "@/types/author";
import {
  createMockFetchWithActiveLibrary,
  createQueryClientWrapper,
  getNonProviderFetchCalls,
} from "./test-utils";
import { useAuthors } from "./useAuthors";

/**
 * Create a mock author for testing.
 */
function createMockAuthor(key: string, name: string): AuthorWithMetadata {
  return {
    key,
    name,
  };
}

describe("useAuthors", () => {
  const mockResponse: AuthorListResponse = {
    items: [
      createMockAuthor("OL1A", "Author 1"),
      createMockAuthor("OL2B", "Author 2"),
    ],
    total: 2,
    page: 1,
    page_size: 20,
    total_pages: 1,
  };

  let queryClient: QueryClient;
  let wrapper: ReturnType<typeof createQueryClientWrapper>;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary(),
    );
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

  describe("list query mode", () => {
    it("should fetch authors on mount", async () => {
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(mockFetchResponse),
      );

      const { result } = renderHook(() => useAuthors(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.authors).toEqual(mockResponse.items);
      expect(result.current.total).toBe(2);
    });

    it("should use custom pageSize", async () => {
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(mockFetchResponse),
      );

      renderHook(() => useAuthors({ pageSize: 50 }), { wrapper });

      await waitFor(() => {
        expect(globalThis.fetch).toHaveBeenCalledWith(
          expect.stringContaining("page_size=50"),
          expect.any(Object),
        );
      });
    });

    it("should use 'all' filter", async () => {
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(mockFetchResponse),
      );

      renderHook(() => useAuthors({ filter: "all" }), { wrapper });

      await waitFor(() => {
        const nonProviderCalls = getNonProviderFetchCalls(
          globalThis.fetch as ReturnType<typeof vi.fn>,
        );
        expect(nonProviderCalls.length).toBeGreaterThan(0);
      });
    });

    it("should use 'unmatched' filter", async () => {
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(mockFetchResponse),
      );

      renderHook(() => useAuthors({ filter: "unmatched" }), { wrapper });

      await waitFor(() => {
        expect(globalThis.fetch).toHaveBeenCalledWith(
          expect.stringContaining("filter=unmatched"),
          expect.any(Object),
        );
      });
    });

    it("should not fetch when enabled is false", async () => {
      renderHook(() => useAuthors({ enabled: false }), { wrapper });

      await waitFor(
        () => {
          const nonProviderCalls = getNonProviderFetchCalls(
            globalThis.fetch as ReturnType<typeof vi.fn>,
          );
          expect(nonProviderCalls).toHaveLength(0);
        },
        { timeout: 100 },
      );
    });

    it("should handle fetch error", async () => {
      const mockFetchResponse = {
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "Failed to fetch" }),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(mockFetchResponse),
      );

      const { result } = renderHook(() => useAuthors(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBe("Failed to fetch");
      expect(result.current.authors).toEqual([]);
    });

    it("should show 'no_active_library' error when no active library", async () => {
      // Mock active library to return null
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        (url: string) => {
          if (url === "/api/libraries/active") {
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve(null),
            } as Response);
          }
          if (url === "/api/auth/me") {
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve({ id: 1, username: "test" }),
            } as Response);
          }
          if (url === "/api/auth/settings") {
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve({ settings: {} }),
            } as Response);
          }
          return Promise.reject(new Error(`Unexpected fetch to ${url}`));
        },
      );

      const { result } = renderHook(() => useAuthors(), { wrapper });

      await waitFor(() => {
        expect(result.current.error).toBe("no_active_library");
      });
    });
  });

  describe("infinite scroll mode", () => {
    it("should accumulate authors across pages", async () => {
      const page1Response: AuthorListResponse = {
        items: [createMockAuthor("OL1A", "Author 1")],
        total: 2,
        page: 1,
        page_size: 1,
        total_pages: 2,
      };
      const page2Response: AuthorListResponse = {
        items: [createMockAuthor("OL2B", "Author 2")],
        total: 2,
        page: 2,
        page_size: 1,
        total_pages: 2,
      };

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(
          {
            ok: true,
            json: vi.fn().mockResolvedValue(page1Response),
          },
          {
            ok: true,
            json: vi.fn().mockResolvedValue(page2Response),
          },
        ),
      );

      const { result } = renderHook(
        () => useAuthors({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      await waitFor(() => {
        expect(result.current.authors).toHaveLength(1);
      });

      expect(result.current.authors[0]?.name).toBe("Author 1");
      expect(result.current.hasMore).toBe(true);

      act(() => {
        result.current.loadMore?.();
      });

      await waitFor(() => {
        expect(result.current.authors).toHaveLength(2);
      });

      expect(result.current.authors[1]?.name).toBe("Author 2");
      expect(result.current.hasMore).toBe(false);
    });

    it("should deduplicate authors by key", async () => {
      const page1Response: AuthorListResponse = {
        items: [createMockAuthor("OL1A", "Author 1")],
        total: 2,
        page: 1,
        page_size: 1,
        total_pages: 2,
      };
      const page2Response: AuthorListResponse = {
        items: [createMockAuthor("OL1A", "Author 1 Duplicate")],
        total: 2,
        page: 2,
        page_size: 1,
        total_pages: 2,
      };

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(
          {
            ok: true,
            json: vi.fn().mockResolvedValue(page1Response),
          },
          {
            ok: true,
            json: vi.fn().mockResolvedValue(page2Response),
          },
        ),
      );

      const { result } = renderHook(
        () => useAuthors({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      await waitFor(() => {
        expect(result.current.authors).toHaveLength(1);
      });

      act(() => {
        result.current.loadMore?.();
      });

      await waitFor(() => {
        // Should still be 1 due to deduplication
        expect(result.current.authors).toHaveLength(1);
      });
    });

    it("should deduplicate authors by name when key is missing", async () => {
      const author1 = createMockAuthor("", "Author 1");
      author1.key = undefined;
      const author2 = createMockAuthor("", "Author 1");
      author2.key = undefined;

      const page1Response: AuthorListResponse = {
        items: [author1],
        total: 2,
        page: 1,
        page_size: 1,
        total_pages: 2,
      };
      const page2Response: AuthorListResponse = {
        items: [author2],
        total: 2,
        page: 2,
        page_size: 1,
        total_pages: 2,
      };

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(
          {
            ok: true,
            json: vi.fn().mockResolvedValue(page1Response),
          },
          {
            ok: true,
            json: vi.fn().mockResolvedValue(page2Response),
          },
        ),
      );

      const { result } = renderHook(
        () => useAuthors({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      await waitFor(() => {
        expect(result.current.authors).toHaveLength(1);
      });

      act(() => {
        result.current.loadMore?.();
      });

      await waitFor(() => {
        expect(result.current.authors).toHaveLength(1);
      });
    });

    it("should not load more when hasMore is false", async () => {
      const page1Response: AuthorListResponse = {
        items: [createMockAuthor("OL1A", "Author 1")],
        total: 1,
        page: 1,
        page_size: 1,
        total_pages: 1,
      };

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary({
          ok: true,
          json: vi.fn().mockResolvedValue(page1Response),
        }),
      );

      const { result } = renderHook(
        () => useAuthors({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      await waitFor(() => {
        expect(result.current.hasMore).toBe(false);
      });

      const fetchCallCount = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls.length;

      act(() => {
        result.current.loadMore?.();
      });

      // Should not trigger additional fetch
      await waitFor(() => {
        expect(
          (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length,
        ).toBe(fetchCallCount);
      });
    });

    it("should provide no-op loadMore when infiniteScroll is false", () => {
      const { result } = renderHook(
        () => useAuthors({ infiniteScroll: false }),
        {
          wrapper,
        },
      );

      // loadMore is always defined but is a no-op when infiniteScroll is false
      expect(result.current.loadMore).toBeDefined();
      expect(typeof result.current.loadMore).toBe("function");
      // hasMore is false when infiniteScroll is false (not undefined)
      expect(result.current.hasMore).toBe(false);

      // Calling loadMore should not trigger any fetch
      const fetchCallCount = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls.length;
      act(() => {
        result.current.loadMore?.();
      });
      // Should not trigger additional fetch
      expect(
        (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.length,
      ).toBe(fetchCallCount);
    });
  });

  describe("loading states", () => {
    it("should show loading when active library is loading", () => {
      // This is tested implicitly through the wrapper, but we can verify
      // that isLoading reflects the active library loading state
      const { result } = renderHook(() => useAuthors(), { wrapper });

      // Initially loading due to active library fetch
      expect(result.current.isLoading).toBe(true);
    });

    it("should show loading when query is fetching", async () => {
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(mockFetchResponse),
      );

      const { result } = renderHook(() => useAuthors(), { wrapper });

      // Should be loading initially
      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe("total calculation", () => {
    it("should use total from first page in infinite scroll mode", async () => {
      const page1Response: AuthorListResponse = {
        items: [createMockAuthor("OL1A", "Author 1")],
        total: 100,
        page: 1,
        page_size: 1,
        total_pages: 100,
      };

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary({
          ok: true,
          json: vi.fn().mockResolvedValue(page1Response),
        }),
      );

      const { result } = renderHook(
        () => useAuthors({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      await waitFor(() => {
        expect(result.current.total).toBe(100);
      });
    });

    it("should use total from list query in list mode", async () => {
      const mockFetchResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue(mockResponse),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary(mockFetchResponse),
      );

      const { result } = renderHook(() => useAuthors(), { wrapper });

      await waitFor(() => {
        expect(result.current.total).toBe(2);
      });
    });
  });
});
