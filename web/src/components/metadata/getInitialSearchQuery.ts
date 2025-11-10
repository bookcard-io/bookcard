import type { Book, BookUpdate } from "@/types/book";

/**
 * Determines the initial search query from book data.
 *
 * Priority: title > series > author
 * Uses form data if provided, otherwise falls back to book data.
 * Follows SRP by focusing solely on query derivation logic.
 *
 * Parameters
 * ----------
 * book : Book | null
 *     Book data to extract query from.
 * formData : BookUpdate | null | undefined
 *     Optional form data that takes priority over book data.
 *
 * Returns
 * -------
 * string
 *     Initial search query string, or empty string if no data available.
 */
export function getInitialSearchQuery(
  book: Book | null,
  formData?: BookUpdate | null,
): string {
  // Priority 1: Title (from form data or book)
  const title = formData?.title?.trim() || book?.title?.trim();
  if (title) {
    return title;
  }

  // Priority 2: Series name (from form data or book)
  const seriesName = formData?.series_name?.trim() || book?.series?.trim();
  if (seriesName) {
    return seriesName;
  }

  // Priority 3: Author name (from form data or book)
  const authorNames = formData?.author_names || book?.authors;
  if (authorNames && authorNames.length > 0 && authorNames[0]) {
    return authorNames[0].trim();
  }

  return "";
}
