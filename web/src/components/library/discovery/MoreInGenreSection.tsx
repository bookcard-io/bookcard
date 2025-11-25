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
import { useFilteredBooks } from "@/hooks/useFilteredBooks";
import { useGenreTags } from "@/hooks/useGenreTags";
import type { Book } from "@/types/book";
import { createEmptyFilters } from "@/utils/filters";
import {
  BROAD_STYLES_AS_GENRES,
  GENRE_CATEGORIES,
} from "@/utils/genreCategorizer";
import { HorizontalBookScroll } from "./HorizontalBookScroll";

export interface MoreInGenreSectionProps {
  /** Callback when book is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback when book edit is requested. */
  onBookEdit?: (bookId: number) => void;
  /** Callback when books data changes (for navigation). */
  onBooksDataChange?: (data: {
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  }) => void;
}

/**
 * More in random genre section.
 *
 * Displays books in a randomly selected genre.
 * Follows SRP by focusing solely on genre-based book display.
 */
export function MoreInGenreSection({
  onBookClick,
  onBookEdit,
  onBooksDataChange,
}: MoreInGenreSectionProps) {
  // Pick a random genre from standardized genres
  // Use useState + useEffect to avoid hydration mismatch (random is different on server/client)
  const [randomGenre, setRandomGenre] = useState<string | null>(null);

  useEffect(() => {
    const allGenres = Array.from(BROAD_STYLES_AS_GENRES).concat(
      Array.from(GENRE_CATEGORIES),
    );
    if (allGenres.length === 0) {
      setRandomGenre(null);
      return;
    }
    const randomIndex = Math.floor(Math.random() * allGenres.length);
    const selectedGenre = allGenres[randomIndex];
    if (selectedGenre) {
      setRandomGenre(selectedGenre);
    }
  }, []);

  // Lookup tag IDs for the genre
  const {
    tagIds,
    isLoading: isLoadingTags,
    error: tagsError,
  } = useGenreTags({
    genreNames: randomGenre ? [randomGenre] : [],
    enabled: randomGenre !== null,
  });

  const filters = useMemo(() => {
    const emptyFilters = createEmptyFilters();
    return {
      ...emptyFilters,
      genreIds: tagIds,
    };
  }, [tagIds]);

  const {
    books,
    isLoading: isLoadingBooks,
    error: booksError,
    loadMore,
    hasMore,
  } = useFilteredBooks({
    enabled: tagIds.length > 0,
    infiniteScroll: true,
    filters,
    sort_by: "title",
    sort_order: "asc",
    page_size: 20,
    full: false,
  });

  const allBooks = useMemo(() => {
    return books.flat();
  }, [books]);

  const isLoading = isLoadingTags || isLoadingBooks;
  const error = tagsError || booksError;

  // Don't render until randomGenre is set (client-side only)
  if (randomGenre === null) {
    return null;
  }

  if (error || tagIds.length === 0) {
    return null;
  }

  if (allBooks.length === 0 && !isLoading) {
    return null;
  }

  // Capitalize first letter of genre name
  const genreDisplayName =
    randomGenre.charAt(0).toUpperCase() + randomGenre.slice(1);

  return (
    <HorizontalBookScroll
      title={`More in ${genreDisplayName}`}
      books={allBooks}
      isLoading={isLoading}
      hasMore={hasMore ?? false}
      loadMore={loadMore}
      onBookClick={onBookClick}
      onBookEdit={onBookEdit}
      onBooksDataChange={onBooksDataChange}
    />
  );
}
