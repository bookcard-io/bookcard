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

import type { ComicReadingDirection } from "@/types/comicReader";
import type {
  PagedNavigationAction,
  PagedNavigationStrategy,
} from "@/types/pagedNavigation";

/**
 * Paged navigation core logic (framework-agnostic).
 *
 * Notes
 * -----
 * This module implements OCP via a strategy map. Hooks/components should
 * depend on this abstraction rather than re-encoding direction-specific
 * behavior inline.
 */

const CLICK_ZONE_EDGE = 1 / 3;

function createStrategy(
  readingDirection: ComicReadingDirection,
  impl: Omit<PagedNavigationStrategy, "readingDirection">,
): PagedNavigationStrategy {
  return { readingDirection, ...impl };
}

const LTR_STRATEGY = createStrategy("ltr", {
  mapKeyToAction: (key: string): PagedNavigationAction => {
    switch (key) {
      case "ArrowRight":
      case "PageDown":
      case " ":
        return "next";
      case "ArrowLeft":
      case "PageUp":
        return "previous";
      case "Home":
        return "first";
      case "End":
        return "last";
      default:
        return null;
    }
  },
  mapSwipeToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ): PagedNavigationAction => {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    if (absX <= absY || absX <= thresholdPx) return null;
    return deltaX > 0 ? "previous" : "next";
  },
  mapWheelToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ): PagedNavigationAction => {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    if (absX <= absY || absX <= thresholdPx) return null;
    return deltaX > 0 ? "next" : "previous";
  },
  mapClickToAction: (
    relativeX: number,
    _relativeY: number,
  ): PagedNavigationAction => {
    if (relativeX < CLICK_ZONE_EDGE) return "previous";
    if (relativeX > 1 - CLICK_ZONE_EDGE) return "next";
    return null;
  },
});

const RTL_STRATEGY = createStrategy("rtl", {
  mapKeyToAction: (key: string): PagedNavigationAction => {
    switch (key) {
      case "ArrowRight":
      case "PageDown":
      case " ":
        return "previous";
      case "ArrowLeft":
      case "PageUp":
        return "next";
      case "Home":
        return "first";
      case "End":
        return "last";
      default:
        return null;
    }
  },
  mapSwipeToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ): PagedNavigationAction => {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    if (absX <= absY || absX <= thresholdPx) return null;
    // reversed relative to LTR
    return deltaX > 0 ? "next" : "previous";
  },
  mapWheelToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ): PagedNavigationAction => {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    if (absX <= absY || absX <= thresholdPx) return null;
    return deltaX > 0 ? "previous" : "next";
  },
  mapClickToAction: (
    relativeX: number,
    _relativeY: number,
  ): PagedNavigationAction => {
    if (relativeX < CLICK_ZONE_EDGE) return "next";
    if (relativeX > 1 - CLICK_ZONE_EDGE) return "previous";
    return null;
  },
});

const VERTICAL_STRATEGY = createStrategy("vertical", {
  mapKeyToAction: (key: string): PagedNavigationAction => {
    switch (key) {
      case "ArrowDown":
      case "PageDown":
      case " ":
        return "next";
      case "ArrowUp":
      case "PageUp":
        return "previous";
      case "Home":
        return "first";
      case "End":
        return "last";
      default:
        // Also allow left/right to work as a fallback
        if (key === "ArrowRight") return "next";
        if (key === "ArrowLeft") return "previous";
        return null;
    }
  },
  mapSwipeToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ): PagedNavigationAction => {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    if (absY <= absX || absY <= thresholdPx) return null;
    // swipe up => next, swipe down => previous
    return deltaY < 0 ? "next" : "previous";
  },
  mapWheelToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ): PagedNavigationAction => {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);
    if (absY <= absX || absY <= thresholdPx) return null;
    return deltaY > 0 ? "next" : "previous";
  },
  mapClickToAction: (
    _relativeX: number,
    relativeY: number,
  ): PagedNavigationAction => {
    if (relativeY < CLICK_ZONE_EDGE) return "previous";
    if (relativeY > 1 - CLICK_ZONE_EDGE) return "next";
    return null;
  },
});

/**
 * Get the strategy for a given reading direction.
 *
 * Parameters
 * ----------
 * readingDirection : ComicReadingDirection
 *     The reading direction to map inputs for.
 *
 * Returns
 * -------
 * PagedNavigationStrategy
 *     Strategy implementation for the direction.
 */
export function getPagedNavigationStrategy(
  readingDirection: ComicReadingDirection,
): PagedNavigationStrategy {
  switch (readingDirection) {
    case "ltr":
      return LTR_STRATEGY;
    case "rtl":
      return RTL_STRATEGY;
    case "vertical":
      return VERTICAL_STRATEGY;
  }
}

/**
 * Detect a swipe action from a touch gesture.
 *
 * Parameters
 * ----------
 * params : object
 *     Gesture + strategy parameters.
 *
 * Returns
 * -------
 * PagedNavigationAction
 *     The action to execute, or null if it doesn't qualify as a swipe.
 */
export function detectSwipeAction(params: {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  durationMs: number;
  maxDurationMs: number;
  thresholdPx: number;
  strategy: PagedNavigationStrategy;
}): Extract<PagedNavigationAction, "next" | "previous"> | null {
  const {
    startX,
    startY,
    endX,
    endY,
    durationMs,
    maxDurationMs,
    thresholdPx,
    strategy,
  } = params;

  if (durationMs > maxDurationMs) return null;

  const deltaX = endX - startX;
  const deltaY = endY - startY;

  const action = strategy.mapSwipeToAction(deltaX, deltaY, thresholdPx);
  if (action === "next" || action === "previous") return action;
  return null;
}

function isAtStart(scrollPos: number, tolerancePx: number): boolean {
  return scrollPos <= tolerancePx;
}

function isAtEnd(
  scrollPos: number,
  scrollSize: number,
  clientSize: number,
  tolerancePx: number,
): boolean {
  return scrollPos >= scrollSize - clientSize - tolerancePx;
}

/**
 * Detect a trackpad/mouse wheel navigation action at scroll edges.
 *
 * Notes
 * -----
 * This enables two-finger trackpad gestures without stealing scroll/pan:
 * we only trigger a page change when the container is already at the
 * corresponding scroll boundary.
 */
export function detectWheelEdgeNavigationAction(params: {
  deltaX: number;
  deltaY: number;
  thresholdPx: number;
  edgeTolerancePx: number;
  strategy: PagedNavigationStrategy;
  scrollLeft: number;
  scrollTop: number;
  scrollWidth: number;
  scrollHeight: number;
  clientWidth: number;
  clientHeight: number;
}): Extract<PagedNavigationAction, "next" | "previous"> | null {
  const {
    deltaX,
    deltaY,
    thresholdPx,
    edgeTolerancePx,
    strategy,
    scrollLeft,
    scrollTop,
    scrollWidth,
    scrollHeight,
    clientWidth,
    clientHeight,
  } = params;

  const action = strategy.mapWheelToAction(deltaX, deltaY, thresholdPx);
  if (action !== "next" && action !== "previous") return null;

  const isVertical = strategy.readingDirection === "vertical";
  if (isVertical) {
    if (action === "previous" && isAtStart(scrollTop, edgeTolerancePx)) {
      return action;
    }
    if (
      action === "next" &&
      isAtEnd(scrollTop, scrollHeight, clientHeight, edgeTolerancePx)
    ) {
      return action;
    }
    return null;
  }

  if (action === "previous" && isAtStart(scrollLeft, edgeTolerancePx)) {
    return action;
  }
  if (
    action === "next" &&
    isAtEnd(scrollLeft, scrollWidth, clientWidth, edgeTolerancePx)
  ) {
    return action;
  }
  return null;
}
