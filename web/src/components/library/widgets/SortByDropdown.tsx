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

import type { SortField } from "@/constants/librarySorting";
import { SORT_OPTIONS } from "@/constants/librarySorting";

export interface SortByDropdownProps {
  /**
   * Currently selected sort field.
   */
  sortBy?: SortField;
  /**
   * Callback fired when the dropdown is clicked.
   */
  onClick?: () => void;
}

/**
 * Dropdown button component for sorting options.
 *
 * Provides a dropdown interface for selecting sort criteria.
 * Follows SRP by handling only UI display and click events.
 */
export function SortByDropdown({
  sortBy = "timestamp",
  onClick,
}: SortByDropdownProps) {
  const handleClick = () => {
    onClick?.();
  };

  const selectedOption = SORT_OPTIONS.find((opt) => opt.value === sortBy);
  const displayText = selectedOption?.label || "Sort by";

  return (
    <button
      type="button"
      className="btn-tonal group flex cursor-pointer items-center gap-2 whitespace-nowrap px-4 py-2.5 font-inherit"
      onClick={handleClick}
      aria-label="Sort options"
      aria-haspopup="true"
      data-sort-button
    >
      <span className="leading-none">{displayText}</span>
      <i
        className="pi pi-chevron-down h-4 w-4 shrink-0 text-text-a30 transition-[color,transform] duration-200 group-hover:text-text-a0"
        aria-hidden="true"
      />
    </button>
  );
}
