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
 * Deduplicate books by ID and apply cover URL overrides.
 *
 * Removes duplicate books based on ID and optionally applies
 * cover URL overrides from a map. Only creates new objects
 * for books with updated URLs to optimize performance.
 *
 * Parameters
 * ----------
 * books : Book[]
 *     Array of books to deduplicate.
 * coverUrlOverrides? : Map<number, string>
 *     Optional map of book ID to override cover URL.
 *
 * Returns
 * -------
 * Book[]
 *     Deduplicated array of books with cover URL overrides applied.
 */
export function deduplicateBooks(
  books: Book[],
  coverUrlOverrides?: Map<number, string>,
): Book[] {
  const seen = new Set<number>();
  const result: Book[] = [];

  for (const book of books) {
    if (seen.has(book.id)) {
      continue;
    }
    seen.add(book.id);

    // Only create new object if URL was overridden (Map lookup is O(1))
    const overrideUrl = coverUrlOverrides?.get(book.id);
    if (overrideUrl) {
      result.push({ ...book, thumbnail_url: overrideUrl });
    } else {
      result.push(book);
    }
  }

  return result;
}
