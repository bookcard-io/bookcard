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

import type { PagingInfo } from "../ReaderControls";

/**
 * Format paging information into display text.
 *
 * Follows SRP by focusing solely on text formatting logic.
 * Follows DRY by centralizing formatting logic.
 *
 * Parameters
 * ----------
 * pagingInfo : PagingInfo | undefined
 *     Paging information to format.
 *
 * Returns
 * -------
 * string | null
 *     Formatted paging text, or null if pagingInfo is not provided.
 */
export function formatPagingText(
  pagingInfo: PagingInfo | undefined,
): string | null {
  if (!pagingInfo) {
    return null;
  }

  if (pagingInfo.chapterLabel) {
    if (pagingInfo.chapterTotalPages) {
      return `Page ${pagingInfo.currentPage} of ${pagingInfo.chapterTotalPages} of chapter: ${pagingInfo.chapterLabel}`;
    }
    return `Page ${pagingInfo.currentPage} of ${pagingInfo.totalPages} of chapter: ${pagingInfo.chapterLabel}`;
  }

  // When chapter label is not available
  return `Page ${pagingInfo.currentPage} of ${pagingInfo.totalPages} of chapter`;
}
