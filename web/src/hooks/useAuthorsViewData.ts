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

import type { AuthorWithMetadata } from "@/types/author";
import { useAuthors } from "./useAuthors";

export interface UseAuthorsViewDataOptions {
  /** Number of items per page. */
  pageSize?: number;
  /** Filter type: "all" shows all authors, "unmatched" shows only unmatched authors. */
  filterType?: "all" | "unmatched";
}

export interface UseAuthorsViewDataResult {
  /** List of authors. */
  authors: AuthorWithMetadata[];
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Total number of authors. */
  total: number;
  /** Function to load next page. */
  loadMore?: () => void;
  /** Whether there are more pages to load. */
  hasMore?: boolean;
}

/**
 * Custom hook for managing authors view data.
 *
 * Handles data fetching with infinite scroll support.
 * Follows SRP by managing only data concerns.
 * Follows IOC by accepting configuration options.
 * Follows DRY by centralizing common data management logic.
 *
 * Parameters
 * ----------
 * options : UseAuthorsViewDataOptions
 *     Configuration for pagination.
 *
 * Returns
 * -------
 * UseAuthorsViewDataResult
 *     Authors data, loading state, and control functions.
 */
export function useAuthorsViewData(
  options: UseAuthorsViewDataOptions = {},
): UseAuthorsViewDataResult {
  const { pageSize = 20, filterType = "all" } = options;

  // Fetch authors using centralized hook with server-side filtering (SOC: data fetching separated)
  const { authors, isLoading, error, total, loadMore, hasMore } = useAuthors({
    infiniteScroll: true,
    pageSize,
    filter: filterType === "unmatched" ? "unmatched" : undefined,
  });

  return {
    authors,
    isLoading,
    error,
    total,
    loadMore,
    hasMore,
  };
}
