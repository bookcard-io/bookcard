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

export interface UseMultiSelectOptions<T> {
  /**
   * Initial selected items.
   */
  initialSelected?: T[];
  /**
   * Callback fired when selection changes.
   */
  onSelectionChange?: (selected: T[]) => void;
}

export interface UseMultiSelectResult<T> {
  /**
   * Currently selected items.
   */
  selected: T[];
  /**
   * Check if an item is selected.
   */
  isSelected: (item: T) => boolean;
  /**
   * Toggle an item's selection state.
   */
  toggle: (item: T) => void;
  /**
   * Select an item.
   */
  select: (item: T) => void;
  /**
   * Deselect an item.
   */
  deselect: (item: T) => void;
  /**
   * Clear all selections.
   */
  clear: () => void;
  /**
   * Set all selections.
   */
  setSelected: (items: T[]) => void;
}

/**
 * Custom hook for managing multi-select state.
 *
 * Provides utilities for selecting/deselecting items from a list.
 * Follows SRP by handling only selection state management.
 * Follows IOC by accepting callbacks for selection changes.
 *
 * Parameters
 * ----------
 * options : UseMultiSelectOptions<T>
 *     Configuration options for multi-select behavior.
 *
 * Returns
 * -------
 * UseMultiSelectResult<T>
 *     Object containing selection state and manipulation functions.
 */
export function useMultiSelect<T>(
  options: UseMultiSelectOptions<T> = {},
): UseMultiSelectResult<T> {
  const { initialSelected = [], onSelectionChange } = options;
  const [selected, setSelected] = useState<T[]>(initialSelected);

  const isSelected = useCallback(
    (item: T) => {
      return selected.includes(item);
    },
    [selected],
  );

  const toggle = useCallback(
    (item: T) => {
      setSelected((prev) => {
        const newSelected = prev.includes(item)
          ? prev.filter((i) => i !== item)
          : [...prev, item];
        onSelectionChange?.(newSelected);
        return newSelected;
      });
    },
    [onSelectionChange],
  );

  const select = useCallback(
    (item: T) => {
      setSelected((prev) => {
        if (prev.includes(item)) {
          return prev;
        }
        const newSelected = [...prev, item];
        onSelectionChange?.(newSelected);
        return newSelected;
      });
    },
    [onSelectionChange],
  );

  const deselect = useCallback(
    (item: T) => {
      setSelected((prev) => {
        const newSelected = prev.filter((i) => i !== item);
        onSelectionChange?.(newSelected);
        return newSelected;
      });
    },
    [onSelectionChange],
  );

  const clear = useCallback(() => {
    setSelected([]);
    onSelectionChange?.([]);
  }, [onSelectionChange]);

  const setSelectedItems = useCallback(
    (items: T[]) => {
      setSelected(items);
      onSelectionChange?.(items);
    },
    [onSelectionChange],
  );

  return {
    selected,
    isSelected,
    toggle,
    select,
    deselect,
    clear,
    setSelected: setSelectedItems,
  };
}
