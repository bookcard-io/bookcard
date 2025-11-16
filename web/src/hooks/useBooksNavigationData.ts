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

import { useEffect, useMemo, useRef } from "react";

export interface BooksNavigationData {
  /** List of book IDs for navigation. */
  bookIds: number[];
  /** Function to load more books. */
  loadMore?: () => void;
  /** Whether there are more books to load. */
  hasMore?: boolean;
  /** Whether data is currently loading. */
  isLoading: boolean;
}

export interface UseBooksNavigationDataOptions {
  /** List of book IDs. */
  bookIds: number[];
  /** Function to load more books. */
  loadMore?: () => void;
  /** Whether there are more books to load. */
  hasMore?: boolean;
  /** Whether data is currently loading. */
  isLoading: boolean;
  /** Callback to notify parent of navigation data changes. */
  onBooksDataChange?: (data: BooksNavigationData) => void;
}

/**
 * Custom hook for managing books navigation data.
 *
 * Handles notifying parent components of navigation data changes while
 * avoiding infinite loops from callback dependency changes.
 * Follows SRP by managing only navigation data concerns.
 * Follows IOC by accepting callback as dependency.
 * Follows DRY by centralizing navigation data change detection.
 *
 * Parameters
 * ----------
 * options : UseBooksNavigationDataOptions
 *     Navigation data and change callback.
 */
export function useBooksNavigationData(
  options: UseBooksNavigationDataOptions,
): void {
  const { bookIds, loadMore, hasMore, isLoading, onBooksDataChange } = options;

  // Use ref to avoid infinite loops from callback dependency changes
  const onBooksDataChangeRef = useRef(onBooksDataChange);
  useEffect(() => {
    onBooksDataChangeRef.current = onBooksDataChange;
  }, [onBooksDataChange]);

  // Memoize the data to avoid unnecessary updates
  const booksData = useMemo(
    () => ({
      bookIds,
      loadMore,
      hasMore,
      isLoading,
    }),
    [bookIds, loadMore, hasMore, isLoading],
  );

  // Store previous data to compare and only update if changed
  const prevBooksDataRef = useRef<BooksNavigationData | null>(null);
  useEffect(() => {
    const prev = prevBooksDataRef.current;
    const current = booksData;

    // Only call callback if data actually changed (or on first render)
    if (
      !prev ||
      prev.bookIds.length !== current.bookIds.length ||
      prev.bookIds.some((id, idx) => id !== current.bookIds[idx]) ||
      prev.hasMore !== current.hasMore ||
      prev.isLoading !== current.isLoading
    ) {
      prevBooksDataRef.current = current;
      if (onBooksDataChangeRef.current) {
        onBooksDataChangeRef.current(current);
      }
    }
  }, [booksData]);
}
