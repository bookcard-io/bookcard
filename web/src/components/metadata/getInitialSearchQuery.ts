import type { Book } from "@/types/book";

/**
 * Determines the initial search query from book data.
 *
 * Priority: title > series > author
 * Follows SRP by focusing solely on query derivation logic.
 *
 * @param book - Book data to extract query from.
 * @returns Initial search query string, or empty string if no data available.
 */
export function getInitialSearchQuery(book: Book | null): string {
  if (!book) {
    return "";
  }

  // Priority 1: Title
  if (book.title?.trim()) {
    return book.title.trim();
  }

  // Priority 2: Series name
  if (book.series?.trim()) {
    return book.series.trim();
  }

  // Priority 3: Author name
  if (book.authors && book.authors.length > 0) {
    return book.authors[0].trim();
  }

  return "";
}
