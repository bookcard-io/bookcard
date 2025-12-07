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

import { useCallback, useEffect } from "react";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import { useReadingSession } from "@/hooks/useReadingSession";
import { cn } from "@/libs/utils";
import { ContinuousComicView } from "./comic/ContinuousComicView";
import { PagedComicView } from "./comic/PagedComicView";
import { WebtoonComicView } from "./comic/WebtoonComicView";
import { useComicNavigation } from "./hooks/useComicNavigation";
import { useComicPages } from "./hooks/useComicPages";
import { useComicSettings } from "./hooks/useComicSettings";
import { useComicSpreads } from "./hooks/useComicSpreads";

export type ComicReadingMode = "paged" | "continuous" | "webtoon";
export type ComicReadingDirection = "ltr" | "rtl" | "vertical";

export interface ComicReaderProps {
  /** Book ID. */
  bookId: number;
  /** Book format (CBZ, CBR, CB7, CBC). */
  format: string;
  /** Reading mode. */
  readingMode?: ComicReadingMode;
  /** Reading direction. */
  readingDirection?: ComicReadingDirection;
  /** Whether to use spread mode (two pages side-by-side). */
  spreadMode?: boolean;
  /** Callback to register jump to progress handler. */
  onJumpToProgress?: (handler: ((progress: number) => void) | null) => void;
  /** Zoom level (0.5 to 3.0). */
  zoomLevel?: number;
  /** Optional className. */
  className?: string;
}

/**
 * Comic book reader component.
 *
 * Main component for reading comic books in various formats.
 * Supports multiple reading modes and navigation options.
 * Follows SRP by delegating to specialized view components.
 *
 * Parameters
 * ----------
 * props : ComicReaderProps
 *     Component props including book ID and format.
 */
export function ComicReader({
  bookId,
  format,
  readingMode: externalReadingMode,
  readingDirection: externalReadingDirection,
  spreadMode: externalSpreadMode,
  zoomLevel: externalZoomLevel,
  onJumpToProgress,
  className,
}: ComicReaderProps) {
  // Load settings from localStorage (book-specific or global)
  const settings = useComicSettings({ bookId });

  // Use external props if provided, otherwise use settings
  const readingMode = externalReadingMode || settings.readingMode;
  const readingDirection =
    externalReadingDirection || settings.readingDirection;
  const spreadMode = externalSpreadMode ?? settings.spreadMode;
  const zoomLevel = externalZoomLevel || settings.zoomLevel;

  const { progress, updateProgress } = useReadingProgress({
    bookId,
    format,
    enabled: true,
  });

  // Start reading session
  useReadingSession({
    bookId,
    format,
    autoStart: true,
    autoEnd: true,
  });

  // Fetch pages
  const {
    pages,
    isLoading: pagesLoading,
    totalPages,
  } = useComicPages({
    bookId,
    format,
    enabled: true,
  });

  // Navigation
  const navigation = useComicNavigation({
    totalPages,
    initialPage: progress?.page_number || null,
    onPageChange: useCallback(
      (page: number, _total: number, pageProgress: number) => {
        updateProgress({
          book_id: bookId,
          format,
          progress: pageProgress,
          page_number: page,
          spread_mode: spreadMode,
          reading_direction: readingDirection,
        });
      },
      [bookId, format, updateProgress, spreadMode, readingDirection],
    ),
  });

  // Spread detection
  const spreads = useComicSpreads({
    pages,
    currentPage: navigation.currentPage,
    enabled: spreadMode,
  });

  // Shared page change handler for continuous and webtoon modes
  const handlePageChange = useCallback(
    (page: number, _total: number, pageProgress: number) => {
      updateProgress({
        book_id: bookId,
        format,
        progress: pageProgress,
        page_number: page,
        spread_mode: spreadMode,
        reading_direction: readingDirection,
      });
    },
    [bookId, format, updateProgress, spreadMode, readingDirection],
  );

  // Register jump handler
  useEffect(() => {
    if (onJumpToProgress) {
      onJumpToProgress(navigation.jumpToProgress);
    }
  }, [onJumpToProgress, navigation.jumpToProgress]);

  if (pagesLoading) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <span className="text-text-a40">Loading comic pages...</span>
      </div>
    );
  }

  if (totalPages === 0) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <span className="text-text-a40">No pages found in comic.</span>
      </div>
    );
  }

  // Render based on reading mode
  if (readingMode === "paged") {
    return (
      <PagedComicView
        bookId={bookId}
        format={format}
        currentPage={navigation.currentPage}
        totalPages={totalPages}
        onPageChange={navigation.goToPage}
        canGoNext={navigation.canGoNext}
        canGoPrevious={navigation.canGoPrevious}
        onNext={navigation.goToNext}
        onPrevious={navigation.goToPrevious}
        spreadMode={spreads.currentSpread.isSpread && spreadMode}
        readingDirection={
          readingDirection === "vertical" ? "ltr" : readingDirection
        }
        zoomLevel={zoomLevel}
        className={className}
      />
    );
  }

  if (readingMode === "continuous") {
    return (
      <ContinuousComicView
        bookId={bookId}
        format={format}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        zoomLevel={zoomLevel}
        className={className}
      />
    );
  }

  if (readingMode === "webtoon") {
    return (
      <WebtoonComicView
        bookId={bookId}
        format={format}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        zoomLevel={zoomLevel}
        className={className}
      />
    );
  }

  return (
    <div className={cn("flex items-center justify-center p-8", className)}>
      <span className="text-text-a40">Unknown reading mode: {readingMode}</span>
    </div>
  );
}
