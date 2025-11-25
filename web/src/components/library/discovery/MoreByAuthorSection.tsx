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

import { useMemo } from "react";
import { useBooks } from "@/hooks/useBooks";
import { useRandomAuthor } from "@/hooks/useRandomAuthor";
import type { Book } from "@/types/book";
import { HorizontalBookScroll } from "./HorizontalBookScroll";

export interface MoreByAuthorSectionProps {
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
 * More by random author section.
 *
 * Displays books by a randomly selected author.
 * Follows SRP by focusing solely on author-based book display.
 */
export function MoreByAuthorSection({
  onBookClick,
  onBookEdit,
  onBooksDataChange,
}: MoreByAuthorSectionProps) {
  const {
    author,
    isLoading: isLoadingAuthor,
    error: authorError,
  } = useRandomAuthor();

  const {
    books,
    isLoading: isLoadingBooks,
    error: booksError,
    loadMore,
    hasMore,
  } = useBooks({
    enabled: author !== null && author.calibre_id !== undefined,
    infiniteScroll: true,
    author_id: author?.calibre_id,
    sort_by: "title",
    sort_order: "asc",
    page_size: 20,
    full: false,
  });

  const allBooks = useMemo(() => {
    return books.flat();
  }, [books]);

  const isLoading = isLoadingAuthor || isLoadingBooks;
  const error = authorError || booksError;

  if (error || !author) {
    return null;
  }

  if (allBooks.length === 0 && !isLoading) {
    return null;
  }

  return (
    <HorizontalBookScroll
      title={`More by ${author.name}`}
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
