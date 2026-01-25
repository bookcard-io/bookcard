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

import { useMemo } from "react";

export interface PreloadPagesContext {
  currentPage: number;
  totalPages: number;
  /**
   * Number of pages to preload before and after current page.
   */
  overscan: number;
  /**
   * If true, we assume a spread may be shown and proactively preload adjacent
   * pages even before spread detection completes.
   */
  spreadMode: boolean;
}

export type GetPreloadPages = (ctx: PreloadPagesContext) => number[];

/**
 * Default preload policy for paged comic view.
 *
 * Notes
 * -----
 * - Always includes `currentPage`.
 * - If `spreadMode` is enabled, also includes `currentPage + 1` (when valid),
 *   even before spread detection is confirmed.
 * - Adds `overscan` pages before and after.
 *
 * Parameters
 * ----------
 * ctx : PreloadPagesContext
 *     Inputs used to determine which pages to preload.
 *
 * Returns
 * -------
 * number[]
 *     Sorted list of pages to preload (1-indexed page numbers).
 */
export const defaultGetPreloadPages: GetPreloadPages = ({
  currentPage,
  totalPages,
  overscan,
  spreadMode,
}: PreloadPagesContext): number[] => {
  const pages = new Set<number>();

  pages.add(currentPage);
  if (spreadMode && currentPage < totalPages) {
    pages.add(currentPage + 1);
  }

  for (let i = 1; i <= overscan; i++) {
    const before = currentPage - i;
    const after = spreadMode ? currentPage + 1 + i : currentPage + i;

    if (before >= 1) pages.add(before);
    if (after <= totalPages) pages.add(after);
  }

  return Array.from(pages).sort((a, b) => a - b);
};

/**
 * Compute a stable list of pages to preload.
 *
 * Notes
 * -----
 * This is a thin memoizing wrapper around a preload policy function. It creates
 * an OCP/DIP seam so callers can inject alternative policies without modifying
 * the view component.
 */
export function usePreloadPages(
  ctx: PreloadPagesContext,
  getPreloadPages: GetPreloadPages = defaultGetPreloadPages,
): number[] {
  const { currentPage, totalPages, overscan, spreadMode } = ctx;
  return useMemo(
    () =>
      getPreloadPages({
        currentPage,
        totalPages,
        overscan,
        spreadMode,
      }),
    [getPreloadPages, currentPage, totalPages, overscan, spreadMode],
  );
}
