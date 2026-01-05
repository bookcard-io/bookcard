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
import type { SearchSuggestionsService } from "./searchSuggestionsService";

/**
 * Service implementation for fetching search suggestions from tracked books.
 */
class TrackedBookSearchSuggestionsService implements SearchSuggestionsService {
  async fetchSuggestions(query: string): Promise<SearchSuggestionsResponse> {
    if (!query.trim()) {
      return { books: [], authors: [], tags: [], series: [] };
    }

    const response = await fetch(
      `/api/tracked-books/search/suggestions?q=${encodeURIComponent(query)}`,
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
 * Tracked book search suggestions service instance.
 */
export const trackedBookSearchSuggestionsService: SearchSuggestionsService =
  new TrackedBookSearchSuggestionsService();
