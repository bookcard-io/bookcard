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
import { cn } from "@/libs/utils";
import { ComicPage } from "./ComicPage";
import { usePagedNavigation } from "./hooks/usePagedNavigation";

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
  readingDirection?: "ltr" | "rtl";
  zoomLevel?: number;
  className?: string;
  /** Number of pages to preload before and after current page (default: 3) */
  overscan?: number;
}

/**
 * Calculate which pages to preload based on current page and overscan.
 */
function getPreloadPages(
  currentPage: number,
  totalPages: number,
  overscan: number,
  spreadMode: boolean,
): number[] {
  const pages = new Set<number>();

  // Visible pages
  pages.add(currentPage);
  if (spreadMode && currentPage < totalPages) {
    pages.add(currentPage + 1);
  }

  // Overscan pages (before and after)
  const startPage = spreadMode ? currentPage : currentPage;
  for (let i = 1; i <= overscan; i++) {
    const before = startPage - i;
    const after = spreadMode ? currentPage + 1 + i : currentPage + i;

    if (before >= 1) pages.add(before);
    if (after <= totalPages) pages.add(after);
  }

  return Array.from(pages).sort((a, b) => a - b);
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
  readingDirection = "ltr",
  zoomLevel = 1.0,
  className,
  overscan = 3,
}: PagedComicViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const loadedPagesRef = useRef<Set<number>>(new Set());
  const currentPagesRef = useRef<number[]>([]);

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

  // Calculate pages to display (spread mode or single page)
  const pagesToDisplay = useMemo(
    () =>
      spreadMode && currentPage < totalPages
        ? [currentPage, currentPage + 1]
        : [currentPage],
    [currentPage, spreadMode, totalPages],
  );

  // Calculate pages to cache (3-page overscan: previous, current, next)
  const pagesToCache = useMemo(
    () => getPreloadPages(currentPage, totalPages, overscan, spreadMode),
    [currentPage, totalPages, overscan, spreadMode],
  );

  // Reset loading state when visible pages change
  useEffect(() => {
    const pagesChanged =
      currentPagesRef.current.length !== pagesToDisplay.length ||
      !currentPagesRef.current.every((p, i) => p === pagesToDisplay[i]);

    if (pagesChanged) {
      currentPagesRef.current = [...pagesToDisplay];
      loadedPagesRef.current = new Set();
      setIsLoading(true);
    }
  }, [pagesToDisplay]);

  // Track when pages load
  const handlePageLoad = useCallback(
    (pageNum: number) => {
      // Track all cached pages loading, but only show loading for visible pages
      loadedPagesRef.current.add(pageNum);

      // Check if all visible pages are now loaded
      const allLoaded = pagesToDisplay.every((p) =>
        loadedPagesRef.current.has(p),
      );

      if (allLoaded && isLoading) {
        setIsLoading(false);
      }
    },
    [pagesToDisplay, isLoading],
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
          "m-auto flex shrink-0 items-center justify-center transition-[width,height] duration-200 ease-out",
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
            onLoad={() => handlePageLoad(pageNum)}
            className={cn(
              "h-full w-full object-contain",
              spreadMode && "w-1/2",
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
              onLoad={() => handlePageLoad(pageNum)}
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
