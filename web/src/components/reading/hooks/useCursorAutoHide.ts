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

import { useCallback, useEffect, useRef, useState } from "react";

export interface UseCursorAutoHideOptions {
  /**
   * Idle timeout in milliseconds before hiding the cursor.
   *
   * Notes
   * -----
   * Defaults to 2000ms (2 seconds).
   */
  idleTimeout?: number;
  /**
   * Interval in milliseconds for checking idle time.
   *
   * Notes
   * -----
   * Defaults to 300ms. Lower values provide more responsive hiding
   * but consume more resources.
   */
  checkInterval?: number;
  /**
   * Whether cursor auto-hide is enabled.
   *
   * Notes
   * -----
   * Defaults to true. Set to false to disable auto-hide functionality.
   */
  enabled?: boolean;
}

export interface UseCursorAutoHideResult {
  /**
   * Whether the cursor is currently visible.
   */
  cursorVisible: boolean;
  /**
   * Event handler for user activity detection.
   *
   * Notes
   * -----
   * Should be attached to mouse, touch, keyboard, and wheel events.
   * Handles all user interaction types to show cursor on activity.
   */
  handleUserActivity: () => void;
  /**
   * CSS class name to apply when cursor should be hidden.
   *
   * Notes
   * -----
   * Returns "cursor-none" when cursor should be hidden, empty string otherwise.
   * Can be used directly in className prop.
   */
  cursorClassName: string;
}

/**
 * Hook for managing cursor auto-hide functionality.
 *
 * Automatically hides the cursor after a period of inactivity and shows it
 * again when user activity is detected. Follows SRP by focusing solely on
 * cursor visibility state management.
 *
 * Parameters
 * ----------
 * options : UseCursorAutoHideOptions, optional
 *     Configuration options including idle timeout and check interval.
 *
 * Returns
 * -------
 * UseCursorAutoHideResult
 *     Cursor visibility state, activity handler, and CSS class name.
 *
 * Examples
 * --------
 * Basic usage:
 * ```tsx
 * const { cursorVisible, handleUserActivity, cursorClassName } = useCursorAutoHide();
 *
 * return (
 *   <div
 *     className={cn("container", cursorClassName)}
 *     onMouseMove={handleUserActivity}
 *     onTouchStart={handleUserActivity}
 *     onKeyDown={handleUserActivity}
 *     onWheel={handleUserActivity}
 *   >
 *     {children}
 *   </div>
 * );
 * ```
 *
 * Custom configuration:
 * ```tsx
 * const { cursorClassName, handleUserActivity } = useCursorAutoHide({
 *   idleTimeout: 3000, // 3 seconds
 *   checkInterval: 500, // Check every 500ms
 * });
 * ```
 */
export function useCursorAutoHide({
  idleTimeout = 2000,
  checkInterval = 300,
  enabled = true,
}: UseCursorAutoHideOptions = {}): UseCursorAutoHideResult {
  const [cursorVisible, setCursorVisible] = useState(true);
  const lastActivityRef = useRef<number>(Date.now());

  const handleUserActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
    setCursorVisible((prev) => {
      if (!prev) return true;
      return prev;
    });
  }, []);

  useEffect(() => {
    if (!enabled) {
      setCursorVisible(true);
      return;
    }

    if (!cursorVisible) return;

    const interval = setInterval(() => {
      const idleMs = Date.now() - lastActivityRef.current;
      if (idleMs >= idleTimeout) {
        setCursorVisible(false);
      }
    }, checkInterval);
    return () => clearInterval(interval);
  }, [cursorVisible, enabled, idleTimeout, checkInterval]);

  const cursorClassName = cursorVisible ? "" : "cursor-none";

  return {
    cursorVisible,
    handleUserActivity,
    cursorClassName,
  };
}
