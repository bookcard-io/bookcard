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

export interface DropIndicator {
  /** Index of the target item. */
  index: number;
  /** Position relative to the target item. */
  position: "before" | "after";
}

export interface UseDragReorderOptions {
  /** Callback invoked when items are reordered. */
  onReorder: (fromIndex: number, toIndex: number) => void;
}

export interface UseDragReorderResult {
  /** Index of the currently dragged item, or null if not dragging. */
  draggedIndex: number | null;
  /** Index of the item being dragged over, or null if not over any item. */
  dragOverIndex: number | null;
  /** Drop indicator showing where the item will be dropped. */
  dropIndicator: DropIndicator | null;
  /** Handler for drag start event. */
  handleDragStart: (index: number) => void;
  /** Handler for drag over event. */
  handleDragOver: (e: React.DragEvent<HTMLElement>, index: number) => void;
  /** Handler for drag leave event. */
  handleDragLeave: () => void;
  /** Handler for drop event. */
  handleDrop: (e: React.DragEvent<HTMLElement>, toIndex: number) => void;
  /** Handler for drag end event. */
  handleDragEnd: () => void;
}

/**
 * Custom hook for managing drag-and-drop reordering.
 *
 * Handles drag state, drop indicator calculation, and reorder logic.
 * Follows SRP by focusing solely on drag-and-drop state management.
 * Follows IOC by accepting reorder callback via options.
 * Follows DRY by centralizing drag-and-drop logic.
 *
 * Parameters
 * ----------
 * options : UseDragReorderOptions
 *     Configuration including reorder callback.
 *
 * Returns
 * -------
 * UseDragReorderResult
 *     Drag state, drop indicator, and event handlers.
 */
export function useDragReorder({
  onReorder,
}: UseDragReorderOptions): UseDragReorderResult {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [dropIndicator, setDropIndicator] = useState<DropIndicator | null>(
    null,
  );

  const handleDragStart = useCallback((index: number) => {
    setDraggedIndex(index);
  }, []);

  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLElement>, index: number) => {
      e.preventDefault();
      if (draggedIndex !== null && draggedIndex !== index) {
        setDragOverIndex(index);
        const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
        const midpoint = rect.top + rect.height / 2;
        const position: "before" | "after" =
          e.clientY < midpoint ? "before" : "after";
        setDropIndicator({ index, position });
      }
    },
    [draggedIndex],
  );

  const handleDragLeave = useCallback(() => {
    setDragOverIndex(null);
    setDropIndicator(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLElement>, toIndex: number) => {
      e.preventDefault();
      if (draggedIndex !== null) {
        // Compute insertion index based on desired position (before/after)
        let insertionIndex = toIndex;
        if (
          dropIndicator?.index === toIndex &&
          dropIndicator.position === "after"
        ) {
          insertionIndex = toIndex + 1;
        }
        // Adjust for removal shift when dragging from above to below
        if (draggedIndex < insertionIndex) {
          insertionIndex -= 1;
        }
        if (draggedIndex !== insertionIndex) {
          onReorder(draggedIndex, insertionIndex);
        }
      }
      setDraggedIndex(null);
      setDragOverIndex(null);
      setDropIndicator(null);
    },
    [draggedIndex, dropIndicator, onReorder],
  );

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
    setDragOverIndex(null);
    setDropIndicator(null);
  }, []);

  return {
    draggedIndex,
    dragOverIndex,
    dropIndicator,
    handleDragStart,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleDragEnd,
  };
}
