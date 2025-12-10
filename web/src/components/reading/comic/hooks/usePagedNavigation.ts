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

import { useCallback, useEffect, useRef } from "react";

export type ReadingDirection = "ltr" | "rtl";

export interface NavigationCallbacks {
  canGoNext: boolean;
  canGoPrevious: boolean;
  onNext: () => void;
  onPrevious: () => void;
  onGoToPage: (page: number) => void;
}

export interface KeyboardNavigationOptions extends NavigationCallbacks {
  readingDirection: ReadingDirection;
  totalPages: number;
  /** Whether to listen for keyboard events (default: true) */
  enabled?: boolean;
}

export interface TouchGestureOptions extends NavigationCallbacks {
  readingDirection: ReadingDirection;
  /** Minimum distance in pixels to trigger a swipe (default: 50) */
  swipeThreshold?: number;
  /** Maximum time in ms for a gesture to count as a swipe (default: 300) */
  swipeTimeThreshold?: number;
}

export interface ClickZoneOptions extends NavigationCallbacks {
  containerRef: React.RefObject<HTMLElement | null>;
  readingDirection: ReadingDirection;
}

/**
 * Hook for handling keyboard navigation in paged comic view.
 *
 * Listens for arrow keys, spacebar, Home, and End for page navigation.
 * Respects reading direction (LTR/RTL) for arrow key behavior.
 *
 * Follows SRP by handling only keyboard-related navigation logic.
 *
 * Parameters
 * ----------
 * options : KeyboardNavigationOptions
 *     Navigation callbacks and configuration.
 */
export function useKeyboardNavigation({
  readingDirection,
  totalPages,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  onGoToPage,
  enabled = true,
}: KeyboardNavigationOptions): void {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore when typing in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key) {
        case "ArrowRight":
        case " ": // Spacebar
          if (readingDirection === "ltr" && canGoNext) {
            e.preventDefault();
            onNext();
          } else if (readingDirection === "rtl" && canGoPrevious) {
            e.preventDefault();
            onPrevious();
          }
          break;
        case "ArrowLeft":
          if (readingDirection === "ltr" && canGoPrevious) {
            e.preventDefault();
            onPrevious();
          } else if (readingDirection === "rtl" && canGoNext) {
            e.preventDefault();
            onNext();
          }
          break;
        case "Home":
          e.preventDefault();
          onGoToPage(1);
          break;
        case "End":
          e.preventDefault();
          onGoToPage(totalPages);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [
    enabled,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    onGoToPage,
    readingDirection,
    totalPages,
  ]);
}

interface TouchState {
  x: number;
  y: number;
  time: number;
}

interface TouchHandlers {
  handleTouchStart: (e: React.TouchEvent) => void;
  handleTouchEnd: (e: React.TouchEvent) => void;
}

/**
 * Hook for handling touch gestures in paged comic view.
 *
 * Detects horizontal swipes for page navigation.
 * Respects reading direction (LTR/RTL) for swipe direction.
 *
 * Follows SRP by handling only touch-related navigation logic.
 *
 * Parameters
 * ----------
 * options : TouchGestureOptions
 *     Navigation callbacks and configuration.
 *
 * Returns
 * -------
 * TouchHandlers
 *     Event handlers to attach to the container element.
 */
export function useTouchGestures({
  readingDirection,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  swipeThreshold = 50,
  swipeTimeThreshold = 300,
}: TouchGestureOptions): TouchHandlers {
  const touchStartRef = useRef<TouchState | null>(null);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    if (!touch) return;

    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };
  }, []);

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!touchStartRef.current) return;

      const touch = e.changedTouches[0];
      if (!touch) {
        touchStartRef.current = null;
        return;
      }

      const deltaX = touch.clientX - touchStartRef.current.x;
      const deltaY = touch.clientY - touchStartRef.current.y;
      const deltaTime = Date.now() - touchStartRef.current.time;

      // Reset state
      touchStartRef.current = null;

      // Check if it's a quick enough swipe
      if (deltaTime > swipeTimeThreshold) return;

      const absDeltaX = Math.abs(deltaX);
      const absDeltaY = Math.abs(deltaY);

      // Only handle horizontal swipes (not vertical)
      if (absDeltaX <= absDeltaY || absDeltaX <= swipeThreshold) return;

      // Determine navigation based on direction
      const isSwipeRight = deltaX > 0;
      const isSwipeLeft = deltaX < 0;

      if (readingDirection === "ltr") {
        if (isSwipeRight && canGoPrevious) onPrevious();
        else if (isSwipeLeft && canGoNext) onNext();
      } else {
        // RTL: reversed
        if (isSwipeRight && canGoNext) onNext();
        else if (isSwipeLeft && canGoPrevious) onPrevious();
      }
    },
    [
      readingDirection,
      canGoNext,
      canGoPrevious,
      onNext,
      onPrevious,
      swipeThreshold,
      swipeTimeThreshold,
    ],
  );

  return { handleTouchStart, handleTouchEnd };
}

interface ClickHandler {
  handleContainerClick: (e: React.MouseEvent<HTMLElement>) => void;
}

/**
 * Hook for handling click zone navigation in paged comic view.
 *
 * Divides the container into three zones:
 * - Left third: previous page (or next in RTL)
 * - Middle third: no action
 * - Right third: next page (or previous in RTL)
 *
 * Follows SRP by handling only click-related navigation logic.
 *
 * Parameters
 * ----------
 * options : ClickZoneOptions
 *     Container reference, navigation callbacks, and reading direction.
 *
 * Returns
 * -------
 * ClickHandler
 *     Click handler to attach to the container element.
 */
export function useClickZoneNavigation({
  containerRef,
  readingDirection,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
}: ClickZoneOptions): ClickHandler {
  const handleContainerClick = useCallback(
    (e: React.MouseEvent<HTMLElement>) => {
      if (!containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const width = rect.width;

      const isLeftZone = clickX < width / 3;
      const isRightZone = clickX > (width * 2) / 3;

      if (readingDirection === "ltr") {
        if (isLeftZone && canGoPrevious) onPrevious();
        else if (isRightZone && canGoNext) onNext();
      } else {
        // RTL: reversed zones
        if (isLeftZone && canGoNext) onNext();
        else if (isRightZone && canGoPrevious) onPrevious();
      }
    },
    [
      containerRef,
      readingDirection,
      canGoNext,
      canGoPrevious,
      onNext,
      onPrevious,
    ],
  );

  return { handleContainerClick };
}

export interface PagedNavigationOptions {
  containerRef: React.RefObject<HTMLElement | null>;
  readingDirection: ReadingDirection;
  totalPages: number;
  canGoNext: boolean;
  canGoPrevious: boolean;
  onNext: () => void;
  onPrevious: () => void;
  onGoToPage: (page: number) => void;
}

export interface PagedNavigationHandlers {
  handleContainerClick: (e: React.MouseEvent<HTMLElement>) => void;
  handleTouchStart: (e: React.TouchEvent) => void;
  handleTouchEnd: (e: React.TouchEvent) => void;
}

/**
 * Combined hook for all paged navigation interactions.
 *
 * Aggregates keyboard, touch, and click zone navigation into a single hook.
 * This simplifies the PagedComicView component by centralizing navigation logic.
 *
 * Follows:
 * - SRP: Each sub-hook handles one input method
 * - DRY: Reuses individual hooks rather than duplicating logic
 * - SOC: Separates navigation concerns from rendering
 *
 * Parameters
 * ----------
 * options : PagedNavigationOptions
 *     All navigation-related props and callbacks.
 *
 * Returns
 * -------
 * PagedNavigationHandlers
 *     Event handlers to attach to the container element.
 */
export function usePagedNavigation({
  containerRef,
  readingDirection,
  totalPages,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  onGoToPage,
}: PagedNavigationOptions): PagedNavigationHandlers {
  // Keyboard navigation (global listener)
  useKeyboardNavigation({
    readingDirection,
    totalPages,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    onGoToPage,
  });

  // Touch gestures
  const { handleTouchStart, handleTouchEnd } = useTouchGestures({
    readingDirection,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    onGoToPage,
  });

  // Click zones
  const { handleContainerClick } = useClickZoneNavigation({
    containerRef,
    readingDirection,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    onGoToPage,
  });

  return {
    handleContainerClick,
    handleTouchStart,
    handleTouchEnd,
  };
}
