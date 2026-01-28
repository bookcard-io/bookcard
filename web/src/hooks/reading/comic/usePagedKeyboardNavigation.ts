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

import { useEffect, useMemo } from "react";
import type { ComicReadingDirection } from "@/types/comicReader";
import type {
  BasicNavigationCallbacks,
  KeydownEventTarget,
  PagedNavigationAction,
  PageJumpCallbacks,
} from "@/types/pagedNavigation";
import { isEditableEventTarget } from "@/utils/domEvents";
import { getPagedNavigationStrategy } from "@/utils/pagedNavigation";

export interface PagedKeyboardNavigationOptions
  extends BasicNavigationCallbacks,
    PageJumpCallbacks {
  readingDirection: ComicReadingDirection;
  /** Whether to listen for keyboard events (default: true). */
  enabled?: boolean;
  /**
   * Optional keydown event target.
   *
   * Notes
   * -----
   * If omitted, defaults to `window` when available.
   */
  target?: KeydownEventTarget | null;
}

function isPageJumpAction(
  action: PagedNavigationAction,
): action is Extract<PagedNavigationAction, "first" | "last"> {
  return action === "first" || action === "last";
}

/**
 * Hook for handling keyboard navigation in the paged comic view.
 *
 * Parameters
 * ----------
 * options : PagedKeyboardNavigationOptions
 *     Keyboard navigation configuration and callbacks.
 */
export function usePagedKeyboardNavigation({
  readingDirection,
  totalPages,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  onGoToPage,
  enabled = true,
  target,
}: PagedKeyboardNavigationOptions): void {
  const strategy = useMemo(
    () => getPagedNavigationStrategy(readingDirection),
    [readingDirection],
  );

  useEffect(() => {
    if (!enabled) return;

    const eventTarget: KeydownEventTarget | null =
      target ??
      (typeof window !== "undefined"
        ? (window as unknown as KeydownEventTarget)
        : null);
    if (!eventTarget) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (isEditableEventTarget(e.target)) return;

      const action = strategy.mapKeyToAction(e.key);
      if (!action) return;

      if (action === "next") {
        if (!canGoNext) return;
        e.preventDefault();
        onNext();
        return;
      }

      if (action === "previous") {
        if (!canGoPrevious) return;
        e.preventDefault();
        onPrevious();
        return;
      }

      if (isPageJumpAction(action)) {
        e.preventDefault();
        onGoToPage(action === "first" ? 1 : totalPages);
      }
    };

    eventTarget.addEventListener("keydown", handleKeyDown);
    return () => eventTarget.removeEventListener("keydown", handleKeyDown);
  }, [
    enabled,
    target,
    strategy,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    onGoToPage,
    totalPages,
  ]);
}
