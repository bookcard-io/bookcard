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

/**
 * Hook for managing books in a shelf.
 *
 * Provides paginated book list for a shelf with sorting support.
 */

import { useCallback, useEffect, useState } from "react";
import { getShelfBooks } from "@/services/shelfService";

interface UseShelfBooksOptions {
  /** Shelf ID. */
  shelfId: number;
  /** Page number (1-indexed, default: 1). */
  page?: number;
  /** Number of items per page (default: 20). */
  pageSize?: number;
  /** Sort field: 'order', 'date_added', or 'book_id' (default: 'order'). */
  sortBy?: string;
  /** Sort order: 'asc' or 'desc' (default: 'asc'). */
  sortOrder?: string;
}

interface UseShelfBooksReturn {
  /** List of book IDs in the shelf. */
  bookIds: number[];
  /** Total number of books in the shelf. */
  total: number;
  /** Whether books are currently loading. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
  /** Refresh the book list. */
  refresh: () => Promise<void>;
}

/**
 * Hook for managing books in a shelf.
 *
 * Parameters
 * ----------
 * options : UseShelfBooksOptions
 *     Configuration options for the hook.
 *
 * Returns
 * -------
 * UseShelfBooksReturn
 *     Object with book IDs, loading state, and refresh function.
 */
export function useShelfBooks(
  options: UseShelfBooksOptions,
): UseShelfBooksReturn {
  const {
    shelfId,
    page = 1,
    pageSize = 20,
    sortBy = "order",
    sortOrder = "asc",
  } = options;
  const [bookIds, setBookIds] = useState<number[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadBooks = useCallback(async () => {
    if (!shelfId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const refs = await getShelfBooks(
        shelfId,
        page,
        sortBy,
        pageSize,
        sortOrder,
      );
      setBookIds(refs.map((ref) => ref.book_id));
      // Note: API doesn't return total yet, so we use the length
      // In future, we can enhance the API to return total count
      setTotal(refs.length);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load shelf books",
      );
    } finally {
      setIsLoading(false);
    }
  }, [shelfId, page, pageSize, sortBy, sortOrder]);

  useEffect(() => {
    void loadBooks();
  }, [loadBooks]);

  return {
    bookIds,
    total,
    isLoading,
    error,
    refresh: loadBooks,
  };
}
