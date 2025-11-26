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

import { useEffect, useState } from "react";
import { useDebounce } from "@/hooks/useDebounce";

export interface UsePathSuggestionsOptions {
  /** Query string to search for. */
  query: string;
  /** Whether suggestions are enabled (default: true). */
  enabled?: boolean;
  /** Minimum query length to trigger search (default: 2). */
  minQueryLength?: number;
  /** Debounce delay in milliseconds (default: 300). */
  debounceDelay?: number;
  /** Maximum number of suggestions to return (default: 50). */
  limit?: number;
  /** Whether to include files in suggestions (default: true). */
  includeFiles?: boolean;
}

export interface UsePathSuggestionsResult {
  /** List of path suggestions. */
  suggestions: string[];
  /** Whether suggestions dropdown should be shown. */
  show: boolean;
  /** Set whether suggestions dropdown should be shown. */
  setShow: (show: boolean) => void;
}

/**
 * Custom hook for fetching path directory suggestions.
 *
 * Debounces the query and fetches directory suggestions from the API.
 * Follows SRP by focusing solely on suggestion fetching logic.
 * Uses IOC by accepting configuration options.
 *
 * Parameters
 * ----------
 * options : UsePathSuggestionsOptions
 *     Configuration including query and options.
 *
 * Returns
 * -------
 * UsePathSuggestionsResult
 *     Suggestions list and visibility control.
 */
export function usePathSuggestions(
  options: UsePathSuggestionsOptions,
): UsePathSuggestionsResult {
  const {
    query,
    enabled = true,
    minQueryLength = 2,
    debounceDelay = 300,
    limit = 50,
    includeFiles = true,
  } = options;

  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [show, setShow] = useState(false);
  const debouncedQuery = useDebounce(query.trim(), debounceDelay);

  useEffect(() => {
    if (!enabled || debouncedQuery.length < minQueryLength) {
      setSuggestions([]);
      setShow(false);
      return;
    }

    let active = true;
    const controller = new AbortController();

    const fetchSuggestions = async () => {
      try {
        const response = await fetch(
          `/api/fs/suggest_dirs?q=${encodeURIComponent(debouncedQuery)}&limit=${limit}&include_files=${includeFiles}`,
          {
            cache: "no-store",
            signal: controller.signal,
          },
        );
        if (!response.ok) return;
        const data = (await response.json()) as { suggestions?: string[] };
        if (active) {
          const suggestionsList = Array.isArray(data?.suggestions)
            ? data.suggestions
            : [];
          setSuggestions(suggestionsList);
          setShow(suggestionsList.length > 0);
        }
      } catch {
        // Ignore suggest errors
      }
    };

    void fetchSuggestions();

    return () => {
      active = false;
      controller.abort();
    };
  }, [enabled, debouncedQuery, minQueryLength, limit, includeFiles]);

  return {
    suggestions,
    show,
    setShow,
  } as const;
}
