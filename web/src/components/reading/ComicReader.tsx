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
import { useReadingSettingsContext } from "@/contexts/ReadingSettingsContext";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import { useReadingSession } from "@/hooks/useReadingSession";
import { cn } from "@/libs/utils";
import { getThemeColors } from "@/utils/readingTheme";
import { ContinuousComicView } from "./comic/ContinuousComicView";
import { PagedComicView } from "./comic/PagedComicView";
import { WebtoonComicView } from "./comic/WebtoonComicView";
import { useComicNavigation } from "./hooks/useComicNavigation";
import { useComicPages } from "./hooks/useComicPages";
import type { PagingInfo } from "./ReaderControls";

export type ComicReadingMode = "paged" | "continuous" | "webtoon";
export type ComicReadingDirection = "ltr" | "rtl" | "vertical";

/**
 * Status message component for reader states.
 *
 * Displays loading or error messages with consistent styling.
 * Follows DRY principle by centralizing status display logic.
 *
 * Parameters
 * ----------
 * message : string
 *     Message to display.
 * backgroundColor : string
 *     Background color for the status message.
 * className : string, optional
 *     Additional CSS classes.
 */
function ReaderStatusMessage({
  message,
  backgroundColor,
  className,
}: {
  message: string;
  backgroundColor: string;
  className?: string;
}) {
  return (
    <div
      className={cn("flex items-center justify-center p-8", className)}
      style={{ backgroundColor }}
    >
      <span className="text-text-a40">{message}</span>
    </div>
  );
}

export interface ComicReaderProps {
  /** Book ID. */
  bookId: number;
  /** Book format (CBZ, CBR, CB7, CBC). */
  format: string;
  /** Callback to register jump to progress handler. */
  onJumpToProgress?: (handler: ((progress: number) => void) | null) => void;
  /** Callback when paging info changes. */
  onPagingInfoChange?: (info: PagingInfo | null) => void;
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
  onJumpToProgress,
  onPagingInfoChange,
  className,
}: ComicReaderProps) {
  const { readingMode, readingDirection, spreadMode, zoomLevel, pageColor } =
    useReadingSettingsContext();

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
  const { isLoading: pagesLoading, totalPages } = useComicPages({
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

  // Shared page change handler for continuous and webtoon modes
  const handlePageChange = useCallback(
    (page: number, _total: number, _pageProgress: number) => {
      // Update navigation state to keep it in sync
      // This will trigger the onPageChange callback defined in useComicNavigation
      // which handles the progress update
      navigation.goToPage(page);
    },
    [navigation],
  );

  // Register jump handler
  useEffect(() => {
    if (onJumpToProgress) {
      onJumpToProgress(navigation.jumpToProgress);
    }
  }, [onJumpToProgress, navigation.jumpToProgress]);

  // Update paging info
  useEffect(() => {
    if (onPagingInfoChange) {
      onPagingInfoChange({
        currentPage: navigation.currentPage,
        totalPages: totalPages,
      });
    }
  }, [navigation.currentPage, totalPages, onPagingInfoChange]);

  // Calculate theme colors
  const { backgroundColor } = getThemeColors(pageColor);

  if (pagesLoading) {
    return (
      <ReaderStatusMessage
        message="Loading comic pages..."
        backgroundColor={backgroundColor}
        className={className}
      />
    );
  }

  if (totalPages === 0) {
    return (
      <ReaderStatusMessage
        message="No pages found in comic."
        backgroundColor={backgroundColor}
        className={className}
      />
    );
  }

  // Component registry for reading modes (OCP pattern)
  // Adding new reading modes only requires adding to this registry
  // Using switch statement for type safety and better OCP compliance
  const baseViewProps = {
    bookId,
    format,
    totalPages,
    zoomLevel,
    className: "h-full w-full",
  } as const;

  // Render based on reading mode using component registry pattern
  const renderView = () => {
    switch (readingMode) {
      case "paged": {
        return (
          <PagedComicView
            {...baseViewProps}
            currentPage={navigation.currentPage}
            onPageChange={navigation.goToPage}
            canGoNext={navigation.canGoNext}
            canGoPrevious={navigation.canGoPrevious}
            onNext={navigation.goToNext}
            onPrevious={navigation.goToPrevious}
            spreadMode={spreadMode}
            readingDirection={
              readingDirection === "vertical" ? "ltr" : readingDirection
            }
          />
        );
      }
      case "continuous": {
        return (
          <ContinuousComicView
            {...baseViewProps}
            onPageChange={handlePageChange}
            onRegisterJump={navigation.registerJumpHandler}
            initialPage={progress?.page_number || null}
          />
        );
      }
      case "webtoon": {
        return (
          <WebtoonComicView
            {...baseViewProps}
            onPageChange={handlePageChange}
            onRegisterJump={navigation.registerJumpHandler}
            initialPage={progress?.page_number || null}
          />
        );
      }
      default: {
        // TypeScript exhaustiveness check
        const _exhaustive: never = readingMode;
        return (
          <ReaderStatusMessage
            message={`Unknown reading mode: ${_exhaustive}`}
            backgroundColor={backgroundColor}
            className={className}
          />
        );
      }
    }
  };

  return (
    <div className={cn("h-full w-full", className)} style={{ backgroundColor }}>
      {renderView()}
    </div>
  );
}
