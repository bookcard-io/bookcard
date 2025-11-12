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

import { useCallback, useState } from "react";

export interface UseListSelectionOptions {
  /** Total number of items in the list. */
  itemCount: number;
  /** Initial selected index (default: -1). */
  initialIndex?: number;
  /** Whether selection is enabled (default: true). */
  enabled?: boolean;
}

export interface UseListSelectionResult {
  /** Currently selected index (-1 if none). */
  selectedIndex: number;
  /** Currently hovered index (-1 if none). */
  hoveredIndex: number;
  /** Set the selected index. */
  setSelectedIndex: (index: number) => void;
  /** Set the hovered index. */
  setHoveredIndex: (index: number) => void;
  /** Move selection to next item (wraps around). */
  selectNext: () => void;
  /** Move selection to previous item (wraps around). */
  selectPrevious: () => void;
  /** Reset selection to -1. */
  reset: () => void;
  /** Reset hover to -1. */
  resetHover: () => void;
  /** Reset both selection and hover. */
  resetAll: () => void;
}

/**
 * Custom hook for managing list selection state (keyboard and mouse).
 *
 * Handles both keyboard navigation (selectedIndex) and mouse hover (hoveredIndex)
 * independently. Follows SRP by focusing solely on selection state management.
 * Uses IOC by accepting configuration options.
 *
 * Parameters
 * ----------
 * options : UseListSelectionOptions
 *     Configuration including item count and initial state.
 *
 * Returns
 * -------
 * UseListSelectionResult
 *     Selection state and control functions.
 */
export function useListSelection(
  options: UseListSelectionOptions,
): UseListSelectionResult {
  const { itemCount, initialIndex = -1, enabled = true } = options;
  const [selectedIndex, setSelectedIndex] = useState<number>(initialIndex);
  const [hoveredIndex, setHoveredIndex] = useState<number>(-1);

  const selectNext = useCallback(() => {
    if (!enabled || itemCount === 0) return;
    setSelectedIndex((prev) => {
      const next = prev < 0 ? 0 : (prev + 1) % itemCount;
      return next;
    });
  }, [enabled, itemCount]);

  const selectPrevious = useCallback(() => {
    if (!enabled || itemCount === 0) return;
    setSelectedIndex((prev) => {
      if (prev < 0) return itemCount - 1;
      return prev === 0 ? itemCount - 1 : prev - 1;
    });
  }, [enabled, itemCount]);

  const reset = useCallback(() => {
    setSelectedIndex(-1);
  }, []);

  const resetHover = useCallback(() => {
    setHoveredIndex(-1);
  }, []);

  const resetAll = useCallback(() => {
    setSelectedIndex(-1);
    setHoveredIndex(-1);
  }, []);

  return {
    selectedIndex,
    hoveredIndex,
    setSelectedIndex,
    setHoveredIndex,
    selectNext,
    selectPrevious,
    reset,
    resetHover,
    resetAll,
  };
}
