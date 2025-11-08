"use client";

import type { SearchSuggestion } from "@/types/search";
import styles from "./SearchWidgetBar.module.scss";
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
  return (
    <div className={styles.widgetBar}>
      <SearchInput
        value={searchValue}
        onChange={onSearchChange}
        onSubmit={onSearchSubmit}
        onSuggestionClick={onSuggestionClick}
      />
      <FiltersButton onClick={onFiltersClick} filters={filters} />
      <WithSelectedDropdown onClick={onWithSelectedClick} />
      <div className={styles.sortByWrapper}>
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
  );
}
