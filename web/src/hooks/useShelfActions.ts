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
 * Hook for shelf book management actions.
 *
 * Provides functions to add, remove, and reorder books in shelves.
 */

import { useCallback, useState } from "react";
import {
  addBookToShelf as addBookToShelfApi,
  removeBookFromShelf as removeBookFromShelfApi,
  reorderShelfBooks as reorderShelfBooksApi,
} from "@/services/shelfService";

interface UseShelfActionsReturn {
  /** Whether an action is in progress. */
  isProcessing: boolean;
  /** Error message if any. */
  error: string | null;
  /** Add a book to a shelf. */
  addBook: (
    shelfId: number,
    bookId: number,
    libraryId: number,
  ) => Promise<void>;
  /** Remove a book from a shelf. */
  removeBook: (
    shelfId: number,
    bookId: number,
    libraryId: number,
  ) => Promise<void>;
  /** Reorder books in a shelf. */
  reorderBooks: (
    shelfId: number,
    bookOrders: { book_id: number; library_id: number; order: number }[],
  ) => Promise<void>;
}

/**
 * Hook for shelf book management actions.
 *
 * Returns
 * -------
 * UseShelfActionsReturn
 *     Object with action functions and state.
 */
export function useShelfActions(): UseShelfActionsReturn {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addBook = useCallback(
    async (
      shelfId: number,
      bookId: number,
      libraryId: number,
    ): Promise<void> => {
      setIsProcessing(true);
      setError(null);
      try {
        await addBookToShelfApi(shelfId, bookId, libraryId);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to add book to shelf";
        setError(errorMessage);
        throw err;
      } finally {
        setIsProcessing(false);
      }
    },
    [],
  );

  const removeBook = useCallback(
    async (
      shelfId: number,
      bookId: number,
      libraryId: number,
    ): Promise<void> => {
      setIsProcessing(true);
      setError(null);
      try {
        await removeBookFromShelfApi(shelfId, bookId, libraryId);
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to remove book from shelf";
        setError(errorMessage);
        throw err;
      } finally {
        setIsProcessing(false);
      }
    },
    [],
  );

  const reorderBooks = useCallback(
    async (
      shelfId: number,
      bookOrders: { book_id: number; library_id: number; order: number }[],
    ): Promise<void> => {
      setIsProcessing(true);
      setError(null);
      try {
        await reorderShelfBooksApi(shelfId, bookOrders);
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to reorder books in shelf";
        setError(errorMessage);
        throw err;
      } finally {
        setIsProcessing(false);
      }
    },
    [],
  );

  return {
    isProcessing,
    error,
    addBook,
    removeBook,
    reorderBooks,
  };
}
