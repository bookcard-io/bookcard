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

import { useEffect, useRef } from "react";
import { cn } from "@/libs/utils";

export type SortField =
  | "title"
  | "author_sort"
  | "timestamp"
  | "pubdate"
  | "series_index";

export interface SortOption {
  /** Display label for the sort option. */
  label: string;
  /** Backend field name. */
  value: SortField;
}

export const SORT_OPTIONS: SortOption[] = [
  { label: "Title", value: "title" },
  { label: "Author", value: "author_sort" },
  { label: "Added date", value: "timestamp" },
  { label: "Modified date", value: "pubdate" },
  { label: "Size", value: "series_index" },
];

export interface SortPanelProps {
  /**
   * Currently selected sort field.
   */
  sortBy?: SortField;
  /**
   * Callback fired when a sort option is selected.
   */
  onSortByChange?: (sortBy: SortField) => void;
  /**
   * Callback fired when the panel should be closed.
   */
  onClose?: () => void;
}

/**
 * Sort panel component for selecting sort criteria.
 *
 * Displays a dropdown menu with sort options (Title, Author, Added date, etc.).
 * Follows SRP by handling only sort selection UI.
 */
export function SortPanel({
  sortBy = "timestamp",
  onSortByChange,
  onClose,
}: SortPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close panel
  // Exclude clicks on the SortByDropdown button
  useEffect(() => {
    if (!onClose) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      // Don't close if clicking on the SortByDropdown button or its children
      const isSortButton = target.closest("[data-sort-button]");
      if (isSortButton) {
        return;
      }

      // Don't close if clicking inside the panel
      if (panelRef.current?.contains(target)) {
        return;
      }

      // Close if clicking outside
      onClose();
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  const handleOptionClick = (option: SortOption) => {
    onSortByChange?.(option.value);
    onClose?.();
  };

  return (
    <div
      className="panel-tonal absolute top-[calc(100%+8px)] left-0 z-[100] flex min-w-[200px] flex-col rounded-md p-1 shadow-[0_4px_12px_rgba(0,0,0,0.15)]"
      ref={panelRef}
    >
      {SORT_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          className={cn(
            "menu-item-tonal cursor-pointer rounded-md border-none bg-transparent px-4 py-2.5 text-left font-inherit text-sm",
            sortBy === option.value &&
              "bg-primary-a20 font-medium text-text-a0",
          )}
          onClick={() => handleOptionClick(option)}
          aria-label={`Sort by ${option.label}`}
          aria-pressed={sortBy === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
