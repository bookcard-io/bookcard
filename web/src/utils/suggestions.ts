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
    suggestions.push({ type: "BOOK", id: item.id, name: item.name });
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
