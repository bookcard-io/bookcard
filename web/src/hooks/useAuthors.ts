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

import { useCallback, useEffect, useState } from "react";
import { fetchAuthors } from "@/services/authorService";
import type { AuthorWithMetadata } from "@/types/author";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";

export interface UseAuthorsOptions {
  /** Whether the query is enabled. */
  enabled?: boolean;
}

export interface UseAuthorsResult {
  /** Array of authors. */
  authors: AuthorWithMetadata[];
  /** Whether data is currently loading. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to manually refetch authors. */
  refetch: () => Promise<void>;
}

/**
 * Custom hook for fetching all authors.
 *
 * Provides loading state, error handling, and refetch functionality.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseAuthorsOptions
 *     Hook options.
 *
 * Returns
 * -------
 * UseAuthorsResult
 *     Authors data, loading state, and control functions.
 */
export function useAuthors(options: UseAuthorsOptions = {}): UseAuthorsResult {
  const { enabled = true } = options;

  const [authors, setAuthors] = useState<AuthorWithMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAuthorsData = useCallback(async () => {
    if (!enabled) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const url = "/api/authors";
      const fetchKey = generateFetchKey(url, {
        method: "GET",
      });

      const result = await deduplicateFetch(fetchKey, async () => {
        return await fetchAuthors();
      });

      setAuthors(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setAuthors([]);
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void fetchAuthorsData();
  }, [fetchAuthorsData]);

  return {
    authors,
    isLoading,
    error,
    refetch: fetchAuthorsData,
  };
}
