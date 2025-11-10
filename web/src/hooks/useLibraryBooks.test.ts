import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createEmptyFilters } from "@/utils/filters";
import { useLibraryBooks } from "./useLibraryBooks";

// Mock the dependencies
vi.mock("./useFilteredBooks", () => ({
  useFilteredBooks: vi.fn(),
}));

vi.mock("./useBooks", () => ({
  useBooks: vi.fn(),
}));

import { useBooks } from "./useBooks";
import { useFilteredBooks } from "./useFilteredBooks";

describe("useLibraryBooks", () => {
  const mockBooksResult = {
    books: [],
    total: 0,
    isLoading: false,
    error: null,
    loadMore: vi.fn(),
    hasMore: false,
  };

  beforeEach(() => {
    (useFilteredBooks as ReturnType<typeof vi.fn>).mockReturnValue(
      mockBooksResult,
    );
    (useBooks as ReturnType<typeof vi.fn>).mockReturnValue(mockBooksResult);
  });

  it("should use filtered books when filters are active", () => {
    const filters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    renderHook(() => useLibraryBooks({ filters }));

    expect(useFilteredBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: true,
        infiniteScroll: true,
        filters,
      }),
    );
  });

  it("should use regular books when filters are not active", () => {
    renderHook(() => useLibraryBooks({}));

    expect(useBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        enabled: true,
        infiniteScroll: true,
      }),
    );
  });

  it("should use regular books with search query", () => {
    renderHook(() => useLibraryBooks({ searchQuery: "test" }));

    expect(useBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        search: "test",
      }),
    );
  });

  it("should pass sort parameters", () => {
    renderHook(() =>
      useLibraryBooks({
        sortBy: "title",
        sortOrder: "asc",
      }),
    );

    expect(useBooks).toHaveBeenCalledWith(
      expect.objectContaining({
        sort_by: "title",
        sort_order: "asc",
      }),
    );
  });

  it("should pass page size", () => {
    renderHook(() => useLibraryBooks({ pageSize: 50 }));

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

    const { result } = renderHook(() => useLibraryBooks({ filters }));

    expect(result.current.books).toEqual(filteredResult.books);
  });
});
