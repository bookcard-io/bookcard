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

export interface ReadingPageParams {
  book_id: string;
  format: string;
}

export interface ParsedReadingPageParams {
  bookId: number;
  format: string;
}

/**
 * Parses and validates reading page route parameters.
 *
 * Follows SRP by handling only parameter parsing and validation.
 * Follows SOC by separating route parameter concerns from components.
 *
 * Parameters
 * ----------
 * params : ReadingPageParams
 *     Raw route parameters from Next.js.
 *
 * Returns
 * -------
 * ParsedReadingPageParams | null
 *     Parsed and validated parameters, or null if invalid.
 */
export function parseReadingPageParams(
  params: ReadingPageParams,
): ParsedReadingPageParams | null {
  const bookId = parseInt(params.book_id, 10);
  if (Number.isNaN(bookId)) {
    return null;
  }

  const format = params.format?.toUpperCase();
  if (!format) {
    return null;
  }

  return {
    bookId,
    format,
  };
}
