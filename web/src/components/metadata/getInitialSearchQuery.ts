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

import type { BookUpdateFormData } from "@/schemas/bookUpdateSchema";
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
 * formData : BookUpdate | BookUpdateFormData | null | undefined
 *     Optional form data that takes priority over book data.
 *
 * Returns
 * -------
 * string
 *     Initial search query string, or empty string if no data available.
 */
export function getInitialSearchQuery(
  book: Book | null,
  formData?: BookUpdate | BookUpdateFormData | null,
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
