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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export interface ImageDimensions {
  width: number;
  height: number;
}

export type SpreadHeuristic = (
  d1: ImageDimensions,
  d2: ImageDimensions,
) => boolean;

/**
 * Default heuristic for detecting "spread" (two-page) layout.
 *
 * Notes
 * -----
 * - Requires both pages to be landscape-ish (aspect > 1.0)
 * - Requires similar pixel dimensions (within 10%)
 */
export function defaultSpreadHeuristic(
  d1: ImageDimensions,
  d2: ImageDimensions,
): boolean {
  const page1Aspect = d1.width / d1.height;
  const page2Aspect = d2.width / d2.height;

  const bothLandscape = page1Aspect > 1.0 && page2Aspect > 1.0;

  const widthDiff =
    Math.abs(d1.width - d2.width) / Math.max(d1.width, d2.width);
  const heightDiff =
    Math.abs(d1.height - d2.height) / Math.max(d1.height, d2.height);
  const similarDimensions = widthDiff < 0.1 && heightDiff < 0.1;

  return bothLandscape && similarDimensions;
}

export interface UseSpreadDetectionOptions {
  enabled: boolean;
  /**
   * A key that changes when the underlying book/source changes.
   *
   * Notes
   * -----
   * This is used to clear any cached per-page dimensions so spread detection
   * doesn't leak across books or formats.
   */
  bookKey: string;
  currentPage: number;
  totalPages: number;
  heuristic?: SpreadHeuristic;
}

export interface UseSpreadDetectionResult {
  effectiveSpreadMode: boolean;
  onPageDimensions: (pageNumber: number, dims: ImageDimensions) => void;
}

/**
 * Manage spread detection and per-page dimension caching.
 *
 * Notes
 * -----
 * This hook intentionally does **not** clear caches on initial mount (the cache
 * already starts empty). It only clears when `bookKey` changes, which avoids
 * surprising "clear-after-learn" races in tests and keeps the component logic
 * focused on rendering (SOC/SRP).
 */
export function useSpreadDetection({
  enabled,
  bookKey,
  currentPage,
  totalPages,
  heuristic = defaultSpreadHeuristic,
}: UseSpreadDetectionOptions): UseSpreadDetectionResult {
  const dimsByPageRef = useRef<Map<number, ImageDimensions>>(new Map());
  const [_version, setVersion] = useState(0);
  const prevBookKeyRef = useRef(bookKey);

  useEffect(() => {
    if (prevBookKeyRef.current === bookKey) {
      return;
    }
    prevBookKeyRef.current = bookKey;
    dimsByPageRef.current = new Map();
    setVersion((v) => v + 1);
  }, [bookKey]);

  const onPageDimensions = useCallback(
    (pageNumber: number, dims: ImageDimensions) => {
      const existing = dimsByPageRef.current.get(pageNumber);
      if (
        existing &&
        existing.width === dims.width &&
        existing.height === dims.height
      ) {
        return;
      }
      dimsByPageRef.current.set(pageNumber, dims);
      setVersion((v) => v + 1);
    },
    [],
  );

  const effectiveSpreadMode = useMemo(() => {
    if (!enabled || currentPage >= totalPages) {
      return false;
    }
    const d1 = dimsByPageRef.current.get(currentPage);
    const d2 = dimsByPageRef.current.get(currentPage + 1);
    if (!d1 || !d2) {
      return false;
    }
    return heuristic(d1, d2);
  }, [enabled, currentPage, totalPages, heuristic]);

  return { effectiveSpreadMode, onPageDimensions };
}
