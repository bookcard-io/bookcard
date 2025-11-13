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

import { useMemo } from "react";
import type { ListColumnDefinition, ListColumnId } from "@/types/listColumns";

export interface ColumnData {
  /** Visible columns in their current order. */
  orderedVisibleColumns: ListColumnDefinition[];
  /** Non-visible columns (excluding required columns). */
  nonVisibleColumns: ListColumnDefinition[];
}

/**
 * Custom hook for transforming column data.
 *
 * Separates visible and non-visible columns, preserving order.
 * Follows SRP by handling only data transformation logic.
 * Follows DRY by centralizing column filtering logic.
 *
 * Parameters
 * ----------
 * visibleColumns : ListColumnId[]
 *     Array of visible column IDs in display order.
 * allColumns : Record<string, ListColumnDefinition>
 *     All available column definitions.
 *
 * Returns
 * -------
 * ColumnData
 *     Separated visible and non-visible columns.
 */
export function useColumnData(
  visibleColumns: ListColumnId[],
  allColumns: Record<string, ListColumnDefinition>,
): ColumnData {
  const orderedVisibleColumns = useMemo(
    () =>
      visibleColumns
        .map((id) => allColumns[id])
        .filter((col): col is ListColumnDefinition => col !== undefined),
    [visibleColumns, allColumns],
  );

  const nonVisibleColumns = useMemo(
    () =>
      Object.values(allColumns).filter(
        (col) =>
          col.id !== "title" &&
          col.id !== "authors" &&
          !visibleColumns.includes(col.id),
      ),
    [allColumns, visibleColumns],
  );

  return {
    orderedVisibleColumns,
    nonVisibleColumns,
  };
}
