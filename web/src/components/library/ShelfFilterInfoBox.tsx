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

import { useCallback, useMemo } from "react";
import { useSelectedShelf } from "@/contexts/SelectedShelfContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { cn } from "@/libs/utils";

/**
 * Info box component for displaying shelf filter status.
 *
 * Shows when books are filtered by a shelf and provides a button to clear the filter.
 * Follows SRP by focusing solely on shelf filter info display.
 * Uses IOC via context hooks.
 */
export function ShelfFilterInfoBox() {
  const { selectedShelfId, setSelectedShelfId } = useSelectedShelf();
  const { shelves } = useShelvesContext();

  // Find the shelf by ID
  const shelf = useMemo(
    () => shelves.find((s) => s.id === selectedShelfId),
    [shelves, selectedShelfId],
  );

  // Handle clear filter (must be called before early return per React hooks rules)
  const handleClearFilter = useCallback(() => {
    setSelectedShelfId(undefined);
  }, [setSelectedShelfId]);

  // Don't render if no shelf is selected
  if (!selectedShelfId || !shelf) {
    return null;
  }

  return (
    <output
      className={cn(
        "mx-8 mb-4 flex items-center justify-between gap-4 rounded-lg border border-info-a20 bg-info-a20 px-4 py-3",
        "transition-colors duration-200",
      )}
      aria-live="polite"
    >
      <div className="flex items-center gap-3">
        <i
          className="pi pi-info-circle text-info-a0 text-lg"
          aria-hidden="true"
        />
        <span className="text-sm text-white">
          Showing books from shelf: <strong>{shelf.name}</strong>
        </span>
      </div>
      <button
        type="button"
        onClick={handleClearFilter}
        className={cn(
          "flex items-center gap-2 rounded-md border border-info-a10 bg-info-a10 px-3 py-1.5 text-sm text-white",
          "transition-[background-color,border-color,color] duration-200",
          "hover:border-info-a0 hover:bg-info-a0 hover:text-white",
          "focus-visible:outline-2 focus-visible:outline-info-a0 focus-visible:outline-offset-2",
          "focus:not-focus-visible:outline-none focus:outline-none",
        )}
        aria-label="Clear shelf filter"
      >
        <i className="pi pi-times text-white" aria-hidden="true" />
        <span>Clear filter</span>
      </button>
    </output>
  );
}
