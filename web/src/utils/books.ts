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

/**
 * Book-related utility functions.
 *
 * Provides reusable functions for book data manipulation.
 * Follows SRP by separating book manipulation logic from presentation.
 * Follows DRY by centralizing book-related utilities.
 */

import type { Book } from "@/types/book";

/**
 * Generate cache-busting cover URL for a book.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID.
 * cacheBuster? : number
 *     Optional cache-busting timestamp. Defaults to current time.
 *
 * Returns
 * -------
 * string
 *     Cover URL with cache-busting parameter.
 */
export function getCoverUrlWithCacheBuster(
  bookId: number,
  cacheBuster?: number,
): string {
  const baseUrl = `/api/books/${bookId}/cover`;
  const timestamp = cacheBuster ?? Date.now();
  return `${baseUrl}?v=${timestamp}`;
}

/**
 * Deduplicate books by ID and apply book data overrides.
 *
 * Removes duplicate books based on ID and optionally applies
 * book data overrides from a map (including cover URL).
 * Only creates new objects for books with overrides to optimize performance.
 *
 * Parameters
 * ----------
 * books : Book[]
 *     Array of books to deduplicate.
 * coverUrlOverrides? : Map<number, string>
 *     Optional map of book ID to override cover URL (deprecated, use bookDataOverrides).
 * bookDataOverrides? : Map<number, Partial<Book>>
 *     Optional map of book ID to override book data (title, authors, cover URL, etc.).
 *
 * Returns
 * -------
 * Book[]
 *     Deduplicated array of books with overrides applied.
 */
export function deduplicateBooks(
  books: Book[],
  coverUrlOverrides?: Map<number, string>,
  bookDataOverrides?: Map<number, Partial<Book>>,
): Book[] {
  const seen = new Set<number>();
  const result: Book[] = [];

  for (const book of books) {
    if (seen.has(book.id)) {
      continue;
    }
    seen.add(book.id);

    // Check for overrides (Map lookups are O(1))
    // coverUrlOverrides is kept for backward compatibility but bookDataOverrides takes precedence
    const overrideUrl = coverUrlOverrides?.get(book.id);
    const overrideData = bookDataOverrides?.get(book.id);

    // Only create new object if there are overrides
    if (overrideUrl || overrideData) {
      const updatedBook = { ...book };
      // Apply bookDataOverrides first (takes precedence)
      if (overrideData) {
        Object.assign(updatedBook, overrideData);
      }
      // Apply coverUrlOverrides only if not already set in bookDataOverrides
      if (overrideUrl && !overrideData?.thumbnail_url) {
        updatedBook.thumbnail_url = overrideUrl;
      }
      result.push(updatedBook);
    } else {
      result.push(book);
    }
  }

  return result;
}

/**
 * Generate modal title for book edit modal.
 *
 * Creates an accessible title string for the book edit modal dialog.
 *
 * Parameters
 * ----------
 * book : Book
 *     Book data to generate title from.
 * formTitle? : string | null
 *     Optional form title (may differ from book title if edited).
 *
 * Returns
 * -------
 * string
 *     Modal title string.
 */
export function getBookEditModalTitle(
  book: Book,
  formTitle?: string | null,
): string {
  const title = formTitle || book.title;
  const authorsText =
    book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author";
  return `Editing book info - ${title} by ${authorsText}`;
}
