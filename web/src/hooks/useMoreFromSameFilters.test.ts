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

import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import type { Book } from "@/types/book";
import { createEmptyFilters } from "@/utils/filters";

// Mocks
const mockHandleApplyFilters = vi.fn<(filters: FilterValues) => void>();
const mockHandleSuggestionsChange = vi.fn<(suggestions: unknown) => void>();

vi.mock("@/contexts/LibraryFiltersContext", () => ({
  useLibraryFiltersContext: () => ({
    filters: {
      filters: {
        ...createEmptyFilters(),
        // ensure we prove "replace" semantics by starting with non-empty values
        authorIds: [999],
        seriesIds: [999],
        genreIds: [999],
        publisherIds: [999],
      },
      selectedFilterSuggestions: {
        authorIds: [{ id: 999, name: "Old Author" }],
      },
      handleApplyFilters: mockHandleApplyFilters,
      handleSuggestionsChange: mockHandleSuggestionsChange,
    },
  }),
}));

vi.mock("@/hooks/useGenreTags", () => ({
  useGenreTags: vi.fn(),
}));

import { useGenreTags } from "@/hooks/useGenreTags";
import { defaultFilterSuggestionsService } from "@/services/filterSuggestionsService";
import { useMoreFromSameFilters } from "./useMoreFromSameFilters";

describe("useMoreFromSameFilters", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should disable Author when author_ids is missing/empty", () => {
    const book = {
      id: 1,
      title: "Book",
      authors: ["Author Name"],
      author_sort: null,
      title_sort: null,
      pubdate: null,
      timestamp: null,
      series: null,
      series_id: null,
      series_index: null,
      isbn: null,
      uuid: "uuid",
      thumbnail_url: null,
      has_cover: false,
      // no author_ids
    } satisfies Book;

    vi.mocked(useGenreTags).mockReturnValue({
      tagIds: [],
      isLoading: false,
      error: null,
    });

    const { result } = renderHook(() => useMoreFromSameFilters({ book }));
    expect(result.current.canApplyAuthor).toBe(false);
  });

  it("should apply Author using author_ids[0] and NOT call author suggestions endpoint", async () => {
    const spy = vi.spyOn(defaultFilterSuggestionsService, "fetchSuggestions");

    const book = {
      id: 1,
      title: "Book",
      authors: ["Author Name"],
      author_ids: [123],
      author_sort: null,
      title_sort: null,
      pubdate: null,
      timestamp: null,
      series: null,
      series_id: null,
      series_index: null,
      isbn: null,
      uuid: "uuid",
      thumbnail_url: null,
      has_cover: false,
    } satisfies Book;

    vi.mocked(useGenreTags).mockReturnValue({
      tagIds: [],
      isLoading: false,
      error: null,
    });

    const { result } = renderHook(() => useMoreFromSameFilters({ book }));
    expect(result.current.canApplyAuthor).toBe(true);

    await act(async () => {
      await result.current.apply("author");
    });

    // "replace context" semantics: only authorIds is set, everything else empty
    expect(mockHandleApplyFilters).toHaveBeenCalledWith({
      ...createEmptyFilters(),
      authorIds: [123],
    });

    expect(mockHandleSuggestionsChange).toHaveBeenCalledWith({
      authorIds: [{ id: 123, name: "Author Name" }],
    });

    // Author should not trigger suggestions fetch
    expect(spy).not.toHaveBeenCalled();
  });

  it.each([
    {
      name: "series (by id)",
      type: "series" as const,
      book: {
        id: 1,
        title: "Book",
        authors: ["Author Name"],
        author_ids: [1],
        author_sort: null,
        title_sort: null,
        pubdate: null,
        timestamp: null,
        series: "Series Name",
        series_id: 42,
        series_index: null,
        isbn: null,
        uuid: "uuid",
        thumbnail_url: null,
        has_cover: false,
      } satisfies Book,
      expectedFilters: { ...createEmptyFilters(), seriesIds: [42] },
      expectedSuggestions: { seriesIds: [{ id: 42, name: "Series Name" }] },
    },
    {
      name: "publisher (by id)",
      type: "publisher" as const,
      book: {
        id: 1,
        title: "Book",
        authors: ["Author Name"],
        author_ids: [1],
        author_sort: null,
        title_sort: null,
        pubdate: null,
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid",
        thumbnail_url: null,
        has_cover: false,
        publisher: "Publisher Name",
        publisher_id: 7,
      } satisfies Book,
      expectedFilters: { ...createEmptyFilters(), publisherIds: [7] },
      expectedSuggestions: {
        publisherIds: [{ id: 7, name: "Publisher Name" }],
      },
    },
  ])("should apply $name and replace filter context", async ({
    type,
    book,
    expectedFilters,
    expectedSuggestions,
  }) => {
    vi.mocked(useGenreTags).mockReturnValue({
      tagIds: [99],
      isLoading: false,
      error: null,
    });

    const { result } = renderHook(() => useMoreFromSameFilters({ book }));

    await act(async () => {
      await result.current.apply(type);
    });

    expect(mockHandleApplyFilters).toHaveBeenCalledWith(expectedFilters);
    expect(mockHandleSuggestionsChange).toHaveBeenCalledWith(
      expectedSuggestions,
    );
  });

  it("should apply Genre using the first tag name and tag id lookup", async () => {
    const book = {
      id: 1,
      title: "Book",
      authors: ["Author Name"],
      author_ids: [1],
      author_sort: null,
      title_sort: null,
      pubdate: null,
      timestamp: null,
      series: null,
      series_id: null,
      series_index: null,
      isbn: null,
      uuid: "uuid",
      thumbnail_url: null,
      has_cover: false,
      tags: ["Fiction", "Other"],
      tag_ids: [55, 56],
    } satisfies Book;

    vi.mocked(useGenreTags).mockReturnValue({
      tagIds: [55],
      isLoading: false,
      error: null,
    });

    const { result } = renderHook(() => useMoreFromSameFilters({ book }));
    expect(result.current.canApplyGenre).toBe(true);

    await act(async () => {
      await result.current.apply("genre");
    });

    expect(mockHandleApplyFilters).toHaveBeenCalledWith({
      ...createEmptyFilters(),
      genreIds: [55],
    });
    expect(mockHandleSuggestionsChange).toHaveBeenCalledWith({
      genreIds: [{ id: 55, name: "Fiction" }],
    });
  });
});
