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

import { useEffect, useMemo, useRef, useState } from "react";
import { useUser } from "@/contexts/UserContext";
import {
  DEFAULT_VISIBLE_COLUMNS,
  LIST_COLUMN_DEFINITIONS,
  type ListColumnId,
} from "@/types/listColumns";

const SETTING_KEY = "list_view_visible_columns";

/**
 * Parse visible columns from setting value.
 *
 * Parameters
 * ----------
 * settingValue : string | null
 *     Setting value (JSON array string or null).
 *
 * Returns
 * -------
 * Set<ListColumnId>
 *     Set of visible column IDs.
 */
function parseVisibleColumns(settingValue: string | null): ListColumnId[] {
  if (!settingValue) {
    return DEFAULT_VISIBLE_COLUMNS;
  }
  try {
    const parsed = JSON.parse(settingValue) as ListColumnId[];
    if (Array.isArray(parsed)) {
      // Validate that all IDs are valid column IDs
      const validColumns = parsed.filter((id) =>
        Object.keys(LIST_COLUMN_DEFINITIONS).includes(id),
      );
      // Ensure title and authors are always included and at the start
      const requiredColumns: ListColumnId[] = ["title", "authors"];
      // Preserve order: put required columns first, then others in their saved order
      const requiredInOrder = requiredColumns.filter((id) =>
        validColumns.includes(id),
      );
      const othersInOrder = validColumns.filter(
        (id) => !requiredColumns.includes(id),
      );
      const allColumns = [...requiredInOrder, ...othersInOrder];
      // If required columns are missing, add them at the start
      for (const requiredId of requiredColumns) {
        if (!allColumns.includes(requiredId)) {
          allColumns.unshift(requiredId);
        }
      }
      return allColumns.length > 0 ? allColumns : DEFAULT_VISIBLE_COLUMNS;
    }
  } catch {
    // Invalid JSON, use default
  }
  return DEFAULT_VISIBLE_COLUMNS;
}

export interface UseListColumnsResult {
  /** Currently visible column IDs. */
  visibleColumns: ListColumnId[];
  /** All available column definitions. */
  allColumns: typeof LIST_COLUMN_DEFINITIONS;
  /** Toggle column visibility. */
  toggleColumn: (columnId: ListColumnId) => void;
  /** Reorder columns by moving from one index to another. */
  reorderColumns: (fromIndex: number, toIndex: number) => void;
  /** Whether settings are loading. */
  isLoading: boolean;
}

/**
 * Custom hook for managing list view column visibility.
 *
 * Handles loading, parsing, and persisting visible column preferences.
 * Follows SRP by focusing solely on column visibility state management.
 * Follows IOC by using UserContext for persistence.
 * Follows DRY by centralizing column visibility logic.
 *
 * Returns
 * -------
 * UseListColumnsResult
 *     Visible columns state, all column definitions, toggle function, and loading status.
 */
export function useListColumns(): UseListColumnsResult {
  const { getSetting, updateSetting, isLoading: isSettingsLoading } = useUser();

  // Parse visible columns from setting
  const visibleColumnsFromSetting = useMemo(() => {
    if (isSettingsLoading) {
      return DEFAULT_VISIBLE_COLUMNS;
    }
    const settingValue = getSetting(SETTING_KEY);
    return parseVisibleColumns(settingValue);
  }, [getSetting, isSettingsLoading]);

  // Track visible columns state
  const [visibleColumns, setVisibleColumns] = useState<ListColumnId[]>(
    visibleColumnsFromSetting,
  );

  // Track if we're in initial load/sync phase to avoid saving during that time
  const isInitialLoadRef = useRef(true);
  const previousValueRef = useRef<ListColumnId[]>(visibleColumnsFromSetting);

  // Sync with setting when it loads or changes
  useEffect(() => {
    if (!isSettingsLoading) {
      setVisibleColumns(visibleColumnsFromSetting);
      previousValueRef.current = visibleColumnsFromSetting;
      // Mark initial load as complete after settings are loaded
      setTimeout(() => {
        isInitialLoadRef.current = false;
      }, 0);
    }
  }, [visibleColumnsFromSetting, isSettingsLoading]);

  // Save changes when visibleColumns changes (but not during initial load)
  useEffect(() => {
    if (isInitialLoadRef.current || isSettingsLoading) {
      return;
    }

    // Only save if value actually changed (preserve order in comparison)
    const currentJson = JSON.stringify(visibleColumns);
    const previousJson = JSON.stringify(previousValueRef.current);
    if (currentJson !== previousJson) {
      updateSetting(SETTING_KEY, JSON.stringify(visibleColumns));
      previousValueRef.current = [...visibleColumns];
    }
  }, [visibleColumns, updateSetting, isSettingsLoading]);

  // Toggle column visibility
  const toggleColumn = (columnId: ListColumnId) => {
    setVisibleColumns((prev) => {
      // Don't allow toggling title or authors (always visible)
      if (columnId === "title" || columnId === "authors") {
        return prev;
      }

      let next: ListColumnId[];
      if (prev.includes(columnId)) {
        // Don't allow removing all columns
        if (prev.length === 1) {
          return prev;
        }
        next = prev.filter((id) => id !== columnId);
      } else {
        next = [...prev, columnId];
      }

      return next;
    });
  };

  // Reorder columns by moving from one index to another
  const reorderColumns = (fromIndex: number, toIndex: number) => {
    setVisibleColumns((prev) => {
      // Validate indices
      if (
        fromIndex < 0 ||
        fromIndex >= prev.length ||
        toIndex < 0 ||
        toIndex >= prev.length ||
        fromIndex === toIndex
      ) {
        return prev;
      }

      const newColumns = [...prev];
      const [movedColumn] = newColumns.splice(fromIndex, 1);
      if (movedColumn !== undefined) {
        newColumns.splice(toIndex, 0, movedColumn);
      }

      return newColumns;
    });
  };

  return {
    visibleColumns,
    allColumns: LIST_COLUMN_DEFINITIONS,
    toggleColumn,
    reorderColumns,
    isLoading: isSettingsLoading,
  };
}
