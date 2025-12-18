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

import { createContext, type ReactNode, useCallback, useContext } from "react";
import type { useLibraryFilters } from "@/hooks/useLibraryFilters";
import type { useLibrarySearch } from "@/hooks/useLibrarySearch";
import { hasActiveFilters } from "@/utils/filters";

interface LibraryFiltersContextType {
  /** Full filters object from useLibraryFilters. */
  filters: ReturnType<typeof useLibraryFilters>;
  /** Full search object from useLibrarySearch. */
  search: ReturnType<typeof useLibrarySearch>;
  /** Current filter values. */
  filterValues: ReturnType<typeof useLibraryFilters>["filters"];
  /** Current search query. */
  searchQuery: string;
  /** Whether any filters or search are active. */
  isFiltered: boolean;
  /** Clear all filters. */
  clearFilters: () => void;
  /** Clear search query. */
  clearSearch: () => void;
  /** Clear both filters and search. */
  clearAll: () => void;
}

const LibraryFiltersContext = createContext<
  LibraryFiltersContextType | undefined
>(undefined);

interface LibraryFiltersProviderProps {
  /** Child components. */
  children: ReactNode;
  /** Filters object from useLibraryFilters. */
  filters: ReturnType<typeof useLibraryFilters>;
  /** Search object from useLibrarySearch. */
  search: ReturnType<typeof useLibrarySearch>;
}

/**
 * Provider for library filters context.
 *
 * Provides filter and search state via context to eliminate prop-drilling.
 * The actual state is managed by the parent component (via useLibraryFilters/useLibrarySearch).
 * Follows SRP by providing context only, not managing state.
 * Follows IOC by accepting filter/search objects as props.
 *
 * Parameters
 * ----------
 * props : LibraryFiltersProviderProps
 *     Provider props including children and filter/search objects.
 */
export function LibraryFiltersProvider({
  children,
  filters,
  search,
}: LibraryFiltersProviderProps) {
  // Compute isFiltered state
  const isFiltered =
    hasActiveFilters(filters.filters) ||
    (search.filterQuery?.trim() ?? "") !== "";

  // Clear all function that clears both filters and search
  const clearAll = useCallback(() => {
    filters.handleClearFilters();
    search.clearSearch();
  }, [filters, search]);

  const value: LibraryFiltersContextType = {
    filters,
    search,
    filterValues: filters.filters,
    searchQuery: search.filterQuery,
    isFiltered,
    clearFilters: filters.handleClearFilters,
    clearSearch: search.clearSearch,
    clearAll,
  };

  return (
    <LibraryFiltersContext.Provider value={value}>
      {children}
    </LibraryFiltersContext.Provider>
  );
}

/**
 * Hook to access library filters context.
 *
 * Returns
 * -------
 * LibraryFiltersContextType
 *     Filter state, search state, and clear functions.
 *
 * Raises
 * ------
 * Error
 *     If used outside of LibraryFiltersProvider.
 */
export function useLibraryFiltersContext() {
  const context = useContext(LibraryFiltersContext);
  if (context === undefined) {
    throw new Error(
      "useLibraryFiltersContext must be used within a LibraryFiltersProvider",
    );
  }
  return context;
}
