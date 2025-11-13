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

"use client";

import { cn } from "@/libs/utils";
import type { ListColumnDefinition } from "@/types/listColumns";

export interface ColumnItemProps {
  /** Column definition to display. */
  column: ListColumnDefinition;
  /** Whether the column is currently checked/visible. */
  checked: boolean;
  /** Whether the column is required (cannot be toggled or dragged). */
  isRequired: boolean;
  /** Callback when column visibility is toggled. */
  onToggle: (columnId: string) => void;
  /** Whether this item is currently being dragged. */
  isDragging?: boolean;
  /** Whether this item is currently being dragged over. */
  isDragOver?: boolean;
  /** Whether to show drop indicator before this item. */
  showBeforeIndicator?: boolean;
  /** Whether to show drop indicator after this item. */
  showAfterIndicator?: boolean;
  /** Drag event handlers (only used if draggable). */
  dragHandlers?: {
    onDragStart: () => void;
    onDragOver: (e: React.DragEvent<HTMLLabelElement>) => void;
    onDragLeave: () => void;
    onDrop: (e: React.DragEvent<HTMLLabelElement>) => void;
    onDragEnd: () => void;
  };
}

/**
 * Column item component for displaying a single column in the selector.
 *
 * Renders a checkbox and label for a column with optional drag-and-drop support.
 * Follows SRP by handling only column item rendering.
 * Follows IOC by accepting handlers via props.
 * Follows DRY by reusing the same component for draggable and non-draggable items.
 *
 * Parameters
 * ----------
 * props : ColumnItemProps
 *     Component props including column definition, state, and handlers.
 */
export function ColumnItem({
  column,
  checked,
  isRequired,
  onToggle,
  isDragging = false,
  isDragOver = false,
  showBeforeIndicator = false,
  showAfterIndicator = false,
  dragHandlers,
}: ColumnItemProps) {
  const isDraggable = !isRequired && dragHandlers !== undefined;

  return (
    <label
      draggable={isDraggable}
      onDragStart={dragHandlers?.onDragStart}
      onDragOver={dragHandlers?.onDragOver}
      onDragLeave={dragHandlers?.onDragLeave}
      onDrop={dragHandlers?.onDrop}
      onDragEnd={dragHandlers?.onDragEnd}
      className={cn(
        "flex cursor-pointer items-center gap-2 rounded py-1.5 pr-2",
        "menu-item-tonal transition-colors duration-150",
        isDragging && "opacity-50",
        isDragOver && "bg-surface-a20",
        showBeforeIndicator && "border-primary-a0 border-t-2",
        showAfterIndicator && "border-primary-a0 border-b-2",
        isDraggable && "cursor-grab active:cursor-grabbing",
      )}
    >
      {isDraggable && (
        <i className="pi pi-bars text-text-a40 text-xs" aria-hidden="true" />
      )}
      <input
        type="checkbox"
        checked={checked}
        onChange={() => onToggle(column.id)}
        disabled={isRequired}
        className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 focus:ring-2 focus:ring-primary-a0 disabled:cursor-not-allowed disabled:opacity-50"
      />
      <span className="flex-1 text-sm text-text-a0">{column.label}</span>
    </label>
  );
}
