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

import { useCallback, useRef } from "react";
import { BooksGrid } from "@/components/library/BooksGrid";
import type { AuthorWithMetadata } from "@/types/author";
import type { Book } from "@/types/book";

export interface AuthorLibraryBooksProps {
  /** Author data. */
  author: AuthorWithMetadata;
  /** Callback when a book is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback when a book edit button is clicked. */
  onBookEdit?: (bookId: number) => void;
}

/**
 * Author library books section component.
 *
 * Displays a grid of books by the author from the library.
 * Uses BooksGrid with author name as search query.
 * Follows SRP by focusing solely on book grid presentation.
 *
 * Parameters
 * ----------
 * props : AuthorLibraryBooksProps
 *     Component props including author data and callbacks.
 */
export function AuthorLibraryBooks({
  author,
  onBookClick,
  onBookEdit,
}: AuthorLibraryBooksProps) {
  const bookDataUpdateRef = useRef<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
    addBook?: (bookId: number) => Promise<void>;
  } | null>(null);

  const handleBooksDataChange = useCallback(() => {
    // No-op for now, can be used for navigation if needed
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="m-0 font-bold text-[var(--color-text-a0)] text-xl">
        Library Books
      </h2>
      <div className="-mx-8">
        <BooksGrid
          searchQuery={author.name}
          onBookClick={onBookClick}
          onBookEdit={onBookEdit}
          bookDataUpdateRef={bookDataUpdateRef}
          onBooksDataChange={handleBooksDataChange}
          sortBy="title"
          sortOrder="asc"
          hideStatusHeader={true}
          hideLoadMoreMessage={true}
        />
      </div>
    </div>
  );
}
