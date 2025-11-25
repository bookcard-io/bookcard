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

export interface OnThisDaySectionProps {
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
 * On this day in history section.
 *
 * Displays all books published on this day (month and day) from any year.
 * Uses the year from the first matching book for the section title.
 * Follows SRP by focusing solely on historical date filtering.
 */
export function OnThisDaySection({
  onBookClick,
  onBookEdit,
  onBooksDataChange,
}: OnThisDaySectionProps) {
  // Get today's month and day
  const today = new Date();
  const month = today.getMonth() + 1; // JavaScript months are 0-indexed
  const day = today.getDate();

  const { books, isLoading, error, loadMore, hasMore } = useBooks({
    enabled: true,
    infiniteScroll: true,
    sort_by: "pubdate",
    sort_order: "asc", // Sort ascending to get oldest books first
    page_size: 20,
    full: false,
    pubdate_month: month,
    pubdate_day: day,
  });

  const allBooks = useMemo(() => {
    return books.flat();
  }, [books]);

  // Extract year from the first book's pubdate (if available)
  const historicalYear = useMemo(() => {
    const firstBook = allBooks.find((book) => book.pubdate);
    if (firstBook?.pubdate) {
      const pubDate = new Date(firstBook.pubdate);
      return pubDate.getFullYear();
    }
    return null;
  }, [allBooks]);

  if (error) {
    return null;
  }

  if (allBooks.length === 0 && !isLoading) {
    return null;
  }

  // Don't render if we don't have a year from the first book
  if (historicalYear === null) {
    return null;
  }

  return (
    <HorizontalBookScroll
      title={`On This Day In ${historicalYear}`}
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
