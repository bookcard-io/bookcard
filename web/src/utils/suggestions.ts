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

import type {
  SearchSuggestion,
  SearchSuggestionsResponse,
} from "@/types/search";

/**
 * Convert search suggestions response to flat list with type indicators.
 *
 * Parameters
 * ----------
 * response : SearchSuggestionsResponse
 *     The search suggestions response from the API.
 *
 * Returns
 * -------
 * SearchSuggestion[]
 *     Flat list of suggestions with type indicators.
 */
export function flattenSuggestions(
  response: SearchSuggestionsResponse,
): SearchSuggestion[] {
  const suggestions: SearchSuggestion[] = [];

  response.books.forEach((item) => {
    suggestions.push({
      type: "BOOK",
      id: item.id,
      name: item.title || item.name,
    });
  });

  response.authors.forEach((item) => {
    suggestions.push({ type: "AUTHOR", id: item.id, name: item.name });
  });

  response.tags.forEach((item) => {
    suggestions.push({ type: "TAG", id: item.id, name: item.name });
  });

  response.series.forEach((item) => {
    suggestions.push({ type: "SERIES", id: item.id, name: item.name });
  });

  return suggestions;
}
