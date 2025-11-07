"use client";

import styles from "./SearchWidgetBar.module.scss";
import { FiltersButton } from "./widgets/FiltersButton";
import { SearchInput } from "./widgets/SearchInput";
import { SortByDropdown } from "./widgets/SortByDropdown";
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
   * Callback fired when filters button is clicked.
   */
  onFiltersClick?: () => void;
  /**
   * Callback fired when "With selected" dropdown is clicked.
   */
  onWithSelectedClick?: () => void;
  /**
   * Callback fired when "Sort by" dropdown is clicked.
   */
  onSortByClick?: () => void;
  /**
   * Currently active view mode.
   */
  activeViewMode?: ViewMode;
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
  onFiltersClick,
  onWithSelectedClick,
  onSortByClick,
  activeViewMode = "grid",
  onViewModeChange,
}: SearchWidgetBarProps) {
  return (
    <div className={styles.widgetBar}>
      <SearchInput
        value={searchValue}
        onChange={onSearchChange}
        onSubmit={onSearchSubmit}
      />
      <FiltersButton onClick={onFiltersClick} />
      <WithSelectedDropdown onClick={onWithSelectedClick} />
      <SortByDropdown onClick={onSortByClick} />
      <ViewModeButtons
        activeMode={activeViewMode}
        onModeChange={onViewModeChange}
      />
    </div>
  );
}
