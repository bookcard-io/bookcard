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

import { useCallback, useMemo } from "react";
import type { ComicPageInfo } from "./useComicPages";

export interface Spread {
  leftPage: number;
  rightPage: number | null;
  isSpread: boolean;
}

export interface UseComicSpreadsOptions {
  pages: ComicPageInfo[];
  currentPage: number;
  enabled?: boolean;
}

export interface UseComicSpreadsResult {
  currentSpread: Spread;
  isSpreadPage: (page: number) => boolean;
  getSpreadForPage: (page: number) => Spread;
}

/**
 * Hook for detecting and managing comic book spreads.
 *
 * Detects when two consecutive pages should be displayed side-by-side.
 * Uses heuristics based on page dimensions and aspect ratios.
 * Follows SRP by focusing solely on spread detection logic.
 *
 * Parameters
 * ----------
 * options : UseComicSpreadsOptions
 *     Options including page list and current page.
 *
 * Returns
 * -------
 * UseComicSpreadsResult
 *     Spread information and detection methods.
 */
export function useComicSpreads({
  pages,
  currentPage,
  enabled = true,
}: UseComicSpreadsOptions): UseComicSpreadsResult {
  // Build spread map: page number -> spread info
  const spreadMap = useMemo(() => {
    const map = new Map<number, Spread>();

    if (!enabled || pages.length === 0) {
      // If disabled or no pages, treat all as single pages
      pages.forEach((page) => {
        map.set(page.page_number, {
          leftPage: page.page_number,
          rightPage: null,
          isSpread: false,
        });
      });
      return map;
    }

    // Detect spreads based on page dimensions
    for (let i = 0; i < pages.length; i++) {
      const current = pages[i];
      if (!current) {
        continue;
      }
      const next = i + 1 < pages.length ? pages[i + 1] : null;

      // Check if current and next page form a spread
      const isSpread = next ? _isLikelySpread(current, next) : false;

      map.set(current.page_number, {
        leftPage: current.page_number,
        rightPage: isSpread && next ? next.page_number : null,
        isSpread: isSpread,
      });

      // If this is a spread, mark the next page as part of the spread
      if (isSpread && next) {
        map.set(next.page_number, {
          leftPage: current.page_number,
          rightPage: next.page_number,
          isSpread: true,
        });
      }
    }

    return map;
  }, [pages, enabled]);

  const currentSpread = useMemo(() => {
    return (
      spreadMap.get(currentPage) || {
        leftPage: currentPage,
        rightPage: null,
        isSpread: false,
      }
    );
  }, [spreadMap, currentPage]);

  const isSpreadPage = useCallback(
    (page: number) => {
      const spread = spreadMap.get(page);
      return spread?.isSpread || false;
    },
    [spreadMap],
  );

  const getSpreadForPage = useCallback(
    (page: number) => {
      return (
        spreadMap.get(page) || {
          leftPage: page,
          rightPage: null,
          isSpread: false,
        }
      );
    },
    [spreadMap],
  );

  return {
    currentSpread,
    isSpreadPage,
    getSpreadForPage,
  };
}

/**
 * Determine if two pages are likely a spread.
 *
 * Uses heuristics:
 * - Both pages have similar dimensions
 * - Pages are landscape-oriented (width > height)
 * - Pages are consecutive
 *
 * Parameters
 * ----------
 * page1 : ComicPageInfo
 *     First page.
 * page2 : ComicPageInfo
 *     Second page.
 *
 * Returns
 * -------
 * bool
 *     True if pages are likely a spread.
 */
function _isLikelySpread(page1: ComicPageInfo, page2: ComicPageInfo): boolean {
  // If dimensions are not available, assume no spread
  if (!page1.width || !page1.height || !page2.width || !page2.height) {
    return false;
  }

  // Check if both pages are landscape-oriented
  const page1Aspect = page1.width / page1.height;
  const page2Aspect = page2.width / page2.height;

  // Landscape pages (width > height) are more likely to be spreads
  const bothLandscape = page1Aspect > 1.0 && page2Aspect > 1.0;

  // Check if dimensions are similar (within 10%)
  const widthDiff =
    Math.abs(page1.width - page2.width) / Math.max(page1.width, page2.width);
  const heightDiff =
    Math.abs(page1.height - page2.height) /
    Math.max(page1.height, page2.height);
  const similarDimensions = widthDiff < 0.1 && heightDiff < 0.1;

  // Pages must be consecutive
  const consecutive = page2.page_number === page1.page_number + 1;

  return bothLandscape && similarDimensions && consecutive;
}
