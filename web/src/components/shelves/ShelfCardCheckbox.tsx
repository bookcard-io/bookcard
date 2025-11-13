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
import type { Shelf } from "@/types/shelf";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface ShelfCardCheckboxProps {
  /** Shelf data. */
  shelf: Shelf;
  /** All shelves in the grid (needed for range selection). */
  allShelves: Shelf[];
  /** Whether the shelf is selected. */
  selected: boolean;
  /** Handler for shelf selection. */
  onShelfSelect: (
    shelf: Shelf,
    allShelves: Shelf[],
    event: React.MouseEvent,
  ) => void;
}

/**
 * Checkbox overlay button for shelf card selection.
 *
 * Handles shelf selection/deselection via checkbox interaction.
 * Follows SRP by focusing solely on selection UI and behavior.
 * Uses IOC via callback prop.
 * Follows DRY by reusing BookCardCheckbox styling pattern.
 */
export function ShelfCardCheckbox({
  shelf,
  allShelves,
  selected,
  onShelfSelect,
}: ShelfCardCheckboxProps) {
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    // Create a synthetic event with ctrlKey set to toggle behavior.
    const syntheticEvent = {
      ...e,
      ctrlKey: true,
      metaKey: false,
      shiftKey: false,
    } as React.MouseEvent;
    onShelfSelect(shelf, allShelves, syntheticEvent);
  };

  const handleKeyDown = createEnterSpaceHandler(() => {
    // Create a synthetic event with stopPropagation method for keyboard events
    const syntheticEvent = {
      stopPropagation: () => {},
      preventDefault: () => {},
    } as React.MouseEvent<HTMLDivElement>;
    handleClick(syntheticEvent);
  });

  return (
    /* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */
    <div
      data-shelf-checkbox
      className={cn(
        "checkbox pointer-events-auto absolute top-3 left-3 flex cursor-default items-center justify-center",
        "text-[var(--color-white)] transition-[background-color,border-color] duration-200 ease-in-out",
        "h-6 w-6 rounded border-2 bg-transparent p-0",
        "focus:shadow-focus-ring focus:outline-none",
        selected
          ? "border-primary-a0 bg-primary-a0"
          : "border-[var(--color-white)] hover:bg-[rgba(144,170,249,0.2)]",
        "[&_i]:block [&_i]:text-sm",
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={selected ? "Deselect shelf" : "Select shelf"}
      onKeyDown={handleKeyDown}
    >
      {selected && <i className="pi pi-check" aria-hidden="true" />}
    </div>
  );
}
