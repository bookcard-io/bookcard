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
import type { Shelf } from "@/types/shelf";

export interface UseShelfCardClickOptions {
  /** Shelf data. */
  shelf: Shelf;
  /** Callback when shelf card is clicked (to navigate to library tab and filter). */
  onShelfClick?: (shelfId: number) => void;
  /** Callback to trigger animation (for empty shelves). */
  onTriggerAnimation: () => void;
}

export interface UseShelfCardClickResult {
  /** Handle mouse click on shelf card. */
  handleClick: (e: React.MouseEvent) => void;
  /** Handle keyboard interaction on shelf card. */
  handleKeyDown: (e: React.KeyboardEvent) => void;
}

/**
 * Custom hook for shelf card click handling.
 *
 * Handles click and keyboard interactions with logic for empty vs non-empty shelves.
 * Follows SRP by handling only click interaction concerns.
 * Follows DRY by centralizing click handling logic.
 * Follows IOC by accepting callbacks for actions.
 *
 * Parameters
 * ----------
 * options : UseShelfCardClickOptions
 *     Configuration options for click handling.
 *
 * Returns
 * -------
 * UseShelfCardClickResult
 *     Object containing click and keyboard handlers.
 */
export function useShelfCardClick(
  options: UseShelfCardClickOptions,
): UseShelfCardClickResult {
  const { shelf, onShelfClick, onTriggerAnimation } = options;

  const handleShelfAction = useCallback(() => {
    if (shelf.book_count === 0) {
      // Empty shelf: trigger shake and red glow animation
      onTriggerAnimation();
    } else {
      // Shelf has books: navigate to library tab and filter
      onShelfClick?.(shelf.id);
    }
  }, [shelf.book_count, shelf.id, onShelfClick, onTriggerAnimation]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      // Don't trigger if clicking on overlay buttons (checkbox, edit, menu)
      const target = e.target as HTMLElement;
      if (
        target.closest("[data-shelf-checkbox]") ||
        target.closest("[data-shelf-edit]") ||
        target.closest("[data-shelf-menu]")
      ) {
        return;
      }

      handleShelfAction();
    },
    [handleShelfAction],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // For keyboard interactions, we don't need to check for overlay buttons
      // since keyboard focus won't be on those elements
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleShelfAction();
      }
    },
    [handleShelfAction],
  );

  return {
    handleClick,
    handleKeyDown,
  };
}
