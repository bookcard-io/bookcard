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

import type { Book } from "@/types/book";

/**
 * Format book authors as a display string.
 *
 * Joins authors with commas, or returns "Unknown Author" if no authors.
 * Follows SRP by handling only author formatting.
 * Follows DRY by centralizing author text formatting.
 *
 * Parameters
 * ----------
 * authors : string[]
 *     List of author names.
 *
 * Returns
 * -------
 * string
 *     Formatted author string.
 */
export function formatAuthors(authors: string[]): string {
  return authors.length > 0 ? authors.join(", ") : "Unknown Author";
}

/**
 * Generate ARIA label for a book card.
 *
 * Creates an accessible label describing the book and its selection state.
 * Follows SRP by handling only label generation.
 *
 * Parameters
 * ----------
 * book : Book
 *     Book data.
 * selected : boolean
 *     Whether the book is selected.
 *
 * Returns
 * -------
 * string
 *     ARIA label string.
 */
export function getBookCardAriaLabel(book: Book, selected: boolean): string {
  const authorsText = formatAuthors(book.authors);
  return `${book.title} by ${authorsText}${selected ? " (selected)" : ""}. Click to view details.`;
}

/**
 * Generate ARIA label for a book list item.
 *
 * Creates an accessible label describing the book and its selection state.
 * Follows SRP by handling only label generation.
 * Follows DRY by reusing formatAuthors utility.
 *
 * Parameters
 * ----------
 * book : Book
 *     Book data.
 * selected : boolean
 *     Whether the book is selected.
 *
 * Returns
 * -------
 * string
 *     ARIA label string.
 */
export function getBookListItemAriaLabel(
  book: Book,
  selected: boolean,
): string {
  const authorsText = formatAuthors(book.authors);
  return `${book.title} by ${authorsText}${selected ? " (selected)" : ""}. Click to view details.`;
}
