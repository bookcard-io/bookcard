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
import { useAuthors } from "@/hooks/useAuthors";
import type { AuthorWithMetadata } from "@/types/author";

export interface UseRandomAuthorResult {
  /** Random author data. */
  author: AuthorWithMetadata | null;
  /** Whether author is loading. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
}

/**
 * Hook for getting a random author.
 *
 * Fetches authors list and picks a random one.
 * Memoizes the selection to avoid re-selection on re-renders.
 * Follows SRP by managing only random author selection.
 *
 * Returns
 * -------
 * UseRandomAuthorResult
 *     Random author, loading state, and error.
 */
export function useRandomAuthor(): UseRandomAuthorResult {
  const { authors, isLoading, error, hasMore, loadMore } = useAuthors({
    pageSize: 100, // Fetch more authors for better randomness
  });
  const [selectedAuthor, setSelectedAuthor] =
    useState<AuthorWithMetadata | null>(null);

  // Load more if we don't have enough authors yet
  useEffect(() => {
    if (hasMore && authors.length < 50 && loadMore) {
      loadMore();
    }
  }, [hasMore, authors.length, loadMore]);

  // Pick a random author from the list (only once)
  useEffect(() => {
    if (!selectedAuthor && authors.length > 0) {
      const idx = Math.floor(Math.random() * authors.length);
      setSelectedAuthor(authors[idx] ?? null);
    }
  }, [authors, selectedAuthor]);

  return {
    author: selectedAuthor,
    isLoading,
    error: error ? String(error) : null,
  };
}
