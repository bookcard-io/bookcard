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

import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import type { SearchSuggestion } from "@/types/search";
import { FiltersButton } from "./widgets/FiltersButton";
import type { FilterValues } from "./widgets/FiltersPanel";
import { SearchInput } from "./widgets/SearchInput";
import { SortByDropdown } from "./widgets/SortByDropdown";
import type { SortField } from "./widgets/SortPanel";
import { SortPanel } from "./widgets/SortPanel";
import { type ViewMode, ViewModeButtons } from "./widgets/ViewModeButtons";
import { WithSelectedDropdown } from "./widgets/WithSelectedDropdown";

export interface SearchWidgetBarProps {
  /**
   * Current search value.
   */
  searchValue?: string;
  /**
   * Callback fired when search value changes.
   */
  onSearchChange?: (value: string) => void;
  /**
   * Callback fired when search is submitted.
   */
  onSearchSubmit?: (value: string) => void;
  /**
   * Callback fired when a search suggestion is clicked.
   */
  onSuggestionClick?: (suggestion: SearchSuggestion) => void;
  /**
   * Callback fired when filters button is clicked.
   */
  onFiltersClick?: () => void;
  /**
   * Current filter values for displaying active filter count.
   */
  filters?: FilterValues;
  /**
   * Callback fired when "With selected" dropdown is clicked.
   */
  onWithSelectedClick?: () => void;
  /**
   * Callback fired when "Sort by" dropdown is clicked.
   */
  onSortByClick?: () => void;
  /**
   * Currently selected sort field.
   */
  sortBy?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /**
   * Whether the sort panel is visible.
   */
  showSortPanel?: boolean;
  /**
   * Callback fired when sort field changes.
   */
  onSortByChange?: (sortBy: SortField) => void;
  /**
   * Currently active view mode.
   */
  activeViewMode?: ViewMode;
  /**
   * Current sort order (used to determine sort icon).
   */
  sortOrder?: "asc" | "desc";
  /**
   * Callback fired when view mode changes.
   */
  onViewModeChange?: (mode: ViewMode) => void;
}

/**
 * Container component for the search and filter widget bar.
 *
 * Orchestrates all search, filter, sort, and view mode widgets in a horizontal layout.
 */
export function SearchWidgetBar({
  searchValue = "",
  onSearchChange,
  onSearchSubmit,
  onSuggestionClick,
  onFiltersClick,
  filters,
  onWithSelectedClick,
  onSortByClick,
  sortBy = "timestamp",
  showSortPanel = false,
  onSortByChange,
  activeViewMode = "grid",
  sortOrder = "desc",
  onViewModeChange,
}: SearchWidgetBarProps) {
  const { selectedBookIds } = useSelectedBooks();

  return (
    <div className="flex flex-col gap-3 px-8 pb-4 md:flex-row md:items-center">
      {/* Row 1: SearchInput (full width on mobile, flex-1 on desktop) */}
      <SearchInput
        value={searchValue}
        onChange={onSearchChange}
        onSubmit={onSearchSubmit}
        onSuggestionClick={onSuggestionClick}
      />
      {/* Row 2+: Other elements wrap horizontally on mobile, stay in row on desktop */}
      <div className="flex flex-wrap items-center gap-3">
        <FiltersButton onClick={onFiltersClick} filters={filters} />
        <WithSelectedDropdown
          onClick={onWithSelectedClick}
          disabled={selectedBookIds.size === 0}
        />
        <div className="relative">
          <SortByDropdown sortBy={sortBy} onClick={onSortByClick} />
          {showSortPanel && (
            <SortPanel
              sortBy={sortBy}
              onSortByChange={onSortByChange}
              onClose={onSortByClick}
            />
          )}
        </div>
        <ViewModeButtons
          activeMode={activeViewMode}
          sortOrder={sortOrder}
          onModeChange={onViewModeChange}
        />
      </div>
    </div>
  );
}
