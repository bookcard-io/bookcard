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
      return { books: [], authors: [], tags: [] };
    }

    const response = await fetch(
      `/api/books/search/suggestions?q=${encodeURIComponent(query)}`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return { books: [], authors: [], tags: [] };
    }

    return (await response.json()) as SearchSuggestionsResponse;
  }
}

/**
 * Default service instance.
 */
export const defaultSearchSuggestionsService: SearchSuggestionsService =
  new ApiSearchSuggestionsService();
