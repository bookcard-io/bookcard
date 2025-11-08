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
 * Default service instance.
 */
export const defaultFilterSuggestionsService: FilterSuggestionsService =
  new ApiFilterSuggestionsService();
