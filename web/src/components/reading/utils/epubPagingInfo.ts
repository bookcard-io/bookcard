// Copyright (C) 2025 khoa and others
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

import type { NavItem, Rendition } from "epubjs";
import type { PagingInfo } from "../ReaderControls";

/**
 * Calculate paging information from rendition location and TOC.
 *
 * Follows SRP by focusing solely on paging info calculation.
 * Follows DRY by centralizing paging calculation logic.
 *
 * Parameters
 * ----------
 * rendition : Rendition
 *     EPUB.js rendition instance.
 * toc : NavItem[]
 *     Table of contents items.
 *
 * Returns
 * -------
 * PagingInfo | null
 *     Paging information, or null if unavailable.
 */
export function calculatePagingInfo(
  rendition: Rendition,
  toc: NavItem[],
): PagingInfo | null {
  if (toc.length === 0) {
    return null;
  }

  try {
    const { displayed, href } = rendition.location.start;
    if (!displayed) {
      return null;
    }

    // Try exact match first, then try matching by normalizing hrefs
    let chapter = toc.find((item) => item.href === href);
    if (!chapter && href) {
      // Try matching by normalizing both hrefs (remove leading slashes, decode)
      const normalizedHref = decodeURIComponent(href.replace(/^\/+/, ""));
      chapter = toc.find((item) => {
        const normalizedItemHref = decodeURIComponent(
          item.href.replace(/^\/+/, ""),
        );
        return normalizedItemHref === normalizedHref;
      });
    }

    return {
      currentPage: displayed.page,
      totalPages: displayed.total,
      chapterLabel: chapter?.label,
      chapterTotalPages: chapter ? displayed.total : undefined,
    };
  } catch {
    // Location might not be ready yet, silently ignore
    return null;
  }
}
