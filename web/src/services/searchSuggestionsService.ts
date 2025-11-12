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

import type { SearchSuggestionsResponse } from "@/types/search";

/**
 * Service interface for fetching search suggestions.
 *
 * Follows IOC pattern - allows dependency injection of different
 * implementations (API, mock, etc.).
 */
export interface SearchSuggestionsService {
  /**
   * Fetch search suggestions for a given query.
   *
   * Parameters
   * ----------
   * query : str
   *     The search query string.
   *
   * Returns
   * -------
   * Promise<SearchSuggestionsResponse>
   *     Search suggestions response.
   */
  fetchSuggestions(query: string): Promise<SearchSuggestionsResponse>;
}

/**
 * Default implementation using the API endpoint.
 */
class ApiSearchSuggestionsService implements SearchSuggestionsService {
  async fetchSuggestions(query: string): Promise<SearchSuggestionsResponse> {
    if (!query.trim()) {
      return { books: [], authors: [], tags: [], series: [] };
    }

    const response = await fetch(
      `/api/books/search/suggestions?q=${encodeURIComponent(query)}`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return { books: [], authors: [], tags: [], series: [] };
    }

    return (await response.json()) as SearchSuggestionsResponse;
  }
}

/**
 * Default service instance.
 */
export const defaultSearchSuggestionsService: SearchSuggestionsService =
  new ApiSearchSuggestionsService();
