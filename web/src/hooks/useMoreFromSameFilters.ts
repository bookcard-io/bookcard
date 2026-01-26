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

import { useCallback, useMemo } from "react";
import { useLibraryFiltersContext } from "@/contexts/LibraryFiltersContext";
import { useGenreTags } from "@/hooks/useGenreTags";
import { defaultFilterSuggestionsService } from "@/services/filterSuggestionsService";
import type { Book } from "@/types/book";
import type { SearchSuggestionItem } from "@/types/search";
import { createEmptyFilters } from "@/utils/filters";

export type MoreFromSameFilterType =
  | "author"
  | "series"
  | "genre"
  | "publisher";

export interface UseMoreFromSameFiltersOptions {
  /** Book to derive filter values from. */
  book: Book;
  /** Whether any async lookups should be enabled (e.g., when flyout is open). */
  enabled?: boolean;
}

export interface UseMoreFromSameFiltersResult {
  /** Whether the Author option can be applied (data present). */
  canApplyAuthor: boolean;
  /** Whether the Series option can be applied (data present). */
  canApplySeries: boolean;
  /** Whether the Genre option can be applied (data present). */
  canApplyGenre: boolean;
  /** Whether the Publisher option can be applied (data present). */
  canApplyPublisher: boolean;

  /** Whether genre tag lookup is in flight. */
  isGenreLookupLoading: boolean;
  /** Genre tag lookup error message, if any. */
  genreLookupError: string | null;

  /**
   * Apply the given filter type to library filters.
   *
   * Notes
   * -----
   * - Replaces the filter context (resets filters), then sets only the selected filter type.
   * - Replaces selected suggestions to keep FiltersPanel in sync.
   *
   * Parameters
   * ----------
   * filterType : MoreFromSameFilterType
   *     Filter type to apply.
   *
   * Returns
   * -------
   * Promise<void>
   *     Resolves when the filter has been applied. Rejects if lookup fails or data is missing.
   */
  apply: (filterType: MoreFromSameFilterType) => Promise<void>;
}

function normalizeOptionalString(
  value: string | null | undefined,
): string | null {
  const trimmed = value?.trim() ?? "";
  return trimmed.length > 0 ? trimmed : null;
}

function isValidId(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function findExactSuggestionId(
  suggestions: SearchSuggestionItem[],
  expectedName: string,
): number | null {
  const expectedLower = expectedName.trim().toLowerCase();
  for (const s of suggestions) {
    const candidate = (s.displayName ?? s.name).trim().toLowerCase();
    if (candidate === expectedLower) {
      return s.id;
    }
  }
  return null;
}

/**
 * Hook that applies "More from the same..." filters from a book.
 *
 * Designed to integrate with LibraryFiltersContext so applying filters:
 * - updates the filter values (FilterValues)
 * - updates selected suggestions (SelectedFilterSuggestions) for FiltersPanel display
 *
 * Parameters
 * ----------
 * options : UseMoreFromSameFiltersOptions
 *     Hook options including the target book and whether async lookups are enabled.
 *
 * Returns
 * -------
 * UseMoreFromSameFiltersResult
 *     Capability flags, lookup state, and an apply() function.
 */
export function useMoreFromSameFilters(
  options: UseMoreFromSameFiltersOptions,
): UseMoreFromSameFiltersResult {
  const { book, enabled = true } = options;
  const libraryFilters = useLibraryFiltersContext();

  const firstAuthor = useMemo(
    () => normalizeOptionalString(book.authors?.[0]),
    [book.authors],
  );
  const firstAuthorId = useMemo(
    () =>
      isValidId(book.author_ids?.[0]) ? (book.author_ids?.[0] ?? null) : null,
    [book.author_ids],
  );
  const firstTag = useMemo(
    () => normalizeOptionalString(book.tags?.[0]),
    [book.tags],
  );
  const seriesName = useMemo(
    () => normalizeOptionalString(book.series),
    [book.series],
  );
  const publisherName = useMemo(
    () => normalizeOptionalString(book.publisher),
    [book.publisher],
  );

  const canApplyAuthor = firstAuthorId !== null;
  // Prefer ID, but allow applying via name if IDs are not present in list view.
  const canApplySeries = isValidId(book.series_id) || seriesName !== null;
  const canApplyGenre = firstTag !== null;
  // Prefer ID, but allow applying via name if IDs are not present in list view.
  const canApplyPublisher =
    isValidId(book.publisher_id) || publisherName !== null;

  // Pre-fetch tag IDs while the flyout is open for snappy click-to-apply.
  const genreTags = useGenreTags({
    genreNames: firstTag ? [firstTag] : [],
    enabled: enabled && firstTag !== null,
  });

  const apply = useCallback(
    async (filterType: MoreFromSameFilterType) => {
      const current = libraryFilters.filters;
      const empty = createEmptyFilters();

      if (filterType === "author") {
        if (!firstAuthorId) {
          throw new Error("Author ID is not available for this book");
        }
        const displayName = firstAuthor ?? `Author ID: ${firstAuthorId}`;

        const updatedFilters = { ...empty, authorIds: [firstAuthorId] };
        const updatedSuggestions = {
          authorIds: [
            {
              id: firstAuthorId,
              name: displayName,
            } satisfies SearchSuggestionItem,
          ],
        };

        current.handleApplyFilters(updatedFilters);
        current.handleSuggestionsChange(updatedSuggestions);
        return;
      }

      if (filterType === "series") {
        const resolvedSeriesId = isValidId(book.series_id)
          ? book.series_id
          : seriesName
            ? findExactSuggestionId(
                await defaultFilterSuggestionsService.fetchSuggestions(
                  seriesName,
                  "series",
                ),
                seriesName,
              )
            : null;

        if (!resolvedSeriesId) {
          throw new Error("Series is not available for this book");
        }

        const displayName = seriesName ?? `Series ID: ${resolvedSeriesId}`;

        const updatedFilters = { ...empty, seriesIds: [resolvedSeriesId] };
        const updatedSuggestions = {
          seriesIds: [
            {
              id: resolvedSeriesId,
              name: displayName,
            } satisfies SearchSuggestionItem,
          ],
        };

        current.handleApplyFilters(updatedFilters);
        current.handleSuggestionsChange(updatedSuggestions);
        return;
      }

      if (filterType === "genre") {
        if (!firstTag) {
          throw new Error("Genre is not available for this book");
        }
        if (genreTags.error) {
          throw new Error(genreTags.error);
        }
        const tagId = genreTags.tagIds[0];
        if (!tagId) {
          throw new Error(`No genre match found for "${firstTag}"`);
        }

        const updatedFilters = { ...empty, genreIds: [tagId] };
        const updatedSuggestions = {
          genreIds: [
            { id: tagId, name: firstTag } satisfies SearchSuggestionItem,
          ],
        };

        current.handleApplyFilters(updatedFilters);
        current.handleSuggestionsChange(updatedSuggestions);
        return;
      }

      // publisher
      const resolvedPublisherId = isValidId(book.publisher_id)
        ? book.publisher_id
        : publisherName
          ? findExactSuggestionId(
              await defaultFilterSuggestionsService.fetchSuggestions(
                publisherName,
                "publisher",
              ),
              publisherName,
            )
          : null;

      if (!resolvedPublisherId) {
        throw new Error("Publisher is not available for this book");
      }

      const displayName =
        publisherName ?? `Publisher ID: ${resolvedPublisherId}`;

      const updatedFilters = {
        ...empty,
        publisherIds: [resolvedPublisherId],
      };
      const updatedSuggestions = {
        publisherIds: [
          {
            id: resolvedPublisherId,
            name: displayName,
          } satisfies SearchSuggestionItem,
        ],
      };

      current.handleApplyFilters(updatedFilters);
      current.handleSuggestionsChange(updatedSuggestions);
    },
    [
      book.publisher_id,
      book.series_id,
      firstAuthor,
      firstTag,
      genreTags.error,
      genreTags.tagIds,
      libraryFilters.filters,
      publisherName,
      seriesName,
      firstAuthorId,
    ],
  );

  return {
    canApplyAuthor,
    canApplySeries,
    canApplyGenre,
    canApplyPublisher,
    isGenreLookupLoading: genreTags.isLoading,
    genreLookupError: genreTags.error,
    apply,
  };
}
