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

import { useEffect, useRef } from "react";

export interface UseInfiniteScrollOptions {
  /** Callback fired when the sentinel element becomes visible. */
  onLoadMore: () => void;
  /** Whether infinite scroll is enabled. */
  enabled?: boolean;
  /** Whether more data is currently being loaded. */
  isLoading?: boolean;
  /** Whether there are more pages to load. */
  hasMore?: boolean;
  /** Root margin for Intersection Observer (e.g., "100px" to trigger 100px before element is visible). */
  rootMargin?: string;
}

/**
 * Custom hook for implementing infinite scroll functionality.
 *
 * Uses Intersection Observer to detect when a sentinel element becomes visible
 * and triggers a callback to load more data. Follows SRP by handling only
 * scroll detection logic, making it reusable across different components.
 *
 * Parameters
 * ----------
 * options : UseInfiniteScrollOptions
 *     Configuration options for infinite scroll behavior.
 *
 * Returns
 * -------
 * React.RefObject<HTMLElement>
 *     Ref to attach to the sentinel element that triggers loading.
 */
export function useInfiniteScroll({
  onLoadMore,
  enabled = true,
  isLoading = false,
  hasMore = true,
  rootMargin = "100px",
}: UseInfiniteScrollOptions): React.RefObject<HTMLElement | null> {
  const sentinelRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!enabled || !hasMore || isLoading) {
      return;
    }

    const sentinel = sentinelRef.current;
    if (!sentinel) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry?.isIntersecting) {
          onLoadMore();
        }
      },
      {
        rootMargin,
      },
    );

    observer.observe(sentinel);

    return () => {
      observer.disconnect();
    };
  }, [enabled, hasMore, isLoading, onLoadMore, rootMargin]);

  return sentinelRef;
}
