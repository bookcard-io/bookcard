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

import { useUser } from "@/contexts/UserContext";
import { OutlineMerge } from "@/icons/OutlineMerge";

export interface AuthorSelectionBarProps {
  /** Number of selected authors. */
  selectedCount: number;
  /** Callback when merge is clicked. */
  onMerge?: () => void;
  /** Callback when delete is clicked. */
  onDelete?: () => void;
  /** Callback when deselect all is clicked. */
  onDeselectAll?: () => void;
}

/**
 * Plex-style selection bar for authors.
 *
 * Displays when authors are selected, showing actions
 * and selection count. Follows SRP by handling only selection bar UI.
 * Uses IOC via callback props.
 */
export function AuthorSelectionBar({
  selectedCount,
  onMerge,
  onDelete,
  onDeselectAll,
}: AuthorSelectionBarProps) {
  const { canPerformAction } = useUser();
  const canWrite = canPerformAction("books", "write");
  const canDelete = canPerformAction("books", "delete");

  if (selectedCount < 1) {
    return null;
  }

  return (
    <div className="-mb-14 sticky top-0 z-50 mx-8 flex h-14 items-center justify-between rounded-md border-2 border-[var(--color-primary-a0)] bg-[var(--color-surface-tonal-a10)] px-6 text-[var(--color-text-a0)] shadow-lg">
      {/* Left: Selection count */}
      <div className="flex items-center">
        <span className="font-medium text-sm">
          {selectedCount} {selectedCount === 1 ? "item" : "items"} selected
        </span>
      </div>

      {/* Center: Action buttons - perfectly centered */}
      <div className="-translate-x-1/2 -translate-y-1/2 absolute top-1/2 left-1/2 flex items-center gap-4">
        <button
          type="button"
          onClick={canWrite && selectedCount >= 2 ? onMerge : undefined}
          disabled={!canWrite || selectedCount < 2}
          className="flex items-center gap-2 rounded-md bg-transparent px-4 py-2 font-medium text-[var(--color-text-a0)] text-sm transition-colors duration-200 hover:bg-[var(--color-primary-a0)]/20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Merge authors"
        >
          <OutlineMerge className="h-5 w-5" />
          <span>Merge</span>
        </button>
        <button
          type="button"
          onClick={onDelete}
          disabled={!canDelete}
          className="flex items-center gap-2 rounded-md bg-transparent px-4 py-2 font-medium text-[var(--color-text-a0)] text-sm transition-colors duration-200 hover:bg-[var(--color-primary-a0)]/20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Delete authors"
        >
          <i className="pi pi-trash text-base" aria-hidden="true" />
          <span>Delete</span>
        </button>
      </div>

      {/* Right: Deselect all */}
      <div className="flex items-center">
        <button
          type="button"
          onClick={onDeselectAll}
          className="flex items-center gap-2 rounded-md bg-transparent px-4 py-2 font-medium text-[var(--color-text-a0)] text-sm transition-colors duration-200 hover:bg-[var(--color-primary-a0)]/20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
          aria-label="Deselect all"
        >
          <i className="pi pi-times text-base" aria-hidden="true" />
          <span>Deselect All</span>
        </button>
      </div>
    </div>
  );
}
