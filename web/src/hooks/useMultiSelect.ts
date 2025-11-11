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
