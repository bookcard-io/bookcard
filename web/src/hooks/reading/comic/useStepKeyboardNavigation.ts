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

import { useCallback, useMemo } from "react";
import { useKeydownListener } from "@/hooks/useKeydownListener";
import type { ComicReadingDirection } from "@/types/comicReader";
import type {
  KeydownEventTarget,
  PagedNavigationAction,
} from "@/types/pagedNavigation";
import { isEditableEventTarget } from "@/utils/domEvents";
import { getPagedNavigationStrategy } from "@/utils/pagedNavigation";

export interface StepKeyboardNavigationOptions {
  /** Reading direction to map keys for. */
  readingDirection: ComicReadingDirection;
  /** Total number of pages (1-based). */
  totalPages: number;
  /** Get the currently visible page number (1-based). */
  getCurrentPage: () => number;
  /** Navigate to a specific page (1-based). */
  onGoToPage: (page: number) => void;
  /** Whether to listen for keyboard events (default: true). */
  enabled?: boolean;
  /** Optional keydown event target (default: window when available). */
  target?: KeydownEventTarget | null;
}

function isPageJumpAction(
  action: PagedNavigationAction,
): action is Extract<PagedNavigationAction, "first" | "last"> {
  return action === "first" || action === "last";
}

/**
 * Hook for step-based keyboard navigation.
 *
 * Notes
 * -----
 * This hook converts mapped navigation actions (via `pagedNavigation` strategy)
 * into page-step transitions using `getCurrentPage`.
 *
 * Parameters
 * ----------
 * options : StepKeyboardNavigationOptions
 *     Keyboard navigation configuration and callbacks.
 */
export function useStepKeyboardNavigation({
  readingDirection,
  totalPages,
  getCurrentPage,
  onGoToPage,
  enabled = true,
  target,
}: StepKeyboardNavigationOptions): void {
  const strategy = useMemo(
    () => getPagedNavigationStrategy(readingDirection),
    [readingDirection],
  );

  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (isEditableEventTarget(e.target)) return;

      const action = strategy.mapKeyToAction(e.key);
      if (!action) return;

      const current = getCurrentPage();

      if (action === "next") {
        if (current >= totalPages) return;
        e.preventDefault();
        onGoToPage(current + 1);
        return;
      }

      if (action === "previous") {
        if (current <= 1) return;
        e.preventDefault();
        onGoToPage(current - 1);
        return;
      }

      if (isPageJumpAction(action)) {
        e.preventDefault();
        onGoToPage(action === "first" ? 1 : totalPages);
      }
    },
    [strategy, getCurrentPage, totalPages, onGoToPage],
  );

  useKeydownListener({
    enabled,
    target,
    defaultTarget: "window",
    onKeyDown,
  });
}
