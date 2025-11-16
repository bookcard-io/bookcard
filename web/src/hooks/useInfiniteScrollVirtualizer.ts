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

import type { Virtualizer } from "@tanstack/react-virtual";
import { useEffect } from "react";

export interface UseInfiniteScrollVirtualizerOptions<
  TScrollElement extends Element | Window,
  TItemElement extends Element,
> {
  /** Virtualizer instance. */
  virtualizer: Virtualizer<TScrollElement, TItemElement>;
  /** Total number of items. */
  itemCount: number;
  /** Whether there are more items to load. */
  hasMore: boolean;
  /** Whether data is currently loading. */
  isLoading: boolean;
  /** Function to load more items. */
  loadMore?: () => void;
  /** Threshold: load more when within this many items of the end. */
  threshold?: number;
}

/**
 * Custom hook for infinite scroll with virtualizer.
 *
 * Automatically loads more items when scrolling near the end of the list.
 * Follows SRP by managing only infinite scroll concerns.
 * Follows IOC by accepting virtualizer and callbacks as dependencies.
 * Follows DRY by centralizing infinite scroll logic.
 *
 * Parameters
 * ----------
 * options : UseInfiniteScrollVirtualizerOptions<TScrollElement, TItemElement>
 *     Virtualizer instance, item count, and load more configuration.
 */
export function useInfiniteScrollVirtualizer<
  TScrollElement extends Element | Window,
  TItemElement extends Element,
>(
  options: UseInfiniteScrollVirtualizerOptions<TScrollElement, TItemElement>,
): void {
  const {
    virtualizer,
    itemCount,
    hasMore,
    isLoading,
    loadMore,
    threshold = 5,
  } = options;

  useEffect(() => {
    if (!hasMore || !loadMore || isLoading) {
      return;
    }

    const virtualItems = virtualizer.getVirtualItems();
    if (!virtualItems.length) {
      return;
    }

    const lastItem = virtualItems[virtualItems.length - 1];
    if (!lastItem) {
      return;
    }

    // Load more if we're within threshold items of the end
    if (lastItem.index >= itemCount - threshold) {
      loadMore();
    }
  }, [hasMore, loadMore, isLoading, virtualizer, itemCount, threshold]);
}
