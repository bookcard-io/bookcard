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

import { useCallback, useEffect, useRef, useState } from "react";
import {
  DEFAULT_SORT_FIELD,
  DEFAULT_SORT_ORDER,
  SORT_FIELDS,
  SORT_ORDERS,
  type SortField,
  type SortOrder,
} from "@/constants/librarySorting";
import { useUser } from "@/contexts/UserContext";

const SORT_FIELD_KEY = "default_sort_field";
const SORT_ORDER_KEY = "default_sort_order";

export interface UseLibrarySortingOptions {
  /** Callback when sort panel visibility changes (for coordinating with filters panel). */
  onSortPanelChange?: (isOpen: boolean) => void;
}

export interface UseLibrarySortingResult {
  /** Current sort field. */
  sortBy: SortField;
  /** Current sort order. */
  sortOrder: SortOrder;
  /** Whether sorting has initialized from user settings. */
  isReady: boolean;
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
 * Initializes from user settings (default_sort_field, default_sort_order).
 * Handles sort order toggle via view mode change.
 * Follows SRP by managing only sorting-related state and logic.
 * Follows IOC by accepting optional callbacks for coordination.
 * Follows SOC by using UserContext for settings persistence.
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
  const { getSetting, isLoading: isSettingsLoading } = useUser();

  // Initialize from settings using lazy initializer (only runs once)
  const [sortBy, setSortBy] = useState<SortField>(() => {
    const settingValue = getSetting(SORT_FIELD_KEY);
    if (SORT_FIELDS.includes(settingValue as SortField)) {
      return settingValue as SortField;
    }
    return DEFAULT_SORT_FIELD;
  });

  const [sortOrder, setSortOrder] = useState<SortOrder>(() => {
    const settingValue = getSetting(SORT_ORDER_KEY);
    if (SORT_ORDERS.includes(settingValue as SortOrder)) {
      return settingValue as SortOrder;
    }
    return DEFAULT_SORT_ORDER;
  });

  const [showSortPanel, setShowSortPanel] = useState(false);

  // Track last synced settings to avoid resync on unrelated settings updates
  const initialSyncedField = SORT_FIELDS.includes(
    getSetting(SORT_FIELD_KEY) as SortField,
  )
    ? (getSetting(SORT_FIELD_KEY) as SortField)
    : null;
  const initialSyncedOrder = SORT_ORDERS.includes(
    getSetting(SORT_ORDER_KEY) as SortOrder,
  )
    ? (getSetting(SORT_ORDER_KEY) as SortOrder)
    : null;
  const lastSyncedFieldRef = useRef<SortField | null>(initialSyncedField);
  const lastSyncedOrderRef = useRef<SortOrder | null>(initialSyncedOrder);

  // Sync with settings only when settings finish loading, and only if the
  // specific setting values actually changed.
  useEffect(() => {
    if (isSettingsLoading) {
      return;
    }
    const fieldValue = getSetting(SORT_FIELD_KEY);
    if (SORT_FIELDS.includes(fieldValue as SortField)) {
      if (lastSyncedFieldRef.current !== fieldValue && fieldValue !== sortBy) {
        setSortBy(fieldValue as SortField);
      }
      lastSyncedFieldRef.current = fieldValue as SortField;
    }
    const orderValue = getSetting(SORT_ORDER_KEY);
    if (SORT_ORDERS.includes(orderValue as SortOrder)) {
      if (
        lastSyncedOrderRef.current !== orderValue &&
        orderValue !== sortOrder
      ) {
        setSortOrder(orderValue as SortOrder);
      }
      lastSyncedOrderRef.current = orderValue as SortOrder;
    }
  }, [isSettingsLoading, sortBy, sortOrder, getSetting]);

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
    isReady: !isSettingsLoading,
    showSortPanel,
    handleSortByClick,
    handleSortByChange,
    handleSortToggle,
    closeSortPanel,
  };
}
