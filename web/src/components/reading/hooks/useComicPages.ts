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

"use client";

import { useCallback, useEffect, useState } from "react";

export interface ComicPageInfo {
  page_number: number;
  filename: string;
  width: number | null;
  height: number | null;
  file_size: number;
}

export interface UseComicPagesOptions {
  bookId: number;
  format: string;
  enabled?: boolean;
}

export interface UseComicPagesResult {
  pages: ComicPageInfo[];
  isLoading: boolean;
  error: string | null;
  totalPages: number;
  refetch: () => void;
}

/**
 * Hook for fetching and managing comic book pages.
 *
 * Fetches page list from the comic API and provides page information.
 * Follows SRP by focusing solely on page data management.
 *
 * Parameters
 * ----------
 * options : UseComicPagesOptions
 *     Options including book ID and format.
 *
 * Returns
 * -------
 * UseComicPagesResult
 *     Page list, loading state, and error information.
 */
export function useComicPages({
  bookId,
  format,
  enabled = true,
}: UseComicPagesOptions): UseComicPagesResult {
  const [pages, setPages] = useState<ComicPageInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPages = useCallback(async () => {
    if (!enabled || !bookId || !format) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        file_format: format,
      });

      const response = await fetch(`/api/comic/${bookId}/pages?${params}`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to fetch pages" }));
        throw new Error(errorData.detail || "Failed to fetch pages");
      }

      const data = (await response.json()) as ComicPageInfo[];
      setPages(data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch pages";
      setError(errorMessage);
      setPages([]);
    } finally {
      setIsLoading(false);
    }
  }, [bookId, format, enabled]);

  useEffect(() => {
    void fetchPages();
  }, [fetchPages]);

  return {
    pages,
    isLoading,
    error,
    totalPages: pages.length,
    refetch: fetchPages,
  };
}
