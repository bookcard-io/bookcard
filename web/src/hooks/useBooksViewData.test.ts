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
import { createRef } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Book } from "@/types/book";
import { useBooksViewData } from "./useBooksViewData";

import * as useLibraryBooksModule from "./useLibraryBooks";

// Mock the dependencies
vi.mock("./useLibraryBooks", () => ({
  useLibraryBooks: vi.fn(() => ({
    books: [],
    isLoading: false,
    error: null,
    total: 0,
    loadMore: undefined,
    hasMore: undefined,
    removeBook: undefined,
    addBook: undefined,
  })),
}));

vi.mock("./useBookDataUpdates", () => ({
  useBookDataUpdates: vi.fn(() => ({
    bookDataOverrides: {},
    updateBook: vi.fn(),
  })),
}));

vi.mock("@/utils/books", () => ({
  deduplicateBooks: vi.fn((books) => books),
}));

describe("useBooksViewData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return books view data", () => {
    const { result } = renderHook(() => useBooksViewData({}));

    expect(result.current.uniqueBooks).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.total).toBe(0);
    expect(result.current.updateBook).toBeDefined();
  });

  it("should expose removeBook and addBook via ref", () => {
    const bookDataUpdateRef = createRef<{
      updateBook: (bookId: number, bookData: Partial<Book>) => void;
      updateCover: (bookId: number) => void;
      removeBook?: (bookId: number) => void;
      addBook?: (bookId: number) => Promise<void>;
    }>();

    const removeBook = vi.fn();
    const addBook = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useLibraryBooksModule.useLibraryBooks).mockReturnValue({
      books: [],
      isLoading: false,
      error: null,
      total: 0,
      loadMore: undefined,
      hasMore: undefined,
      removeBook,
      addBook,
    });

    renderHook(() =>
      useBooksViewData({
        bookDataUpdateRef: bookDataUpdateRef as React.RefObject<{
          updateBook: (bookId: number, bookData: Partial<Book>) => void;
          updateCover: (bookId: number) => void;
          removeBook?: (bookId: number) => void;
          addBook?: (bookId: number) => Promise<void>;
        }>,
      }),
    );

    expect(bookDataUpdateRef.current).toBeDefined();
    expect(bookDataUpdateRef.current?.removeBook).toBeDefined();
    expect(bookDataUpdateRef.current?.addBook).toBeDefined();
  });

  it("should not expose removeBook and addBook when ref is not provided", () => {
    vi.mocked(useLibraryBooksModule.useLibraryBooks).mockReturnValue({
      books: [],
      isLoading: false,
      error: null,
      total: 0,
      loadMore: undefined,
      hasMore: undefined,
      removeBook: undefined,
      addBook: undefined,
    });

    const { result } = renderHook(() => useBooksViewData({}));

    // The hook returns removeBook and addBook from useLibraryBooks, not from ref
    // So they will be undefined if useLibraryBooks returns undefined
    expect(result.current.removeBook).toBeUndefined();
    expect(result.current.addBook).toBeUndefined();
  });

  it("should call removeBook from ref", () => {
    const bookDataUpdateRef = createRef<{
      updateBook: (bookId: number, bookData: Partial<Book>) => void;
      updateCover: (bookId: number) => void;
      removeBook?: (bookId: number) => void;
      addBook?: (bookId: number) => Promise<void>;
    }>();

    const removeBook = vi.fn();

    vi.mocked(useLibraryBooksModule.useLibraryBooks).mockReturnValue({
      books: [],
      isLoading: false,
      error: null,
      total: 0,
      loadMore: undefined,
      hasMore: undefined,
      removeBook,
      addBook: undefined,
    });

    renderHook(() =>
      useBooksViewData({
        bookDataUpdateRef: bookDataUpdateRef as React.RefObject<{
          updateBook: (bookId: number, bookData: Partial<Book>) => void;
          updateCover: (bookId: number) => void;
          removeBook?: (bookId: number) => void;
          addBook?: (bookId: number) => Promise<void>;
        }>,
      }),
    );

    bookDataUpdateRef.current?.removeBook?.(123);
    expect(removeBook).toHaveBeenCalledWith(123);
  });

  it("should call addBook from ref", async () => {
    const bookDataUpdateRef = createRef<{
      updateBook: (bookId: number, bookData: Partial<Book>) => void;
      updateCover: (bookId: number) => void;
      removeBook?: (bookId: number) => void;
      addBook?: (bookId: number) => Promise<void>;
    }>();

    const addBook = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useLibraryBooksModule.useLibraryBooks).mockReturnValue({
      books: [],
      isLoading: false,
      error: null,
      total: 0,
      loadMore: undefined,
      hasMore: undefined,
      removeBook: undefined,
      addBook,
    });

    renderHook(() =>
      useBooksViewData({
        bookDataUpdateRef: bookDataUpdateRef as React.RefObject<{
          updateBook: (bookId: number, bookData: Partial<Book>) => void;
          updateCover: (bookId: number) => void;
          removeBook?: (bookId: number) => void;
          addBook?: (bookId: number) => Promise<void>;
        }>,
      }),
    );

    await bookDataUpdateRef.current?.addBook?.(123);
    expect(addBook).toHaveBeenCalledWith(123);
  });

  it("should handle ref with existing methods", () => {
    const bookDataUpdateRef = createRef<{
      updateBook: (bookId: number, bookData: Partial<Book>) => void;
      updateCover: (bookId: number) => void;
      removeBook?: (bookId: number) => void;
      addBook?: (bookId: number) => Promise<void>;
    }>();

    bookDataUpdateRef.current = {
      updateBook: vi.fn(),
      updateCover: vi.fn(),
    };

    const removeBook = vi.fn();
    const addBook = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useLibraryBooksModule.useLibraryBooks).mockReturnValue({
      books: [],
      isLoading: false,
      error: null,
      total: 0,
      loadMore: undefined,
      hasMore: undefined,
      removeBook,
      addBook,
    });

    renderHook(() =>
      useBooksViewData({
        bookDataUpdateRef: bookDataUpdateRef as React.RefObject<{
          updateBook: (bookId: number, bookData: Partial<Book>) => void;
          updateCover: (bookId: number) => void;
          removeBook?: (bookId: number) => void;
          addBook?: (bookId: number) => Promise<void>;
        }>,
      }),
    );

    expect(bookDataUpdateRef.current?.updateBook).toBeDefined();
    expect(bookDataUpdateRef.current?.updateCover).toBeDefined();
    expect(bookDataUpdateRef.current?.removeBook).toBeDefined();
    expect(bookDataUpdateRef.current?.addBook).toBeDefined();
  });
});
