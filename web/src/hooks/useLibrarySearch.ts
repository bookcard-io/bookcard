import { useCallback, useState } from "react";
import type { SearchSuggestion } from "@/types/search";

export interface UseLibrarySearchOptions {
  /** Callback to clear filters when search is applied. */
  onClearFilters?: () => void;
  /** Callback when book suggestion is clicked. */
  onBookClick?: (bookId: number) => void;
}

export interface UseLibrarySearchResult {
  /** Current search input value (what user types). */
  searchInputValue: string;
  /** Current filter query (what filters books). */
  filterQuery: string;
  /** Handler for search input value changes. */
  handleSearchChange: (value: string) => void;
  /** Handler for search submission. */
  handleSearchSubmit: (value: string) => void;
  /** Handler for search suggestion clicks. */
  handleSuggestionClick: (suggestion: SearchSuggestion) => void;
  /** Clear search input and filter query. */
  clearSearch: () => void;
}

/**
 * Custom hook for managing library search state and actions.
 *
 * Separates search input value (for UI) from filter query (for filtering).
 * Handles search submission and suggestion clicks.
 * Follows SRP by managing only search-related state and logic.
 * Follows IOC by accepting optional callbacks for coordination.
 *
 * Parameters
 * ----------
 * options : UseLibrarySearchOptions
 *     Optional callbacks for coordination with other concerns.
 *
 * Returns
 * -------
 * UseLibrarySearchResult
 *     Search state and action handlers.
 */
export function useLibrarySearch(
  options: UseLibrarySearchOptions = {},
): UseLibrarySearchResult {
  const { onClearFilters, onBookClick } = options;
  const [searchInputValue, setSearchInputValue] = useState("");
  const [filterQuery, setFilterQuery] = useState("");

  const handleSearchChange = useCallback((value: string) => {
    // Update input value but don't filter - only show suggestions
    setSearchInputValue(value);
  }, []);

  const handleSearchSubmit = useCallback(
    (value: string) => {
      // When user submits search manually, filter by the submitted value
      // Clear filters when search is applied
      onClearFilters?.();
      setFilterQuery(value);
      setSearchInputValue(value);
    },
    [onClearFilters],
  );

  const handleSuggestionClick = useCallback(
    (suggestion: SearchSuggestion) => {
      // Filter books by tag, author, or series when suggestion pill is clicked
      // Clear filters when search is applied
      if (
        suggestion.type === "TAG" ||
        suggestion.type === "AUTHOR" ||
        suggestion.type === "SERIES"
      ) {
        onClearFilters?.();
        setFilterQuery(suggestion.name);
        setSearchInputValue(suggestion.name);
      } else if (suggestion.type === "BOOK") {
        // Open book view modal when book suggestion is clicked
        onBookClick?.(suggestion.id);
      }
    },
    [onClearFilters, onBookClick],
  );

  const clearSearch = useCallback(() => {
    setSearchInputValue("");
    setFilterQuery("");
  }, []);

  return {
    searchInputValue,
    filterQuery,
    handleSearchChange,
    handleSearchSubmit,
    handleSuggestionClick,
    clearSearch,
  };
}
