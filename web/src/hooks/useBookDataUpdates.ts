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

import { useCallback, useEffect, useState } from "react";
import type { Book } from "@/types/book";
import { getCoverUrlWithCacheBuster } from "@/utils/books";

export interface UseBookDataUpdatesOptions {
  /** Ref to expose update method externally. */
  updateRef?: React.RefObject<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
  } | null>;
}

export interface UseBookDataUpdatesResult {
  /** Map of book ID to updated book data. */
  bookDataOverrides: Map<number, Partial<Book>>;
  /** Function to update book data for a specific book. */
  updateBook: (bookId: number, bookData: Partial<Book>) => void;
  /** Function to update cover URL with cache-busting for a specific book. */
  updateCover: (bookId: number) => void;
  /** Function to clear all book data overrides. */
  clearOverrides: () => void;
}

/**
 * Custom hook for managing book data updates in book lists.
 *
 * Tracks book data overrides by book ID and provides methods to update them.
 * Follows SRP by focusing solely on book data override state management.
 * Follows IOC by accepting ref for external access.
 * Follows DRY by centralizing book data update logic.
 *
 * Parameters
 * ----------
 * options : UseBookDataUpdatesOptions
 *     Configuration including optional ref for external access.
 *
 * Returns
 * -------
 * UseBookDataUpdatesResult
 *     Book data overrides map and control functions.
 */
export function useBookDataUpdates(
  options: UseBookDataUpdatesOptions = {},
): UseBookDataUpdatesResult {
  const { updateRef } = options;
  const [bookDataOverrides, setBookDataOverrides] = useState<
    Map<number, Partial<Book>>
  >(new Map());

  const updateBook = useCallback((bookId: number, bookData: Partial<Book>) => {
    setBookDataOverrides((prev) => {
      const next = new Map(prev);
      // Merge with existing override if present
      const existing = next.get(bookId);
      next.set(bookId, { ...existing, ...bookData });
      return next;
    });
  }, []);

  const updateCover = useCallback(
    (bookId: number) => {
      const newUrl = getCoverUrlWithCacheBuster(bookId);
      updateBook(bookId, { thumbnail_url: newUrl });
    },
    [updateBook],
  );

  const clearOverrides = useCallback(() => {
    setBookDataOverrides(new Map());
  }, []);

  // Expose updateBook and updateCover methods via ref
  useEffect(() => {
    if (updateRef) {
      // Preserve existing methods (removeBook, addBook) if they exist
      const existing = updateRef.current || {};
      updateRef.current = {
        ...existing,
        updateBook,
        updateCover,
      };
    }
  }, [updateRef, updateBook, updateCover]);

  return {
    bookDataOverrides,
    updateBook,
    updateCover,
    clearOverrides,
  };
}
