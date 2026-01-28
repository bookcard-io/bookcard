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
  detectWheelEdgeNavigationAction,
  getPagedNavigationStrategy,
} from "@/utils/pagedNavigation";

/**
 * Trackpad (wheel) navigation tuning.
 *
 * Notes
 * -----
 * These are intentionally module-level "magic numbers" so you can easily
 * tinker without plumbing settings through the entire hook stack.
 */
export const PAGED_WHEEL_THRESHOLD_PX = 12;
export const PAGED_WHEEL_EDGE_TOLERANCE_PX = 2;
export const PAGED_WHEEL_COOLDOWN_MS = 350;

export interface WheelNavigationHandlers {
  handleWheel: (e: React.WheelEvent<HTMLElement>) => void;
}

export interface PagedWheelNavigationOptions extends BasicNavigationCallbacks {
  containerRef: React.RefObject<HTMLElement | null>;
  readingDirection: ComicReadingDirection;

  /** Minimum wheel delta in pixels to consider (default: `PAGED_WHEEL_THRESHOLD_PX`). */
  wheelThresholdPx?: number;
  /** Scroll-edge tolerance in pixels (default: `PAGED_WHEEL_EDGE_TOLERANCE_PX`). */
  edgeTolerancePx?: number;
  /** Cooldown between page turns from wheel (default: `PAGED_WHEEL_COOLDOWN_MS`). */
  cooldownMs?: number;
}

function normalizeWheelDelta(
  e: Pick<WheelEvent, "deltaX" | "deltaY" | "deltaMode">,
): {
  deltaX: number;
  deltaY: number;
} {
  // DOM_DELTA_PIXEL = 0, DOM_DELTA_LINE = 1, DOM_DELTA_PAGE = 2
  if (e.deltaMode === 1) {
    return { deltaX: e.deltaX * 16, deltaY: e.deltaY * 16 };
  }
  if (e.deltaMode === 2) {
    return { deltaX: e.deltaX * 800, deltaY: e.deltaY * 800 };
  }
  return { deltaX: e.deltaX, deltaY: e.deltaY };
}

/**
 * Hook for handling trackpad/mouse wheel navigation in the paged comic view.
 *
 * Notes
 * -----
 * - Primarily targets two-finger trackpad gestures (wheel events).
 * - Uses "edge-only" navigation to avoid stealing scroll/pan when zoomed.
 *
 * Parameters
 * ----------
 * options : PagedWheelNavigationOptions
 *     Wheel navigation configuration and callbacks.
 *
 * Returns
 * -------
 * WheelNavigationHandlers
 *     Wheel handler to attach to the container element.
 */
export function usePagedWheelNavigation({
  containerRef,
  readingDirection,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  wheelThresholdPx = PAGED_WHEEL_THRESHOLD_PX,
  edgeTolerancePx = PAGED_WHEEL_EDGE_TOLERANCE_PX,
  cooldownMs = PAGED_WHEEL_COOLDOWN_MS,
}: PagedWheelNavigationOptions): WheelNavigationHandlers {
  const strategy = useMemo(
    () => getPagedNavigationStrategy(readingDirection),
    [readingDirection],
  );

  const lastNavAtRef = useRef<number>(0);
  const lastActionRef = useRef<"next" | "previous" | null>(null);

  const handleWheel = useCallback(
    (e: React.WheelEvent<HTMLElement>) => {
      // Pinch-to-zoom on trackpads often comes through as wheel+ctrlKey.
      if (e.ctrlKey) return;

      const el = containerRef.current;
      if (!el) return;

      const { deltaX, deltaY } = normalizeWheelDelta(e.nativeEvent);

      const action = detectWheelEdgeNavigationAction({
        deltaX,
        deltaY,
        thresholdPx: wheelThresholdPx,
        edgeTolerancePx,
        strategy,
        scrollLeft: el.scrollLeft,
        scrollTop: el.scrollTop,
        scrollWidth: el.scrollWidth,
        scrollHeight: el.scrollHeight,
        clientWidth: el.clientWidth,
        clientHeight: el.clientHeight,
      });

      if (!action) return;
      if (action === "next" && !canGoNext) return;
      if (action === "previous" && !canGoPrevious) return;

      const now = performance.now();
      if (
        now - lastNavAtRef.current < cooldownMs &&
        lastActionRef.current === action
      ) {
        return;
      }
      lastNavAtRef.current = now;
      lastActionRef.current = action;

      e.preventDefault();
      if (action === "next") onNext();
      else onPrevious();
    },
    [
      canGoNext,
      canGoPrevious,
      containerRef,
      cooldownMs,
      edgeTolerancePx,
      onNext,
      onPrevious,
      strategy,
      wheelThresholdPx,
    ],
  );

  return { handleWheel };
}
