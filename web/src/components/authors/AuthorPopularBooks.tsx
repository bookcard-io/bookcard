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

import { useRouter } from "next/navigation";
import type { AuthorWithMetadata } from "@/types/author";

export interface AuthorPopularBooksProps {
  /** List of popular books by the author. */
  books: NonNullable<AuthorWithMetadata["popular_books"]>;
}

/**
 * Author popular books section component.
 *
 * Displays a list of popular books by the author.
 * Similar to Plex "Popular Tracks" section.
 * Follows SRP by focusing solely on book list presentation.
 *
 * Parameters
 * ----------
 * props : AuthorPopularBooksProps
 *     Component props including list of books.
 */
export function AuthorPopularBooks({ books }: AuthorPopularBooksProps) {
  const router = useRouter();

  const handleBookClick = (bookId: number) => {
    router.push(`/books/${bookId}/view`);
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="m-0 font-bold text-[var(--color-text-a0)] text-xl">
        Popular Books
      </h2>
      <div className="flex flex-col gap-0">
        {books.map((book, index) => (
          <button
            key={book.id}
            type="button"
            onClick={() => handleBookClick(book.id)}
            className="group flex items-center gap-4 border-surface-a20 border-b px-2 py-3 text-left transition-[background-color] duration-200 first:border-t hover:bg-surface-a10 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
            aria-label={`View ${book.title}`}
          >
            <span className="flex-shrink-0 font-medium text-[var(--color-text-a30)] text-sm">
              {index + 1}.
            </span>
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <span className="font-medium text-[var(--color-text-a0)] text-sm group-hover:text-[var(--color-primary-a0)]">
                {book.title}
              </span>
              {book.series && (
                <span className="text-[var(--color-text-a30)] text-xs">
                  {book.series}
                </span>
              )}
            </div>
            {book.duration && (
              <span className="flex-shrink-0 text-[var(--color-text-a30)] text-sm">
                {book.duration}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
