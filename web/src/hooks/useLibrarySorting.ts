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
import type { SortField } from "@/components/library/widgets/SortPanel";

export interface UseLibrarySortingOptions {
  /** Callback when sort panel visibility changes (for coordinating with filters panel). */
  onSortPanelChange?: (isOpen: boolean) => void;
}

export interface UseLibrarySortingResult {
  /** Current sort field. */
  sortBy: SortField;
  /** Current sort order. */
  sortOrder: "asc" | "desc";
  /** Whether sort panel is visible. */
  showSortPanel: boolean;
  /** Handler for sort panel toggle. */
  handleSortByClick: () => void;
  /** Handler for sort field change. */
  handleSortByChange: (newSortBy: SortField) => void;
  /** Handler for sort order toggle. */
  handleSortToggle: () => void;
  /** Close sort panel programmatically. */
  closeSortPanel: () => void;
}

/**
 * Custom hook for managing library sorting state and actions.
 *
 * Manages sort field, sort order, and panel visibility.
 * Handles sort order toggle via view mode change.
 * Follows SRP by managing only sorting-related state and logic.
 * Follows IOC by accepting optional callbacks for coordination.
 *
 * Parameters
 * ----------
 * options : UseLibrarySortingOptions
 *     Optional callbacks for coordination with other concerns.
 *
 * Returns
 * -------
 * UseLibrarySortingResult
 *     Sorting state and action handlers.
 */
export function useLibrarySorting(
  options: UseLibrarySortingOptions = {},
): UseLibrarySortingResult {
  const { onSortPanelChange } = options;
  const [sortBy, setSortBy] = useState<SortField>("timestamp");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [showSortPanel, setShowSortPanel] = useState(false);

  const handleSortByClick = useCallback(() => {
    setShowSortPanel((prev) => {
      const newValue = !prev;
      onSortPanelChange?.(newValue);
      return newValue;
    });
  }, [onSortPanelChange]);

  const handleSortByChange = useCallback(
    (newSortBy: SortField) => {
      setSortBy(newSortBy);
      setShowSortPanel(false);
      onSortPanelChange?.(false);
    },
    [onSortPanelChange],
  );

  const handleSortToggle = useCallback(() => {
    // Toggle sort order
    setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
  }, []);

  const closeSortPanel = useCallback(() => {
    setShowSortPanel(false);
    onSortPanelChange?.(false);
  }, [onSortPanelChange]);

  return {
    sortBy,
    sortOrder,
    showSortPanel,
    handleSortByClick,
    handleSortByChange,
    handleSortToggle,
    closeSortPanel,
  };
}
