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

import { useCallback } from "react";
import { useKeydownListener } from "@/hooks/useKeydownListener";

export interface KeyboardNavigationOptions {
  /** Callback when Escape key is pressed. */
  onEscape?: () => void;
  /** Callback when ArrowLeft key is pressed. */
  onArrowLeft?: () => void;
  /** Callback when ArrowRight key is pressed. */
  onArrowRight?: () => void;
  /** Whether keyboard navigation is enabled. */
  enabled?: boolean;
}

/**
 * Custom hook for keyboard navigation.
 *
 * Handles keyboard events for navigation (Escape, ArrowLeft, ArrowRight).
 * Follows SRP by focusing solely on keyboard event handling.
 * Uses IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : KeyboardNavigationOptions
 *     Navigation options with callbacks.
 */
export function useKeyboardNavigation(
  options: KeyboardNavigationOptions,
): void {
  const { onEscape, onArrowLeft, onArrowRight, enabled = true } = options;

  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape" && onEscape) {
        e.preventDefault();
        onEscape();
        return;
      }
      if (e.key === "ArrowLeft" && onArrowLeft) {
        e.preventDefault();
        onArrowLeft();
        return;
      }
      if (e.key === "ArrowRight" && onArrowRight) {
        e.preventDefault();
        onArrowRight();
      }
    },
    [onEscape, onArrowLeft, onArrowRight],
  );

  useKeydownListener({
    enabled,
    defaultTarget: "document",
    onKeyDown,
  });
}
