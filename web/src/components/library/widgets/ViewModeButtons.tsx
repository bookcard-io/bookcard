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

import { ViewModeButton } from "./ViewModeButton";

export type ViewMode = "sort" | "grid" | "list";

export interface ViewModeButtonsProps {
  /**
   * Currently active view mode.
   */
  activeMode?: ViewMode;
  /**
   * Current sort order (used to determine sort icon).
   */
  sortOrder?: "asc" | "desc";
  /**
   * Callback fired when a view mode is selected.
   */
  onModeChange?: (mode: ViewMode) => void;
}

/**
 * Container component for view mode toggle buttons.
 *
 * Manages multiple view mode options (sort, grid, list) and their active state.
 * Follows SRP by handling only view mode selection UI.
 */
export function ViewModeButtons({
  activeMode = "grid",
  sortOrder = "desc",
  onModeChange,
}: ViewModeButtonsProps) {
  const handleModeChange = (mode: ViewMode) => {
    onModeChange?.(mode);
  };

  // Determine sort icon based on current sort order
  const sortIconClass =
    sortOrder === "asc" ? "pi-sort-amount-down-alt" : "pi-sort-amount-up";

  return (
    <fieldset
      className="m-0 flex items-center gap-1 border-none p-0"
      aria-label="View mode options"
    >
      <legend className="-m-px clip-[rect(0,0,0,0)] absolute h-px w-px overflow-hidden whitespace-nowrap border-0 p-0">
        View mode options
      </legend>
      <ViewModeButton
        iconClass={sortIconClass}
        isActive={activeMode === "sort"}
        onClick={() => handleModeChange("sort")}
        ariaLabel="Sort view"
      />
      <ViewModeButton
        iconClass="pi-th-large"
        isActive={activeMode === "grid"}
        onClick={() => handleModeChange("grid")}
        ariaLabel="Grid view"
      />
      <ViewModeButton
        iconClass="pi-list"
        isActive={activeMode === "list"}
        onClick={() => handleModeChange("list")}
        ariaLabel="List view"
      />
    </fieldset>
  );
}
