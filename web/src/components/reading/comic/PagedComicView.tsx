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

import { useCallback, useMemo, useRef } from "react";
import { ComicPage } from "@/components/reading/comic/ComicPage";
import { usePagedNavigation } from "@/components/reading/comic/hooks/usePagedNavigation";
import { usePagedPageLoading } from "@/components/reading/comic/hooks/usePagedPageLoading";
import type { GetPreloadPages } from "@/components/reading/comic/hooks/usePreloadPages";
import { usePreloadPages } from "@/components/reading/comic/hooks/usePreloadPages";
import type {
  ImageDimensions,
  SpreadHeuristic,
} from "@/components/reading/comic/hooks/useSpreadDetection";
import { useSpreadDetection } from "@/components/reading/comic/hooks/useSpreadDetection";
import { useZoomScrollCenter } from "@/components/reading/comic/hooks/useZoomScrollCenter";
import { cn } from "@/libs/utils";

export interface PagedComicViewProps {
  bookId: number;
  format: string;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  canGoNext: boolean;
  canGoPrevious: boolean;
  onNext: () => void;
  onPrevious: () => void;
  spreadMode?: boolean;
  /**
   * Optional override for spread detection behavior.
   *
   * Notes
   * -----
   * This provides an OCP/DIP-friendly seam for experimenting with different
   * heuristics without changing the component internals.
   */
  spreadHeuristic?: SpreadHeuristic;
  readingDirection?: "ltr" | "rtl";
  zoomLevel?: number;
  className?: string;
  /** Number of pages to preload before and after current page (default: 3) */
  overscan?: number;
  /**
   * Optional override for page preloading behavior.
   *
   * Notes
   * -----
   * This provides an OCP/DIP seam for experimenting with different preloading
   * strategies without changing `PagedComicView`.
   */
  getPreloadPages?: GetPreloadPages;
}

/**
 * Paged comic view component.
 *
 * Displays comic pages one at a time with navigation controls.
 * Supports spread mode for two-page displays.
 *
 * This refactored version follows:
 * - SRP: Focuses only on rendering; navigation logic extracted to hooks
 * - SOC: Input handling separated from display logic
 * - DRY: Uses shared navigation hooks
 *
 * Parameters
 * ----------
 * props : PagedComicViewProps
 *     Component props including page navigation and display options.
 */
export function PagedComicView({
  bookId,
  format,
  currentPage,
  totalPages,
  onPageChange,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
  spreadMode = false,
  spreadHeuristic,
  readingDirection = "ltr",
  zoomLevel = 1.0,
  className,
  overscan = 3,
  getPreloadPages,
}: PagedComicViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bookKey = useMemo(() => `${bookId}:${format}`, [bookId, format]);

  useZoomScrollCenter({ containerRef, zoomLevel });

  // Use extracted navigation hook (SRP improvement)
  const { handleContainerClick, handleTouchStart, handleTouchEnd } =
    usePagedNavigation({
      containerRef,
      readingDirection,
      totalPages,
      canGoNext,
      canGoPrevious,
      onNext,
      onPrevious,
      onGoToPage: onPageChange,
    });

  const { effectiveSpreadMode, onPageDimensions } = useSpreadDetection({
    enabled: spreadMode,
    bookKey,
    currentPage,
    totalPages,
    heuristic: spreadHeuristic,
  });

  // Calculate pages to display (spread mode or single page)
  const pagesToDisplay = useMemo(
    () =>
      effectiveSpreadMode && currentPage < totalPages
        ? [currentPage, currentPage + 1]
        : [currentPage],
    [currentPage, effectiveSpreadMode, totalPages],
  );

  const pagesToCache = usePreloadPages(
    { currentPage, totalPages, overscan, spreadMode },
    getPreloadPages,
  );

  const { isLoading, onPageLoad } = usePagedPageLoading({
    bookKey,
    visiblePages: pagesToDisplay,
  });

  const handlePageDimensions = useCallback(
    (pageNum: number, dims: ImageDimensions) => {
      onPageDimensions(pageNum, dims);
    },
    [onPageDimensions],
  );

  return (
    <section
      ref={containerRef}
      className={cn("flex h-screen w-full overflow-auto", className)}
      onClick={handleContainerClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (canGoNext) {
            onNext();
          } else if (canGoPrevious) {
            onPrevious();
          }
        }
      }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      aria-label={`Comic page viewer, page ${currentPage} of ${totalPages}`}
    >
      <div
        className={cn(
          "m-auto flex shrink-0 items-center justify-center",
          spreadMode && pagesToDisplay.length === 2 && "gap-0",
        )}
        style={{
          width: `${zoomLevel * 100}%`,
          height: `${zoomLevel * 100}%`,
        }}
      >
        {pagesToDisplay.map((pageNum) => (
          <ComicPage
            key={pageNum}
            bookId={bookId}
            format={format}
            pageNumber={pageNum}
            onLoad={() => onPageLoad(pageNum)}
            onDimensions={(dims) => handlePageDimensions(pageNum, dims)}
            className={cn(
              "h-full w-full object-contain",
              effectiveSpreadMode && "w-1/2",
            )}
          />
        ))}
      </div>

      {/* Preload adjacent pages for seamless navigation (hidden) */}
      <div className="sr-only" aria-hidden="true">
        {pagesToCache
          .filter((pageNum) => !pagesToDisplay.includes(pageNum))
          .map((pageNum) => (
            <ComicPage
              key={pageNum}
              bookId={bookId}
              format={format}
              pageNumber={pageNum}
              onLoad={() => onPageLoad(pageNum)}
              onDimensions={(dims) => handlePageDimensions(pageNum, dims)}
              className="h-full w-full object-contain"
            />
          ))}
      </div>

      {/* Loading overlay - only shows when pages are initially loading */}
      {isLoading && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-surface-tonal-a0"
          aria-live="polite"
        >
          <span className="text-text-a40">Loading page...</span>
        </div>
      )}
    </section>
  );
}
