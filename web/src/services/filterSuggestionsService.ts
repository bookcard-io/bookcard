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

import { POPULAR_LANGUAGES } from "@/constants/languages";
import type { SearchSuggestionItem } from "@/types/search";

/**
 * Service interface for fetching filter suggestions.
 *
 * Follows IOC pattern - allows dependency injection of different
 * implementations (API, mock, etc.).
 */
export interface FilterSuggestionsService {
  /**
   * Fetch filter suggestions for a given query and filter type.
   *
   * Parameters
   * ----------
   * query : string
   *     The search query string.
   * filterType : string
   *     The type of filter: 'author', 'title', 'genre', 'publisher',
   *     'identifier', 'series', 'format', 'rating', 'language'.
   *
   * Returns
   * -------
   * Promise<SearchSuggestionItem[]>
   *     List of filter suggestions.
   */
  fetchSuggestions(
    query: string,
    filterType: string,
  ): Promise<SearchSuggestionItem[]>;
}

/**
 * Default implementation using the API endpoint.
 */
class ApiFilterSuggestionsService implements FilterSuggestionsService {
  async fetchSuggestions(
    query: string,
    filterType: string,
  ): Promise<SearchSuggestionItem[]> {
    if (!query.trim()) {
      return [];
    }

    const response = await fetch(
      `/api/books/filter/suggestions?q=${encodeURIComponent(query)}&filter_type=${encodeURIComponent(filterType)}`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return [];
    }

    const data = (await response.json()) as {
      suggestions: SearchSuggestionItem[];
    };
    return data.suggestions;
  }
}

/**
 * Service implementation for static language suggestions.
 *
 * Uses a predefined list of popular languages and filters them
 * based on the query string (matches both code and name).
 */
class LanguageFilterSuggestionsService implements FilterSuggestionsService {
  async fetchSuggestions(
    query: string,
    filterType: string,
  ): Promise<SearchSuggestionItem[]> {
    if (!query.trim() || filterType !== "language") {
      return [];
    }

    const queryLower = query.toLowerCase().trim();
    const matches: SearchSuggestionItem[] = [];

    for (let i = 0; i < POPULAR_LANGUAGES.length; i++) {
      const language = POPULAR_LANGUAGES[i];
      if (!language) continue;

      // Extract ISO-639-1 base code (part before the dash) for backend use
      const baseCode = language.code.split("-")[0] as string;

      const codeLower = baseCode.toLowerCase();
      const nameLower = language.name.toLowerCase();
      const englishNameLower = language.englishName.toLowerCase();

      // Match if query matches base code, name, or english name
      if (
        codeLower.includes(queryLower) ||
        nameLower.includes(queryLower) ||
        englishNameLower.includes(queryLower)
      ) {
        matches.push({
          id: matches.length + 1, // Use sequential ID
          name: baseCode, // ISO-639-1 base code for backend use (maps all variants to same code)
          displayName: language.englishName || language.name, // Friendly name for display (shows all variants)
        });
      }

      // Limit results to 20 for performance
      if (matches.length >= 20) {
        break;
      }
    }

    return matches;
  }
}

/**
 * Default service instance.
 */
export const defaultFilterSuggestionsService: FilterSuggestionsService =
  new ApiFilterSuggestionsService();

/**
 * Language-specific service instance for static suggestions.
 */
export const languageFilterSuggestionsService: FilterSuggestionsService =
  new LanguageFilterSuggestionsService();
