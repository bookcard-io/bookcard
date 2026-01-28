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
import type { ComicReadingDirection } from "@/types/comicReader";
import type { BasicNavigationCallbacks } from "@/types/pagedNavigation";
import {
  detectSwipeAction,
  getPagedNavigationStrategy,
} from "@/utils/pagedNavigation";

interface TouchStartState {
  x: number;
  y: number;
  timeMs: number;
}

export interface TouchGestureHandlers {
  handleTouchStart: (e: React.TouchEvent) => void;
  handleTouchEnd: (e: React.TouchEvent) => void;
}

export interface PagedTouchGesturesOptions extends BasicNavigationCallbacks {
  readingDirection: ComicReadingDirection;
  /** Minimum distance in pixels to trigger a swipe (default: 50). */
  swipeThresholdPx?: number;
  /** Maximum duration in ms for a swipe (default: 300). */
  swipeMaxDurationMs?: number;
  /** Injectable time source for tests (default: Date.now). */
  now?: () => number;
}

/**
 * Hook for handling touch swipe gestures in the paged comic view.
 *
 * Parameters
 * ----------
 * options : PagedTouchGesturesOptions
 *     Touch gesture configuration and navigation callbacks.
 *
 * Returns
 * -------
 * TouchGestureHandlers
 *     React touch handlers to attach to the container element.
 */
export function usePagedTouchGestures({
  readingDirection,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  swipeThresholdPx = 50,
  swipeMaxDurationMs = 300,
  now = Date.now,
}: PagedTouchGesturesOptions): TouchGestureHandlers {
  const touchStartRef = useRef<TouchStartState | null>(null);

  const strategy = useMemo(
    () => getPagedNavigationStrategy(readingDirection),
    [readingDirection],
  );

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      const touch = e.touches[0];
      if (!touch) return;

      touchStartRef.current = {
        x: touch.clientX,
        y: touch.clientY,
        timeMs: now(),
      };
    },
    [now],
  );

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      const start = touchStartRef.current;
      if (!start) return;

      const touch = e.changedTouches[0];
      touchStartRef.current = null;
      if (!touch) return;

      const action = detectSwipeAction({
        startX: start.x,
        startY: start.y,
        endX: touch.clientX,
        endY: touch.clientY,
        durationMs: now() - start.timeMs,
        maxDurationMs: swipeMaxDurationMs,
        thresholdPx: swipeThresholdPx,
        strategy,
      });

      if (action === "next" && canGoNext) {
        onNext();
      } else if (action === "previous" && canGoPrevious) {
        onPrevious();
      }
    },
    [
      canGoNext,
      canGoPrevious,
      now,
      onNext,
      onPrevious,
      strategy,
      swipeMaxDurationMs,
      swipeThresholdPx,
    ],
  );

  return { handleTouchStart, handleTouchEnd };
}
