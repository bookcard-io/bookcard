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

import { useQueries, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { getRecentReads } from "@/services/readingService";
import type { Book } from "@/types/book";

export interface UseRecentlyReadBooksOptions {
  /** Maximum number of recent reads to fetch. */
  limit?: number;
  /** Whether the query is enabled. */
  enabled?: boolean;
}

export interface UseRecentlyReadBooksResult {
  /** Recently read books. */
  books: Book[];
  /** Whether books are loading. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
}

/**
 * Hook for fetching recently read books.
 *
 * Combines recent reading progress with full book details.
 * Follows SRP by managing only recently read books data.
 * Uses IOC via react-query.
 *
 * Parameters
 * ----------
 * options : UseRecentlyReadBooksOptions
 *     Configuration options.
 *
 * Returns
 * -------
 * UseRecentlyReadBooksResult
 *     Recently read books, loading state, and error.
 */
export function useRecentlyReadBooks(
  options: UseRecentlyReadBooksOptions = {},
): UseRecentlyReadBooksResult {
  const { limit = 10, enabled = true } = options;

  // Fetch recent reads
  const {
    data: recentReadsData,
    isLoading: isLoadingReads,
    error: readsError,
  } = useQuery({
    queryKey: ["recent-reads", limit],
    queryFn: () => getRecentReads(limit),
    enabled,
    staleTime: 60_000, // 1 minute
  });

  // Extract unique book IDs
  const bookIds = useMemo(() => {
    if (!recentReadsData?.reads) {
      return [];
    }
    const ids = recentReadsData.reads.map((read) => read.book_id);
    // Remove duplicates
    return Array.from(new Set(ids));
  }, [recentReadsData]);

  // Fetch full book details for each book ID using useQueries
  const bookQueries = useQueries({
    queries: bookIds.map((bookId) => ({
      queryKey: ["book", bookId, true], // full=true
      queryFn: async () => {
        const url = new URL(`/api/books/${bookId}`, window.location.origin);
        url.searchParams.set("full", "true");
        const response = await fetch(url.toString(), {
          cache: "no-store",
        });
        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(errorData.detail || "Failed to fetch book");
        }
        return (await response.json()) as Book;
      },
      enabled: enabled && bookIds.length > 0,
      staleTime: 60_000,
    })),
  });

  const isLoadingBooks = bookQueries.some((q) => q.isLoading);
  const bookErrors = bookQueries
    .map((q) => q.error)
    .filter((e): e is Error => e !== null);

  const books = useMemo(() => {
    return bookQueries
      .map((q) => q.data)
      .filter((book): book is Book => book !== null && book !== undefined);
  }, [bookQueries]);

  const isLoading = isLoadingReads || isLoadingBooks;
  const error = readsError
    ? readsError instanceof Error
      ? readsError.message
      : "Failed to load recent reads"
    : bookErrors.length > 0
      ? bookErrors[0] instanceof Error
        ? bookErrors[0].message
        : "Failed to load books"
      : null;

  return {
    books,
    isLoading,
    error,
  };
}
