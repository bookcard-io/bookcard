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

import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LibraryLoadingProvider } from "@/contexts/LibraryLoadingContext";
import { createEmptyFilters } from "@/utils/filters";
import { useLibraryBooks } from "./useLibraryBooks";

// Mock the dependencies
vi.mock("./useFilteredBooks", () => ({
  useFilteredBooks: vi.fn(),
}));

vi.mock("./useBooks", () => ({
  useBooks: vi.fn(),
}));

vi.mock("./useShelfBooks", () => ({
  useShelfBooks: vi.fn(),
}));

import { useBooks } from "./useBooks";
import { useFilteredBooks } from "./useFilteredBooks";
import { useShelfBooks } from "./useShelfBooks";

/**
 * Wrapper component with LibraryLoadingProvider for tests.
 */
const wrapper = ({ children }: { children: ReactNode }) => {
  return <LibraryLoadingProvider>{children}</LibraryLoadingProvider>;
};

describe("useLibraryBooks", () => {
  const mockBooksResult = {
    books: [],
    total: 0,
    isLoading: false,
    error: null,
    loadMore: vi.fn(),
    hasMore: false,
  };

  const mockShelfBooksResult = {
    bookIds: [],
    total: 0,
    isLoading: false,
    error: null,
  };

  beforeEach(() => {
    (useFilteredBooks as ReturnType<typeof vi.fn>).mockReturnValue(
      mockBooksResult,
    );
    (useBooks as ReturnType<typeof vi.fn>).mockReturnValue(mockBooksResult);
    (useShelfBooks as ReturnType<typeof vi.fn>).mockReturnValue(
      mockShelfBooksResult,
    );
  });

  it("should use filtered books when filters are active", () => {
    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    renderHook(() => useLibraryBooks({ filters }), { wrapper });

    expect(useFilteredBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: true,
        infiniteScroll: true,
        filters,
      }),
    );
  });

  it("should use regular books when filters are not active", () => {
    renderHook(() => useLibraryBooks({}), { wrapper });

    expect(useBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: true,
        infiniteScroll: true,
      }),
    );
  });

  it("should use regular books with search query", () => {
    renderHook(() => useLibraryBooks({ searchQuery: "test" }), { wrapper });

    expect(useBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        search: "test",
      }),
    );
  });

  it("should pass sort parameters", () => {
    renderHook(
      () =>
        useLibraryBooks({
          sortBy: "title",
          sortOrder: "asc",
        }),
      { wrapper },
    );

    expect(useBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        sort_by: "title",
        sort_order: "asc",
      }),
    );
  });

  it("should pass page size", () => {
    renderHook(() => useLibraryBooks({ pageSize: 50 }), { wrapper });

    expect(useBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        page_size: 50,
      }),
    );
  });

  it("should return books from active hook", () => {
    const filteredResult = {
      ...mockBooksResult,
      books: [
        { id: 1, title: "Filtered Book" },
      ] as typeof mockBooksResult.books,
    };
    (useFilteredBooks as ReturnType<typeof vi.fn>).mockReturnValue(
      filteredResult,
    );

    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    const { result } = renderHook(() => useLibraryBooks({ filters }), {
      wrapper,
    });

    expect(result.current.books).toEqual(filteredResult.books);
  });

  it("should filter books by shelf IDs when shelf filter is active", () => {
    const shelfBookIds = [1, 3, 5];
    const allBooks = [
      { id: 1, title: "Book 1" },
      { id: 2, title: "Book 2" },
      { id: 3, title: "Book 3" },
      { id: 4, title: "Book 4" },
      { id: 5, title: "Book 5" },
    ] as typeof mockBooksResult.books;

    (useShelfBooks as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockShelfBooksResult,
      bookIds: shelfBookIds,
      total: shelfBookIds.length,
      isLoading: false,
      error: null,
    });

    (useBooks as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockBooksResult,
      books: allBooks,
    });

    const { result } = renderHook(() => useLibraryBooks({ shelfId: 1 }), {
      wrapper,
    });

    expect(result.current.books).toHaveLength(3);
    expect(result.current.books.map((b) => b.id)).toEqual([1, 3, 5]);
  });

  it("should return empty array when shelf books are loading", () => {
    (useShelfBooks as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockShelfBooksResult,
      isLoading: true,
    });

    const { result } = renderHook(() => useLibraryBooks({ shelfId: 1 }), {
      wrapper,
    });

    expect(result.current.books).toEqual([]);
  });

  it("should return empty array when shelf books have error", () => {
    (useShelfBooks as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockShelfBooksResult,
      error: "Failed to fetch shelf books",
    });

    const { result } = renderHook(() => useLibraryBooks({ shelfId: 1 }), {
      wrapper,
    });

    expect(result.current.books).toEqual([]);
  });

  it("should integrate with library loading context when loading", () => {
    (useBooks as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockBooksResult,
      isLoading: true,
    });

    // The hook should work without errors when loading
    const { result } = renderHook(() => useLibraryBooks({}), { wrapper });

    expect(result.current.isLoading).toBe(true);
    // The useEffect should run and call incrementBooksLoading
    // We can't easily test the cleanup without complex mocking,
    // but we verify the hook works correctly with the context
  });
});
