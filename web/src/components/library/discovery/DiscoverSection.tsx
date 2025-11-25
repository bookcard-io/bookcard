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
import type { Book } from "@/types/book";
import { HorizontalBookScroll } from "./HorizontalBookScroll";

export interface DiscoverSectionProps {
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
 * Discover section.
 *
 * Displays random books for discovery.
 * Follows SRP by focusing solely on random book display.
 */
export function DiscoverSection({
  onBookClick,
  onBookEdit,
  onBooksDataChange,
}: DiscoverSectionProps) {
  const { books, isLoading, error, loadMore, hasMore } = useBooks({
    enabled: true,
    infiniteScroll: true,
    sort_by: "random",
    sort_order: "desc", // Ignored for random sort
    page_size: 20,
    full: false,
  });

  const allBooks = useMemo(() => {
    return books.flat();
  }, [books]);

  if (error) {
    return null;
  }

  if (allBooks.length === 0 && !isLoading) {
    return null;
  }

  return (
    <HorizontalBookScroll
      title="Discover"
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
