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

import { useCallback, useMemo, useRef } from "react";

export interface CurrentPageTracker {
  /** Get the currently tracked page number (1-based). */
  getCurrentPage: () => number;
  /** Update the tracked page number. */
  updateCurrentPage: (page: number) => void;
  /** Create a page change handler that updates the tracker. */
  createPageChangeHandler: (
    onPageChange?: (page: number, totalPages: number, progress: number) => void,
  ) => (page: number, totalPages: number, progress: number) => void;
}

/**
 * Hook for tracking the current page number in a ref.
 *
 * Notes
 * -----
 * This hook implements SRP by isolating page tracking logic. It's useful when
 * you need synchronous access to the current page (e.g., for keyboard navigation)
 * but the page is reported asynchronously via callbacks.
 *
 * Parameters
 * ----------
 * initialPage : int, optional
 *     Initial page number to track (default: 1).
 *
 * Returns
 * -------
 * CurrentPageTracker
 *     Tracker with methods to get/update current page and create handlers.
 */
export function useCurrentPageTracker(
  initialPage: number = 1,
): CurrentPageTracker {
  const currentPageRef = useRef<number>(initialPage);

  const getCurrentPage = useCallback(() => currentPageRef.current, []);

  const updateCurrentPage = useCallback((page: number) => {
    currentPageRef.current = page;
  }, []);

  const createPageChangeHandler = useCallback(
    (
      onPageChange?: (
        page: number,
        totalPages: number,
        progress: number,
      ) => void,
    ) => {
      return (page: number, totalPages: number, progress: number) => {
        updateCurrentPage(page);
        onPageChange?.(page, totalPages, progress);
      };
    },
    [updateCurrentPage],
  );

  return useMemo(
    () => ({
      getCurrentPage,
      updateCurrentPage,
      createPageChangeHandler,
    }),
    [getCurrentPage, updateCurrentPage, createPageChangeHandler],
  );
}
