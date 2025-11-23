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

import { useRef, useState } from "react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { cn } from "@/libs/utils";

export type FilterType = "all" | "unmatched";
export type ViewType = "authors" | "genres" | "series" | "publishers";
export type SortField = "name" | "rating" | "date_added" | "date_read";

export interface LibraryFilterBarProps {
  /** Total count of items to display. */
  total: number;
  /** Current number of items fetched/shown (for infinite scrolling). */
  currentCount?: number;
  /** Whether there are more items to load. */
  hasMore?: boolean;
  /** Currently selected filter type. */
  filterType?: FilterType;
  /** Currently selected view type. */
  viewType?: ViewType;
  /** Currently selected sort field. */
  sortBy?: SortField;
  /** Current sort order. */
  sortOrder?: "asc" | "desc";
  /** Callback when filter type changes. */
  onFilterTypeChange?: (filterType: FilterType) => void;
  /** Callback when view type changes. */
  onViewTypeChange?: (viewType: ViewType) => void;
  /** Callback when sort field changes. */
  onSortByChange?: (sortBy: SortField) => void;
  /** Callback when sort order changes. */
  onSortOrderChange?: (sortOrder: "asc" | "desc") => void;
}

const FILTER_OPTIONS: Array<{ label: string; value: FilterType }> = [
  { label: "All", value: "all" },
  { label: "Unmatched", value: "unmatched" },
];

const VIEW_OPTIONS: Array<{ label: string; value: ViewType }> = [
  { label: "Authors", value: "authors" },
  { label: "Genres", value: "genres" },
  { label: "Series", value: "series" },
  { label: "Publishers", value: "publishers" },
];

const SORT_OPTIONS: Array<{ label: string; value: SortField }> = [
  { label: "By Name", value: "name" },
  { label: "Rating", value: "rating" },
  { label: "Date Added", value: "date_added" },
  { label: "Date Read", value: "date_read" },
];

/**
 * Library filter and sort bar component.
 *
 * Provides filter, view, and sort dropdowns similar to Plex interface.
 * Follows SRP by handling only filter/sort UI concerns.
 */
export function LibraryFilterBar({
  total,
  filterType = "all",
  viewType = "authors",
  sortBy = "name",
  sortOrder = "asc",
  onFilterTypeChange,
  onViewTypeChange,
  onSortByChange,
}: LibraryFilterBarProps) {
  const [isFilterMenuOpen, setIsFilterMenuOpen] = useState(false);
  const [isViewMenuOpen, setIsViewMenuOpen] = useState(false);
  const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);
  const [filterCursorPosition, setFilterCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [viewCursorPosition, setViewCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [sortCursorPosition, setSortCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);

  const filterButtonRef = useRef<HTMLButtonElement>(null);
  const viewButtonRef = useRef<HTMLButtonElement>(null);
  const sortButtonRef = useRef<HTMLButtonElement>(null);

  // Calculate button label left edge position (px-2 = 8px padding)
  const getButtonLabelLeftEdge = (button: HTMLButtonElement) => {
    const rect = button.getBoundingClientRect();
    return rect.left + 8; // px-2 = 0.5rem = 8px
  };

  const handleFilterClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (filterButtonRef.current) {
      const labelLeft = getButtonLabelLeftEdge(filterButtonRef.current);
      setFilterCursorPosition({ x: labelLeft, y: e.clientY });
    }
    setIsFilterMenuOpen((prev) => !prev);
  };

  const handleViewClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (viewButtonRef.current) {
      const labelLeft = getButtonLabelLeftEdge(viewButtonRef.current);
      setViewCursorPosition({ x: labelLeft, y: e.clientY });
    }
    setIsViewMenuOpen((prev) => !prev);
  };

  const handleSortClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (sortButtonRef.current) {
      const labelLeft = getButtonLabelLeftEdge(sortButtonRef.current);
      setSortCursorPosition({ x: labelLeft, y: e.clientY });
    }
    setIsSortMenuOpen((prev) => !prev);
  };

  const handleFilterSelect = (value: FilterType) => {
    onFilterTypeChange?.(value);
    setIsFilterMenuOpen(false);
  };

  const handleViewSelect = (value: ViewType) => {
    onViewTypeChange?.(value);
    setIsViewMenuOpen(false);
  };

  const handleSortSelect = (value: SortField) => {
    onSortByChange?.(value);
    setIsSortMenuOpen(false);
  };

  const selectedFilterLabel =
    FILTER_OPTIONS.find((opt) => opt.value === filterType)?.label || "All";
  const selectedViewLabel =
    VIEW_OPTIONS.find((opt) => opt.value === viewType)?.label || "Authors";
  const selectedSortLabel =
    SORT_OPTIONS.find((opt) => opt.value === sortBy)?.label || "By Name";

  const sortIcon =
    sortOrder === "asc" ? "pi-sort-up-fill" : "pi-sort-down-fill";

  return (
    <div className="flex items-center gap-1 px-8 pb-4">
      {/* Filter dropdown: All/Unmatched */}
      <div className="relative">
        <button
          ref={filterButtonRef}
          type="button"
          onClick={handleFilterClick}
          className={cn(
            "group flex cursor-pointer items-center gap-1.5 whitespace-nowrap px-2 py-1.5 font-inherit",
            "text-text-a30 transition-colors duration-200 hover:text-text-a0",
            "border-none bg-transparent",
          )}
          aria-label="Filter options"
          aria-haspopup="true"
          aria-expanded={isFilterMenuOpen}
        >
          <span className="leading-none">{selectedFilterLabel}</span>
          <i
            className={cn(
              "h-4 w-4 shrink-0 text-text-a30 transition-[color,transform] duration-200 group-hover:text-text-a0",
              isFilterMenuOpen ? "pi pi-sort-up-fill" : "pi pi-sort-down-fill",
            )}
            aria-hidden="true"
          />
        </button>
        <DropdownMenu
          isOpen={isFilterMenuOpen}
          onClose={() => setIsFilterMenuOpen(false)}
          buttonRef={filterButtonRef}
          cursorPosition={filterCursorPosition}
          ariaLabel="Filter options"
          minWidth={160}
          alignLeftEdge
        >
          {FILTER_OPTIONS.map((option) => (
            <DropdownMenuItem
              key={option.value}
              label={option.label}
              onClick={() => handleFilterSelect(option.value)}
              rightContent={
                filterType === option.value ? (
                  <i
                    className="pi pi-check text-primary-a0"
                    aria-hidden="true"
                  />
                ) : null
              }
              justifyBetween
            />
          ))}
        </DropdownMenu>
      </div>

      {/* View dropdown: Authors/Genres/Series/Publishers */}
      <div className="relative">
        <button
          ref={viewButtonRef}
          type="button"
          onClick={handleViewClick}
          className={cn(
            "group flex cursor-pointer items-center gap-1.5 whitespace-nowrap px-2 py-1.5 font-inherit",
            "text-text-a30 transition-colors duration-200 hover:text-text-a0",
            "border-none bg-transparent",
          )}
          aria-label="View options"
          aria-haspopup="true"
          aria-expanded={isViewMenuOpen}
        >
          <span className="leading-none">{selectedViewLabel}</span>
          <i
            className={cn(
              "h-4 w-4 shrink-0 text-text-a30 transition-[color,transform] duration-200 group-hover:text-text-a0",
              isViewMenuOpen ? "pi pi-sort-up-fill" : "pi pi-sort-down-fill",
            )}
            aria-hidden="true"
          />
        </button>
        <DropdownMenu
          isOpen={isViewMenuOpen}
          onClose={() => setIsViewMenuOpen(false)}
          buttonRef={viewButtonRef}
          cursorPosition={viewCursorPosition}
          ariaLabel="View options"
          minWidth={160}
          alignLeftEdge
        >
          {VIEW_OPTIONS.map((option) => (
            <DropdownMenuItem
              key={option.value}
              label={option.label}
              onClick={() => handleViewSelect(option.value)}
              rightContent={
                viewType === option.value ? (
                  <i
                    className="pi pi-check text-primary-a0"
                    aria-hidden="true"
                  />
                ) : null
              }
              justifyBetween
            />
          ))}
        </DropdownMenu>
      </div>

      {/* Sort dropdown: By Name/Rating/Date Added/Date Read */}
      <div className="relative">
        <button
          ref={sortButtonRef}
          type="button"
          onClick={handleSortClick}
          className={cn(
            "group flex cursor-pointer items-center gap-1.5 whitespace-nowrap px-2 py-1.5 font-inherit",
            "text-text-a30 transition-colors duration-200 hover:text-text-a0",
            "border-none bg-transparent",
          )}
          aria-label="Sort options"
          aria-haspopup="true"
          aria-expanded={isSortMenuOpen}
        >
          <span className="leading-none">{selectedSortLabel}</span>
          <i
            className={cn(
              "h-4 w-4 shrink-0 text-text-a30 transition-[color,transform] duration-200 group-hover:text-text-a0",
              isSortMenuOpen ? "pi pi-sort-up-fill" : "pi pi-sort-down-fill",
            )}
            aria-hidden="true"
          />
        </button>
        <DropdownMenu
          isOpen={isSortMenuOpen}
          onClose={() => setIsSortMenuOpen(false)}
          buttonRef={sortButtonRef}
          cursorPosition={sortCursorPosition}
          ariaLabel="Sort options"
          minWidth={180}
          alignLeftEdge
        >
          {SORT_OPTIONS.map((option) => (
            <DropdownMenuItem
              key={option.value}
              label={option.label}
              onClick={() => handleSortSelect(option.value)}
              rightContent={
                sortBy === option.value ? (
                  <i
                    className={cn("pi", sortIcon, "text-primary-a0")}
                    aria-hidden="true"
                  />
                ) : null
              }
              justifyBetween
            />
          ))}
        </DropdownMenu>
      </div>

      {/* Count display - positioned right after sort button */}
      {total > 0 && (
        <div className="ml-2 rounded-md bg-surface-tonal-a10 px-2 py-1">
          <span className="text-sm text-text-a30">{total}</span>
        </div>
      )}
    </div>
  );
}
