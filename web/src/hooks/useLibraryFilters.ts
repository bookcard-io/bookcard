import { useCallback, useState } from "react";
import type {
  FilterValues,
  SelectedFilterSuggestions,
} from "@/components/library/widgets/FiltersPanel";
import { createEmptyFilters } from "@/utils/filters";

export interface UseLibraryFiltersOptions {
  /** Callback to clear search when filters are applied. */
  onClearSearch?: () => void;
  /** Callback when filters panel visibility changes (for coordinating with sort panel). */
  onFiltersPanelChange?: (isOpen: boolean) => void;
}

export interface UseLibraryFiltersResult {
  /** Current filter values. */
  filters: FilterValues;
  /** Selected filter suggestions (for display names). */
  selectedFilterSuggestions: SelectedFilterSuggestions;
  /** Whether filters panel is visible. */
  showFiltersPanel: boolean;
  /** Handler for filters panel toggle. */
  handleFiltersClick: () => void;
  /** Handler for filters change. */
  handleFiltersChange: (newFilters: FilterValues) => void;
  /** Handler for selected suggestions change. */
  handleSuggestionsChange: (suggestions: SelectedFilterSuggestions) => void;
  /** Handler for applying filters. */
  handleApplyFilters: (appliedFilters: FilterValues) => void;
  /** Handler for clearing all filters. */
  handleClearFilters: () => void;
  /** Handler for closing filters panel. */
  handleCloseFiltersPanel: () => void;
  /** Clear all filters and suggestions. */
  clearFilters: () => void;
  /** Close filters panel programmatically. */
  closeFiltersPanel: () => void;
}

/**
 * Custom hook for managing library filter state and actions.
 *
 * Manages filter values, selected suggestions, and panel visibility.
 * Follows SRP by managing only filter-related state and logic.
 * Follows IOC by accepting optional callbacks for coordination.
 *
 * Parameters
 * ----------
 * options : UseLibraryFiltersOptions
 *     Optional callbacks for coordination with other concerns.
 *
 * Returns
 * -------
 * UseLibraryFiltersResult
 *     Filter state and action handlers.
 */
export function useLibraryFilters(
  options: UseLibraryFiltersOptions = {},
): UseLibraryFiltersResult {
  const { onClearSearch, onFiltersPanelChange } = options;
  const [filters, setFilters] = useState<FilterValues>(createEmptyFilters());
  const [selectedFilterSuggestions, setSelectedFilterSuggestions] =
    useState<SelectedFilterSuggestions>({});
  const [showFiltersPanel, setShowFiltersPanel] = useState(false);

  const handleFiltersClick = useCallback(() => {
    setShowFiltersPanel((prev) => {
      const newValue = !prev;
      onFiltersPanelChange?.(newValue);
      return newValue;
    });
  }, [onFiltersPanelChange]);

  const handleFiltersChange = useCallback((newFilters: FilterValues) => {
    setFilters(newFilters);
  }, []);

  const handleSuggestionsChange = useCallback(
    (suggestions: SelectedFilterSuggestions) => {
      setSelectedFilterSuggestions(suggestions);
    },
    [],
  );

  const handleApplyFilters = useCallback(
    (appliedFilters: FilterValues) => {
      // Clear search when filters are applied
      onClearSearch?.();
      setFilters(appliedFilters);
      setShowFiltersPanel(false);
      onFiltersPanelChange?.(false);
    },
    [onClearSearch, onFiltersPanelChange],
  );

  const handleClearFilters = useCallback(() => {
    // Clear all filters and suggestions
    setFilters(createEmptyFilters());
    setSelectedFilterSuggestions({});
  }, []);

  const handleCloseFiltersPanel = useCallback(() => {
    setShowFiltersPanel(false);
    onFiltersPanelChange?.(false);
  }, [onFiltersPanelChange]);

  const clearFilters = useCallback(() => {
    setFilters(createEmptyFilters());
    setSelectedFilterSuggestions({});
  }, []);

  const closeFiltersPanel = useCallback(() => {
    setShowFiltersPanel(false);
    onFiltersPanelChange?.(false);
  }, [onFiltersPanelChange]);

  return {
    filters,
    selectedFilterSuggestions,
    showFiltersPanel,
    handleFiltersClick,
    handleFiltersChange,
    handleSuggestionsChange,
    handleApplyFilters,
    handleClearFilters,
    handleCloseFiltersPanel,
    clearFilters,
    closeFiltersPanel,
  };
}
