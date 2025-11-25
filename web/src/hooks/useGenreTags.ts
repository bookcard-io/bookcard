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

import { useQuery } from "@tanstack/react-query";

export interface UseGenreTagsOptions {
  /** Genre names to lookup. */
  genreNames: string[];
  /** Whether the query is enabled. */
  enabled?: boolean;
}

export interface UseGenreTagsResult {
  /** Tag IDs matching the genre names. */
  tagIds: number[];
  /** Whether tags are loading. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
}

/**
 * Hook for looking up tag IDs by genre names.
 *
 * Calls the genre/tag lookup endpoint to get tag IDs.
 * Follows SRP by managing only genre tag lookup.
 *
 * Parameters
 * ----------
 * options : UseGenreTagsOptions
 *     Configuration options.
 *
 * Returns
 * -------
 * UseGenreTagsResult
 *     Tag IDs, loading state, and error.
 */
export function useGenreTags(options: UseGenreTagsOptions): UseGenreTagsResult {
  const { genreNames, enabled = true } = options;

  const { data, isLoading, error } = useQuery({
    queryKey: ["genre-tags", genreNames],
    queryFn: async () => {
      if (genreNames.length === 0) {
        return { tags: [] };
      }
      const params = new URLSearchParams({
        names: genreNames.join(","),
      });
      const response = await fetch(`/api/books/tags/by-name?${params}`, {
        credentials: "include",
      });
      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to lookup tags");
      }
      return (await response.json()) as {
        tags: Array<{ id: number; name: string }>;
      };
    },
    enabled: enabled && genreNames.length > 0,
    staleTime: 300_000, // 5 minutes - genre tags don't change often
  });

  const tagIds = data?.tags.map((tag) => tag.id) ?? [];

  return {
    tagIds,
    isLoading,
    error: error
      ? error instanceof Error
        ? error.message
        : "Failed to lookup tags"
      : null,
  };
}
