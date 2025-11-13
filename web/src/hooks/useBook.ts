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

"use client";

import { useCallback, useEffect, useState } from "react";
import type { Book, BookUpdate } from "@/types/book";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";

export interface UseBookOptions {
  /** Book ID to fetch. */
  bookId: number;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
  /** Whether to fetch full metadata (tags, identifiers, description, etc.). */
  full?: boolean;
}

export interface UseBookResult {
  /** Book data. */
  book: Book | null;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to refetch book data. */
  refetch: () => Promise<void>;
  /** Function to update book metadata. */
  updateBook: (update: BookUpdate) => Promise<Book | null>;
  /** Whether an update is in progress. */
  isUpdating: boolean;
  /** Error message if update failed. */
  updateError: string | null;
}

/**
 * Custom hook for fetching and updating a single book.
 *
 * Provides loading state, error handling, and update functionality.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * @param options - Hook options including book ID.
 * @returns Book data, loading state, and control functions.
 */
export function useBook(options: UseBookOptions): UseBookResult {
  const { bookId, enabled = true, full = false } = options;

  const [book, setBook] = useState<Book | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const fetchBook = useCallback(async () => {
    if (!enabled || !bookId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const url = new URL(`/api/books/${bookId}`, window.location.origin);
      if (full) {
        url.searchParams.set("full", "true");
      }

      const fetchKey = generateFetchKey(url.toString(), {
        method: "GET",
      });

      const result = await deduplicateFetch(fetchKey, async () => {
        const response = await fetch(url.toString(), {
          cache: "no-store",
        });
        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(errorData.detail || "Failed to fetch book");
        }
        return (await response.json()) as Book;
      });

      setBook(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setBook(null);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, bookId, full]);

  useEffect(() => {
    void fetchBook();
  }, [fetchBook]);

  const updateBook = useCallback(
    async (update: BookUpdate): Promise<Book | null> => {
      if (!bookId) {
        return null;
      }

      setIsUpdating(true);
      setUpdateError(null);

      try {
        const response = await fetch(`/api/books/${bookId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(update),
        });

        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(errorData.detail || "Failed to update book");
        }

        const updatedBook = (await response.json()) as Book;
        setBook(updatedBook);
        return updatedBook;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setUpdateError(message);
        return null;
      } finally {
        setIsUpdating(false);
      }
    },
    [bookId],
  );

  return {
    book,
    isLoading,
    error,
    refetch: fetchBook,
    updateBook,
    isUpdating,
    updateError,
  };
}
