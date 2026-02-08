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

import { vi } from "vitest";

vi.mock("@/services/shelfService", () => ({
  getShelfBooks: vi.fn(),
}));

vi.mock("@/contexts/ActiveLibraryContext", () => ({
  useActiveLibrary: vi.fn(),
}));

vi.mock("@/contexts/ShelvesContext", () => ({
  useShelvesContext: vi.fn(),
}));

vi.mock("@/utils/fetch", () => ({
  deduplicateFetch: vi.fn((_key: string, fn: () => Promise<unknown>) => fn()),
  generateFetchKey: vi.fn(
    (url: string, init?: { body?: string }) => `${url}:${init?.body ?? ""}`,
  ),
}));

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { SortField, SortOrder } from "@/constants/librarySorting";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { getShelfBooks } from "@/services/shelfService";
import type { BookListResponse } from "@/types/book";
import type { Shelf } from "@/types/shelf";
import { useShelfBooksView } from "./useShelfBooksView";

function createWrapper(queryClient: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const mockBook = (id: number, title: string) => ({
  id,
  title,
  authors: ["Author"],
  author_sort: "Author",
  title_sort: null,
  pubdate: null,
  timestamp: null,
  series: null,
  series_id: null,
  series_index: null,
  isbn: null,
  uuid: `uuid-${id}`,
  thumbnail_url: null,
  has_cover: false,
});

const mockBookListResponse = (
  ids: number[],
  titles: string[],
): BookListResponse => ({
  items: ids.map((id, i) => mockBook(id, titles[i] ?? `Book ${id}`)),
  total: ids.length,
  page: 1,
  page_size: ids.length,
  total_pages: 1,
});

const mockShelf = (overrides: Partial<Shelf> = {}): Shelf => ({
  id: 1,
  uuid: "shelf-uuid-1",
  name: "Test Shelf",
  description: null,
  cover_picture: null,
  library_id: 1,
  user_id: 1,
  is_public: false,
  is_active: true,
  shelf_type: "shelf",
  last_modified: "2024-01-01T00:00:00Z",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  book_count: 3,
  ...overrides,
});

describe("useShelfBooksView", () => {
  let queryClient: QueryClient;
  let wrapper: ReturnType<typeof createWrapper>;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();

    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });
    wrapper = createWrapper(queryClient);

    // Default: active library is loaded
    vi.mocked(useActiveLibrary).mockReturnValue({
      activeLibrary: {
        id: 1,
        name: "Test Library",
        calibre_db_path: "/path",
        calibre_db_file: "metadata.db",
        calibre_uuid: null,
        use_split_library: false,
        split_library_dir: null,
        auto_reconnect: false,
        is_active: true,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
      isLoading: false,
      refresh: vi.fn(),
      visibleLibraries: [],
      selectedLibraryId: null,
      setSelectedLibraryId: vi.fn(),
    });

    // Default: shelf with id=1 exists and has 3 books
    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [mockShelf()],
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    queryClient.clear();
  });

  it("should return empty state when no shelfId is provided", () => {
    const { result } = renderHook(() => useShelfBooksView({}), { wrapper });

    expect(result.current.books).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.error).toBeNull();
    expect(getShelfBooks).not.toHaveBeenCalled();
  });

  it("should fetch shelf books with default sort params", async () => {
    const ids = [1, 2, 3];
    vi.mocked(getShelfBooks).mockResolvedValue(ids);

    const response = mockBookListResponse(ids, ["Charlie", "Alpha", "Bravo"]);
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(response),
    } as Response);

    const { result } = renderHook(() => useShelfBooksView({ shelfId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(3);
    });

    expect(result.current.books).toEqual(response.items);
    expect(result.current.total).toBe(3);
    expect(result.current.error).toBeNull();
  });

  it("should pass sortBy and sortOrder to the books filter API", async () => {
    const ids = [1, 2];
    vi.mocked(getShelfBooks).mockResolvedValue(ids);

    const response = mockBookListResponse(ids, ["Alpha", "Bravo"]);
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(response),
    } as Response);

    const { result } = renderHook(
      () =>
        useShelfBooksView({
          shelfId: 1,
          sortBy: "title",
          sortOrder: "asc",
        }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(2);
    });

    // Verify the fetch URL includes the correct sort params
    const fetchCalls = vi.mocked(globalThis.fetch).mock.calls;
    const filterCall = fetchCalls.find(
      (call) =>
        typeof call[0] === "string" &&
        (call[0] as string).includes("/api/books/filter"),
    );
    expect(filterCall).toBeDefined();
    const url = filterCall?.[0] as string;
    expect(url).toContain("sort_by=title");
    expect(url).toContain("sort_order=asc");
  });

  it("should use default timestamp/desc when sortBy and sortOrder are omitted", async () => {
    const ids = [1];
    vi.mocked(getShelfBooks).mockResolvedValue(ids);

    const response = mockBookListResponse(ids, ["Book 1"]);
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(response),
    } as Response);

    const { result } = renderHook(() => useShelfBooksView({ shelfId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    const fetchCalls = vi.mocked(globalThis.fetch).mock.calls;
    const filterCall = fetchCalls.find(
      (call) =>
        typeof call[0] === "string" &&
        (call[0] as string).includes("/api/books/filter"),
    );
    expect(filterCall).toBeDefined();
    const url = filterCall?.[0] as string;
    expect(url).toContain("sort_by=timestamp");
    expect(url).toContain("sort_order=desc");
  });

  it("should re-fetch when sortBy changes", async () => {
    const ids = [1, 2];
    vi.mocked(getShelfBooks).mockResolvedValue(ids);

    const responseByTimestamp = mockBookListResponse(ids, ["Bravo", "Alpha"]);
    const responseByTitle = mockBookListResponse(ids, ["Alpha", "Bravo"]);

    vi.mocked(globalThis.fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(responseByTimestamp),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(responseByTitle),
      } as Response);

    const { result, rerender } = renderHook(
      ({ sortBy, sortOrder }: { sortBy: SortField; sortOrder: SortOrder }) =>
        useShelfBooksView({
          shelfId: 1,
          sortBy,
          sortOrder,
        }),
      {
        wrapper,
        initialProps: {
          sortBy: "timestamp" as SortField,
          sortOrder: "desc" as SortOrder,
        },
      },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(2);
    });

    expect(result.current.books[0]?.title).toBe("Bravo");

    // Change sort — should trigger a new query
    rerender({ sortBy: "title", sortOrder: "asc" });

    await waitFor(() => {
      expect(result.current.books[0]?.title).toBe("Alpha");
    });

    // getShelfBooks called twice (once per query key change)
    expect(getShelfBooks).toHaveBeenCalledTimes(2);
  });

  it("should return books in API response order, not shelf ID order", async () => {
    // Shelf returns IDs in order [3, 1, 2] but API returns sorted by title
    const shelfIds = [3, 1, 2];
    vi.mocked(getShelfBooks).mockResolvedValue(shelfIds);

    // API returns sorted by title (Alpha=1, Bravo=2, Charlie=3)
    const response = mockBookListResponse(
      [1, 2, 3],
      ["Alpha", "Bravo", "Charlie"],
    );
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(response),
    } as Response);

    const { result } = renderHook(
      () =>
        useShelfBooksView({
          shelfId: 1,
          sortBy: "title",
          sortOrder: "asc",
        }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(3);
    });

    // Books should be in API order (Alpha, Bravo, Charlie), NOT shelf order
    expect(result.current.books.map((b) => b.title)).toEqual([
      "Alpha",
      "Bravo",
      "Charlie",
    ]);
  });

  it("should report no_active_library error when no library is active", () => {
    vi.mocked(useActiveLibrary).mockReturnValue({
      activeLibrary: null,
      isLoading: false,
      refresh: vi.fn(),
      visibleLibraries: [],
      selectedLibraryId: null,
      setSelectedLibraryId: vi.fn(),
    });

    const { result } = renderHook(() => useShelfBooksView({ shelfId: 1 }), {
      wrapper,
    });

    expect(result.current.error).toBe("no_active_library");
    expect(getShelfBooks).not.toHaveBeenCalled();
  });

  it("should not fetch when shelfId is 0", () => {
    const { result } = renderHook(() => useShelfBooksView({ shelfId: 0 }), {
      wrapper,
    });

    expect(result.current.books).toEqual([]);
    expect(getShelfBooks).not.toHaveBeenCalled();
  });

  it("should handle empty shelf gracefully", async () => {
    vi.mocked(getShelfBooks).mockResolvedValue([]);

    const { result } = renderHook(() => useShelfBooksView({ shelfId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.books).toEqual([]);
    // fetch should not be called for book details when no IDs
    const fetchCalls = vi.mocked(globalThis.fetch).mock.calls;
    const filterCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" &&
        (call[0] as string).includes("/api/books/filter"),
    );
    expect(filterCalls).toHaveLength(0);
  });

  it("should use shelf total from ShelvesContext", async () => {
    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [mockShelf({ book_count: 42 })],
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    const ids = [1, 2];
    vi.mocked(getShelfBooks).mockResolvedValue(ids);

    const response = mockBookListResponse(ids, ["Alpha", "Bravo"]);
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(response),
    } as Response);

    const { result } = renderHook(() => useShelfBooksView({ shelfId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.books).toHaveLength(2);
    });

    // Total comes from shelves context, not from fetched books length
    expect(result.current.total).toBe(42);
  });

  it("should pass shelfSortBy and shelfSortOrder to the shelf endpoint", async () => {
    const ids = [1];
    vi.mocked(getShelfBooks).mockResolvedValue(ids);

    const response = mockBookListResponse(ids, ["Book 1"]);
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(response),
    } as Response);

    const { result } = renderHook(
      () =>
        useShelfBooksView({
          shelfId: 1,
          shelfSortBy: "date_added",
          shelfSortOrder: "desc",
        }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.books).toHaveLength(1);
    });

    expect(getShelfBooks).toHaveBeenCalledWith(1, 1, "date_added", 20, "desc");
  });
});
