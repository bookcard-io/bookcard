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
import type { Shelf } from "@/types/shelf";

export interface UseShelfSelectionOptions {
  /** Callback to notify parent of selection changes. */
  onSelectionChange?: (selectedIds: Set<number>) => void;
}

export interface UseShelfSelectionResult {
  /** Set of selected shelf IDs. */
  selectedShelfIds: Set<number>;
  /** Check if a shelf is selected. */
  isShelfSelected: (shelfId: number) => boolean;
  /** Handle shelf selection toggle. */
  handleShelfSelect: (
    shelf: Shelf,
    _allShelves: Shelf[],
    event: React.MouseEvent,
  ) => void;
  /** Remove shelves from selection (e.g., after deletion). */
  removeFromSelection: (shelfIds: number[]) => void;
  /** Clear all selections. */
  clearSelection: () => void;
}

/**
 * Custom hook for shelf selection state management.
 *
 * Manages selection state with deferred parent notification to avoid
 * setState during render. Follows SRP by handling only selection concerns.
 * Follows IOC by accepting callback for selection changes.
 *
 * Parameters
 * ----------
 * options : UseShelfSelectionOptions
 *     Configuration options for selection management.
 *
 * Returns
 * -------
 * UseShelfSelectionResult
 *     Object containing selection state and handlers.
 */
export function useShelfSelection(
  options: UseShelfSelectionOptions = {},
): UseShelfSelectionResult {
  const { onSelectionChange } = options;
  const [selectedShelfIds, setSelectedShelfIds] = useState<Set<number>>(
    new Set(),
  );

  // Store callback in ref to avoid dependency issues and prevent calling during render
  const onSelectionChangeRef = useRef(onSelectionChange);
  useEffect(() => {
    onSelectionChangeRef.current = onSelectionChange;
  }, [onSelectionChange]);

  // Notify parent of selection changes (deferred to avoid setState during render)
  useEffect(() => {
    onSelectionChangeRef.current?.(selectedShelfIds);
  }, [selectedShelfIds]);

  const handleShelfSelect = useCallback(
    (shelf: Shelf, _allShelves: Shelf[], event: React.MouseEvent) => {
      if (event?.stopPropagation) {
        event.stopPropagation();
      }
      setSelectedShelfIds((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(shelf.id)) {
          newSet.delete(shelf.id);
        } else {
          newSet.add(shelf.id);
        }
        // Don't call onSelectionChange here - let useEffect handle it
        return newSet;
      });
    },
    [],
  );

  const removeFromSelection = useCallback((shelfIds: number[]) => {
    setSelectedShelfIds((prev) => {
      const newSet = new Set(prev);
      for (const id of shelfIds) {
        newSet.delete(id);
      }
      // Don't call onSelectionChange here - let useEffect handle it
      return newSet;
    });
  }, []);

  const isShelfSelected = useCallback(
    (shelfId: number) => selectedShelfIds.has(shelfId),
    [selectedShelfIds],
  );

  const clearSelection = useCallback(() => {
    setSelectedShelfIds(new Set());
  }, []);

  return {
    selectedShelfIds,
    isShelfSelected,
    handleShelfSelect,
    removeFromSelection,
    clearSelection,
  };
}
