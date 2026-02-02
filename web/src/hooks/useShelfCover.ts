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

import { useEffect, useMemo, useState } from "react";
import { fetchMagicShelfCoverBooks } from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";
import { isMagicShelf as isMagicShelfUtil } from "@/utils/shelfUtils";

export type ShelfCoverGridLayout = "one" | "two" | "three" | "four";

export interface UseShelfCoverOptions {
  /** Shelf to derive cover information from. */
  shelf: Shelf;
  /** Whether the hook should fetch grid covers when applicable. */
  enabled?: boolean;
}

export interface ShelfCoverData {
  /** Whether shelf is a Magic Shelf (normalized). */
  isMagicShelf: boolean;
  /** Whether shelf has a custom cover picture. */
  hasCustomCover: boolean;
  /** Whether the UI should prefer the grid cover strategy. */
  shouldUseGridCover: boolean;
  /** Candidate book cover URLs for the grid cover. */
  coverUrls: string[];
  /** Layout hint for grid rendering based on cover count. */
  gridLayout: ShelfCoverGridLayout;
  /** Whether grid cover IDs are being fetched. */
  isLoading: boolean;
  /** Error message when fetch fails (non-abort). */
  error: string | null;
}

/**
 * Encapsulate shelf cover selection and Magic Shelf grid cover fetching.
 *
 * Notes
 * -----
 * - Keeps API/service logic out of presentation components (SRP).
 * - Enables reuse of Magic Shelf cover selection across shelf UIs (DRY).
 */
export function useShelfCover(options: UseShelfCoverOptions): ShelfCoverData {
  const { shelf, enabled = true } = options;

  const isMagicShelf = isMagicShelfUtil(shelf);
  const hasCustomCover = Boolean(shelf.cover_picture);
  const shouldUseGridCover = enabled && isMagicShelf && !hasCustomCover;

  const [coverBookIds, setCoverBookIds] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!shouldUseGridCover) {
      setCoverBookIds([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    const abortController = new AbortController();
    setIsLoading(true);
    setError(null);

    fetchMagicShelfCoverBooks(shelf.id, abortController.signal)
      .then((bookIds) => {
        setCoverBookIds(bookIds.slice(0, 4));
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        const message = err instanceof Error ? err.message : "Failed to load";
        setError(message);
        setCoverBookIds([]);
      })
      .finally(() => {
        setIsLoading(false);
      });

    return () => abortController.abort();
  }, [shouldUseGridCover, shelf.id]);

  const coverUrls = useMemo(() => {
    return coverBookIds.map((id) => `/api/books/${id}/cover`);
  }, [coverBookIds]);

  const gridLayout = useMemo<ShelfCoverGridLayout>(() => {
    const count = coverUrls.length;
    if (count <= 1) return "one";
    if (count === 2) return "two";
    if (count === 3) return "three";
    return "four";
  }, [coverUrls.length]);

  return {
    isMagicShelf,
    hasCustomCover,
    shouldUseGridCover,
    coverUrls,
    gridLayout,
    isLoading,
    error,
  };
}
