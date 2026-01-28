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

import { useCallback, useEffect, useMemo, useRef } from "react";

/**
 * Configuration for smooth scroll behavior restoration.
 *
 * Notes
 * -----
 * These are intentionally module-level constants so you can easily
 * adjust timing without plumbing settings through the entire hook stack.
 */
export const SMOOTH_SCROLL_RESTORE_DELAY_MS = 800;

export interface SmoothScrollBehaviorController {
  /**
   * Apply smooth scroll behavior temporarily and schedule restoration.
   *
   * Parameters
   * ----------
   * element : HTMLElement
   *     The scroll container element.
   * scrollFn : () => void
   *     Function to trigger the scroll (called after applying smooth behavior).
   */
  scrollWithSmoothBehavior: (
    element: HTMLElement,
    scrollFn: () => void,
  ) => void;
}

/**
 * Hook for managing temporary CSS scroll-behavior changes.
 *
 * Notes
 * -----
 * This hook implements SRP by isolating scroll-behavior lifecycle management.
 * It temporarily applies `scroll-behavior: smooth` to enable CSS-driven smooth
 * scrolling, then restores the original value after a delay.
 *
 * This is necessary because @tanstack/react-virtual doesn't support smooth
 * scrolling in dynamic-size mode, so we use CSS to achieve the effect.
 *
 * Parameters
 * ----------
 * restoreDelayMs : int, optional
 *     Milliseconds to wait before restoring original scroll behavior
 *     (default: SMOOTH_SCROLL_RESTORE_DELAY_MS).
 *
 * Returns
 * -------
 * SmoothScrollBehaviorController
 *     Controller with method to trigger smooth scrolling.
 */
export function useSmoothScrollBehavior(
  restoreDelayMs: number = SMOOTH_SCROLL_RESTORE_DELAY_MS,
): SmoothScrollBehaviorController {
  const restoreTimeoutRef = useRef<number | null>(null);
  const smoothScrollStateRef = useRef<{
    element: HTMLElement;
    previousBehavior: string;
  } | null>(null);

  const restoreOriginalBehavior = useCallback(() => {
    if (restoreTimeoutRef.current !== null) {
      window.clearTimeout(restoreTimeoutRef.current);
      restoreTimeoutRef.current = null;
    }
    const state = smoothScrollStateRef.current;
    if (state) {
      state.element.style.scrollBehavior = state.previousBehavior;
      smoothScrollStateRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      // Cleanup: restore original behavior
      restoreOriginalBehavior();
    };
  }, [restoreOriginalBehavior]);

  const scrollWithSmoothBehavior = useCallback(
    (element: HTMLElement, scrollFn: () => void): void => {
      // Store original behavior if not already stored
      if (!smoothScrollStateRef.current) {
        smoothScrollStateRef.current = {
          element,
          previousBehavior: element.style.scrollBehavior,
        };
      }

      // Apply smooth behavior
      element.style.scrollBehavior = "smooth";

      // Trigger the scroll
      scrollFn();

      // Clear any existing restore timeout
      if (restoreTimeoutRef.current !== null) {
        window.clearTimeout(restoreTimeoutRef.current);
      }

      // Schedule restoration after delay
      restoreTimeoutRef.current = window.setTimeout(() => {
        restoreOriginalBehavior();
      }, restoreDelayMs);
    },
    [restoreDelayMs, restoreOriginalBehavior],
  );

  return useMemo(
    () => ({ scrollWithSmoothBehavior }),
    [scrollWithSmoothBehavior],
  );
}
