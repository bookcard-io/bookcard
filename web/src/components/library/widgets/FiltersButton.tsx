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

import { countActiveFilterTypes } from "@/utils/filters";
import type { FilterValues } from "./FiltersPanel";

export interface FiltersButtonProps {
  /**
   * Callback fired when the filters button is clicked.
   */
  onClick?: () => void;
  /**
   * Current filter values for displaying active filter count.
   */
  filters?: FilterValues;
}

/**
 * Button component for opening the filters panel.
 *
 * Displays a filter icon and label for accessing filter options.
 * Shows a badge with the count of active filter types when filters are active.
 */
export function FiltersButton({ onClick, filters }: FiltersButtonProps) {
  const handleClick = () => {
    onClick?.();
  };

  const activeFilterCount = countActiveFilterTypes(filters);
  const ariaLabel =
    activeFilterCount > 0
      ? `Open filters (${activeFilterCount} active)`
      : "Open filters";

  return (
    <button
      type="button"
      className="relative flex cursor-pointer items-center gap-2 whitespace-nowrap rounded-lg border border-surface-a20 bg-surface-tonal-a10 px-4 py-2.5 font-inherit text-sm text-text-a0 transition-[background-color,border-color] duration-200 hover:border-surface-a30 hover:bg-surface-tonal-a20 active:bg-surface-tonal-a30"
      onClick={handleClick}
      aria-label={ariaLabel}
      data-filters-button
    >
      <div className="flex items-center gap-2">
        <i className="pi pi-filter" aria-hidden="true" />
        <span className="leading-none">Filters</span>
      </div>
      {activeFilterCount > 0 && (
        <span
          className="-right-1.5 -top-1.5 absolute flex h-[18px] min-w-[18px] items-center justify-center whitespace-nowrap rounded-full bg-primary-a0 px-[5px] font-semibold text-[11px] text-text-a0 leading-none"
          aria-hidden="true"
        >
          {activeFilterCount}
        </span>
      )}
    </button>
  );
}
