import { useCallback, useEffect, useState } from "react";
import type { FilterSuggestionsService } from "@/services/filterSuggestionsService";
import { defaultFilterSuggestionsService } from "@/services/filterSuggestionsService";
import type { SearchSuggestionItem } from "@/types/search";

export interface UseFilterSuggestionsOptions {
  /** Search query string. */
  query: string;
  /** Filter type: 'author', 'title', 'genre', 'publisher', 'identifier', 'series', 'format', 'rating', 'language'. */
  filterType: string;
  /** Whether to fetch suggestions (default: true). */
  enabled?: boolean;
  /** Custom service implementation (for testing/IOC). */
  service?: FilterSuggestionsService;
  /** Debounce delay in milliseconds (default: 300). */
  debounceDelay?: number;
}

export interface UseFilterSuggestionsResult {
  /** List of filter suggestions. */
  suggestions: SearchSuggestionItem[];
  /** Whether suggestions are currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to manually refetch suggestions. */
  refetch: () => Promise<void>;
}

/**
 * Custom hook for fetching and managing filter suggestions.
 *
 * Follows SRP by separating filter logic from UI components.
 * Follows IOC by accepting a service dependency.
 *
 * Parameters
 * ----------
 * options : UseFilterSuggestionsOptions
 *     Configuration options for the hook.
 *
 * Returns
 * -------
 * UseFilterSuggestionsResult
 *     Filter suggestions data and control functions.
 */
export function useFilterSuggestions(
  options: UseFilterSuggestionsOptions,
): UseFilterSuggestionsResult {
  const {
    query,
    filterType,
    enabled = true,
    service = defaultFilterSuggestionsService,
    debounceDelay = 300,
  } = options;

  const [suggestions, setSuggestions] = useState<SearchSuggestionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceDelay);

    return () => {
      clearTimeout(timer);
    };
  }, [query, debounceDelay]);

  const fetchSuggestions = useCallback(async () => {
    if (!enabled || !debouncedQuery.trim() || !filterType.trim()) {
      setSuggestions([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await service.fetchSuggestions(
        debouncedQuery,
        filterType,
      );
      setSuggestions(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, debouncedQuery, filterType, service]);

  useEffect(() => {
    void fetchSuggestions();
  }, [fetchSuggestions]);

  return {
    suggestions,
    isLoading,
    error,
    refetch: fetchSuggestions,
  };
}
