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

import { useCallback, useEffect, useRef, useState } from "react";

export interface UsePagedPageLoadingOptions {
  /**
   * A key that changes when the underlying book/source changes.
   *
   * Notes
   * -----
   * This is used to clear cached "loaded page" state so loading UI doesn't leak
   * across books or formats.
   */
  bookKey: string;
  /**
   * The pages currently visible in the viewport (e.g. [page] or [page, page+1]).
   */
  visiblePages: number[];
}

export interface UsePagedPageLoadingResult {
  isLoading: boolean;
  onPageLoad: (pageNumber: number) => void;
}

/**
 * Track which pages have loaded and expose a loading state for visible pages.
 *
 * Notes
 * -----
 * - Uses refs for the loaded-page set to avoid re-renders on every load event.
 * - Uses state only for the boolean `isLoading` flag.
 * - Clears caches only when `bookKey` changes (not on initial mount).
 *
 * Parameters
 * ----------
 * options : UsePagedPageLoadingOptions
 *     Loading tracking options.
 *
 * Returns
 * -------
 * UsePagedPageLoadingResult
 *     Loading flag and a page-load callback.
 */
export function usePagedPageLoading({
  bookKey,
  visiblePages,
}: UsePagedPageLoadingOptions): UsePagedPageLoadingResult {
  const [isLoading, setIsLoading] = useState(true);
  const loadedPagesRef = useRef<Set<number>>(new Set());
  const visiblePagesRef = useRef<number[]>(visiblePages);
  const prevBookKeyRef = useRef(bookKey);

  useEffect(() => {
    visiblePagesRef.current = visiblePages;
    const allVisibleAlreadyLoaded = visiblePages.every((p) =>
      loadedPagesRef.current.has(p),
    );
    setIsLoading(!allVisibleAlreadyLoaded);
  }, [visiblePages]);

  useEffect(() => {
    if (prevBookKeyRef.current === bookKey) {
      return;
    }
    prevBookKeyRef.current = bookKey;
    loadedPagesRef.current = new Set();
    setIsLoading(true);
  }, [bookKey]);

  const onPageLoad = useCallback((pageNumber: number) => {
    loadedPagesRef.current.add(pageNumber);

    const allLoaded = visiblePagesRef.current.every((p) =>
      loadedPagesRef.current.has(p),
    );
    if (allLoaded) {
      setIsLoading(false);
    }
  }, []);

  return { isLoading, onPageLoad };
}
