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
  BasicNavigationCallbacks,
  KeydownEventTarget,
  PageJumpCallbacks,
} from "@/types/pagedNavigation";
import {
  type ClickZoneHandlers,
  usePagedClickZoneNavigation,
} from "./usePagedClickZoneNavigation";
import { usePagedKeyboardNavigation } from "./usePagedKeyboardNavigation";
import {
  type TouchGestureHandlers,
  usePagedTouchGestures,
} from "./usePagedTouchGestures";
import {
  usePagedWheelNavigation,
  type WheelNavigationHandlers,
} from "./usePagedWheelNavigation";

export interface PagedNavigationOptions
  extends BasicNavigationCallbacks,
    PageJumpCallbacks {
  containerRef: React.RefObject<HTMLElement | null>;
  readingDirection: ComicReadingDirection;

  /** Whether keyboard navigation is enabled (default: true). */
  keyboardEnabled?: boolean;
  /** Optional keyboard target for `keydown` events. */
  keyboardTarget?: KeydownEventTarget | null;

  /** Swipe threshold in pixels (default: 50). */
  swipeThresholdPx?: number;
  /** Swipe max duration in ms (default: 300). */
  swipeMaxDurationMs?: number;
}

export interface PagedNavigationHandlers
  extends ClickZoneHandlers,
    TouchGestureHandlers,
    WheelNavigationHandlers {}

/**
 * Combined hook for all paged navigation interactions.
 *
 * Parameters
 * ----------
 * options : PagedNavigationOptions
 *     Navigation configuration and callbacks.
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
  onGoToPage,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  keyboardEnabled = true,
  keyboardTarget,
  swipeThresholdPx,
  swipeMaxDurationMs,
}: PagedNavigationOptions): PagedNavigationHandlers {
  usePagedKeyboardNavigation({
    readingDirection,
    totalPages,
    onGoToPage,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    enabled: keyboardEnabled,
    target: keyboardTarget,
  });

  const { handleTouchStart, handleTouchEnd } = usePagedTouchGestures({
    readingDirection,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    swipeThresholdPx,
    swipeMaxDurationMs,
  });

  const { handleWheel } = usePagedWheelNavigation({
    containerRef,
    readingDirection,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
  });

  const { handleContainerClick } = usePagedClickZoneNavigation({
    containerRef,
    readingDirection,
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
  });

  return {
    handleContainerClick,
    handleTouchStart,
    handleTouchEnd,
    handleWheel,
  };
}
