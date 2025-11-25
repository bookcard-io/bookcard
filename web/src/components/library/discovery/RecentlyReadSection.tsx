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

import { useRecentlyReadBooks } from "@/hooks/useRecentlyReadBooks";
import type { Book } from "@/types/book";
import { HorizontalBookScroll } from "./HorizontalBookScroll";

export interface RecentlyReadSectionProps {
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
 * Recently read books section.
 *
 * Displays books that have been recently read by the user.
 * Follows SRP by focusing solely on recently read books display.
 */
export function RecentlyReadSection({
  onBookClick,
  onBookEdit,
  onBooksDataChange,
}: RecentlyReadSectionProps) {
  const { books, isLoading, error } = useRecentlyReadBooks({ limit: 20 });

  if (error) {
    return null; // Silently fail for discovery sections
  }

  if (books.length === 0 && !isLoading) {
    return null;
  }

  return (
    <HorizontalBookScroll
      title="Recently Read Books"
      books={books}
      isLoading={isLoading}
      hasMore={false}
      onBookClick={onBookClick}
      onBookEdit={onBookEdit}
      onBooksDataChange={onBooksDataChange}
    />
  );
}
