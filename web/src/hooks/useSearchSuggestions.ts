import { useCallback, useEffect, useState } from "react";
import type { SearchSuggestionsService } from "@/services/searchSuggestionsService";
import { defaultSearchSuggestionsService } from "@/services/searchSuggestionsService";
import type { SearchSuggestion } from "@/types/search";
import { flattenSuggestions } from "@/utils/suggestions";

export interface UseSearchSuggestionsOptions {
  /** Search query string. */
  query: string;
  /** Whether to fetch suggestions (default: true). */
  enabled?: boolean;
  /** Custom service implementation (for testing/IOC). */
  service?: SearchSuggestionsService;
  /** Debounce delay in milliseconds (default: 300). */
  debounceDelay?: number;
}

export interface UseSearchSuggestionsResult {
  /** List of search suggestions. */
  suggestions: SearchSuggestion[];
  /** Whether suggestions are currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to manually refetch suggestions. */
  refetch: () => Promise<void>;
}

/**
 * Custom hook for fetching and managing search suggestions.
 *
 * Follows SRP by separating search logic from UI components.
 * Follows IOC by accepting a service dependency.
 *
 * Parameters
 * ----------
 * options : UseSearchSuggestionsOptions
 *     Configuration options for the hook.
 *
 * Returns
 * -------
 * UseSearchSuggestionsResult
 *     Search suggestions data and control functions.
 */
export function useSearchSuggestions(
  options: UseSearchSuggestionsOptions,
): UseSearchSuggestionsResult {
  const {
    query,
    enabled = true,
    service = defaultSearchSuggestionsService,
    debounceDelay = 300,
  } = options;

  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
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
    if (!enabled || !debouncedQuery.trim()) {
      setSuggestions([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await service.fetchSuggestions(debouncedQuery);
      const flattened = flattenSuggestions(response);
      setSuggestions(flattened);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, debouncedQuery, service]);

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
