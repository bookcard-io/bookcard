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
import { useReadingSettingsContext } from "@/contexts/ReadingSettingsContext";
import { useHeaderVisibility } from "@/hooks/useHeaderVisibility";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import { useReadingSession } from "@/hooks/useReadingSession";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/libs/utils";
import { ComicReader } from "./ComicReader";
import { HeaderTriggerZone } from "./components/HeaderTriggerZone";
import { EPUBReader, type SearchResult } from "./EPUBReader";
import { PDFReader } from "./PDFReader";
import type { PagingInfo } from "./ReaderControls";
import { ReaderControls } from "./ReaderControls";

export interface EBookReaderProps {
  /** Book ID. */
  bookId: number;
  /** Book format (EPUB, PDF, etc.). */
  format: string;
  /** Callback to register TOC toggle handler. Receives a function that toggles TOC. */
  onTocToggle?: (handler: (() => void) | null) => void;
  /** Callback when locations are ready (for EPUB). */
  onLocationsReadyChange?: (ready: boolean) => void;
  /** Search query to search for in the book. */
  searchQuery?: string;
  /** Callback when search results are available. */
  onSearchResults?: (results: SearchResult[]) => void;
  /** Callback to register jump to CFI handler. */
  onJumpToCfi?: (handler: ((cfi: string) => void) | null) => void;
  /** Optional className. */
  className?: string;
}

/**
 * E-book reader component wrapper.
 *
 * Handles format detection (EPUB vs PDF) and manages reading session lifecycle.
 * Integrates progress tracking and reader controls.
 * Follows SRP by delegating to specialized reader components.
 *
 * Parameters
 * ----------
 * props : EBookReaderProps
 *     Component props including book ID and format.
 */
export function EBookReader({
  bookId,
  format,
  onTocToggle,
  onLocationsReadyChange,
  searchQuery,
  onSearchResults,
  onJumpToCfi,
  className,
}: EBookReaderProps) {
  const { theme } = useTheme();

  const { pageColor } = useReadingSettingsContext();

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const { progress, updateProgress } = useReadingProgress({
    bookId,
    format,
    enabled: true,
  });

  // Local progress state to reflect actual reading position
  // This ensures the progress bar updates when navigating to persisted location
  const [currentProgress, setCurrentProgress] = useState(
    progress?.progress || 0,
  );

  // Start reading session (auto-managed by hook)
  useReadingSession({
    bookId,
    format,
    autoStart: true,
    autoEnd: true,
  });

  const bookUrl = useMemo(
    () => `/api/books/${bookId}/download/${format}`,
    [bookId, format],
  );

  const isEPUB = format.toUpperCase() === "EPUB";
  const isPDF = format.toUpperCase() === "PDF";
  const isComic = ["CBZ", "CBR", "CB7", "CBC"].includes(format.toUpperCase());

  // For EPUB, locations need to be generated, so start as false
  // For PDF, locations are ready immediately, so start as true
  // For comics, locations are ready immediately (page-based)
  const [areLocationsReady, setAreLocationsReady] = useState(!isEPUB);

  // Track paging information for EPUB
  const [pagingInfo, setPagingInfo] = useState<PagingInfo | null>(null);

  // Footer visibility logic
  const {
    isVisible: isFooterVisible,
    handleMouseEnter: handleFooterMouseEnter,
    handleMouseLeave: handleFooterMouseLeave,
  } = useHeaderVisibility(areLocationsReady);

  // Debounced progress update
  const debouncedUpdateProgress = useCallback(
    (newProgress: number, cfi?: string, pageNumber?: number) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      debounceTimerRef.current = setTimeout(() => {
        updateProgress({
          book_id: bookId,
          format,
          progress: newProgress,
          cfi: cfi || null,
          page_number: pageNumber || null,
        });
      }, 1000);
    },
    [bookId, format, updateProgress],
  );

  const handleLocationChange = useCallback(
    (cfi: string, newProgress: number, skipBackendUpdate = false) => {
      // During initial load, only update progress if it's a valid non-zero value
      // This prevents overwriting persisted progress with 0 during location generation
      if (skipBackendUpdate) {
        // Only update if we have a valid progress value (not 0 from failed calculation)
        if (newProgress > 0) {
          setCurrentProgress(newProgress);
        }
        // Don't update backend during initial load
      } else {
        // Normal operation: update progress and backend
        setCurrentProgress(newProgress);
        debouncedUpdateProgress(newProgress, cfi);
      }
    },
    [debouncedUpdateProgress],
  );

  const handlePageChange = useCallback(
    (page: number, _totalPages: number, newProgress: number) => {
      setCurrentProgress(newProgress);
      debouncedUpdateProgress(newProgress, undefined, page);
    },
    [debouncedUpdateProgress],
  );

  const jumpToProgressRef = useRef<((progress: number) => void) | null>(null);
  const jumpToCfiRef = useRef<((cfi: string) => void) | null>(null);
  const tocToggleRef = useRef<(() => void) | null>(null);

  // Register TOC toggle handler with parent
  useEffect(() => {
    if (onTocToggle) {
      onTocToggle(tocToggleRef.current);
    }
  }, [onTocToggle]);

  // Register jump to CFI handler with parent
  useEffect(() => {
    if (onJumpToCfi) {
      onJumpToCfi(jumpToCfiRef.current);
    }
  }, [onJumpToCfi]);

  // Notify parent when locations are ready
  useEffect(() => {
    if (onLocationsReadyChange) {
      onLocationsReadyChange(areLocationsReady);
    }
  }, [areLocationsReady, onLocationsReadyChange]);

  const handleProgressChange = useCallback((newProgress: number) => {
    // Jump to position in reader immediately
    // The jump handler will trigger onLocationChange with the CFI,
    // which will update the backend with both progress and CFI
    if (jumpToProgressRef.current) {
      jumpToProgressRef.current(newProgress);
    }
    // Note: We don't call debouncedUpdateProgress here because
    // the jump handler will trigger onLocationChange which includes the CFI
    // This ensures the backend update has the correct CFI data
  }, []);

  // Update currentProgress when persisted progress is loaded
  // This handles the case where progress data loads after component mount
  useEffect(() => {
    const progressValue = progress?.progress;
    if (progressValue !== undefined) {
      setCurrentProgress(progressValue);
    }
  }, [progress]);

  if (!isEPUB && !isPDF && !isComic) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <span className="text-text-a40">
          Format {format} is not supported for reading.
        </span>
      </div>
    );
  }

  return (
    <div className={cn("relative h-screen w-full overflow-hidden", className)}>
      <div className="h-full w-full">
        {isEPUB && (
          <EPUBReader
            url={bookUrl}
            initialCfi={progress?.cfi || null}
            onLocationChange={handleLocationChange}
            onJumpToProgress={(handler) => {
              jumpToProgressRef.current = handler;
            }}
            onTocToggle={(handler) => {
              tocToggleRef.current = handler;
            }}
            onLocationsReadyChange={setAreLocationsReady}
            onPagingInfoChange={setPagingInfo}
            searchQuery={searchQuery}
            onSearchResults={onSearchResults}
            onJumpToCfi={(handler) => {
              jumpToCfiRef.current = handler;
            }}
            className="h-full w-full"
          />
        )}
        {isPDF && (
          <PDFReader
            url={bookUrl}
            initialPage={progress?.page_number || null}
            onPageChange={handlePageChange}
            onJumpToProgress={(handler) => {
              jumpToProgressRef.current = handler;
            }}
            zoom={1.0}
            theme={theme}
            className="h-full w-full"
          />
        )}
        {isComic && (
          <ComicReader
            bookId={bookId}
            format={format}
            onJumpToProgress={(handler) => {
              jumpToProgressRef.current = handler;
            }}
            className="h-full w-full"
          />
        )}
      </div>

      <HeaderTriggerZone
        isVisible={isFooterVisible}
        onMouseEnter={handleFooterMouseEnter}
        position="bottom"
      />

      {/* biome-ignore lint/a11y/noStaticElementInteractions: Footer uses hover for show/hide, not keyboard interaction */}
      <div
        onMouseEnter={handleFooterMouseEnter}
        onMouseLeave={handleFooterMouseLeave}
        className={cn(
          "fixed right-0 bottom-0 left-0 z-[800] transition-transform duration-300 ease-in-out",
          "flex min-h-[5rem] flex-col justify-end",
          isFooterVisible ? "translate-y-0" : "translate-y-full",
        )}
      >
        <ReaderControls
          progress={currentProgress}
          onProgressChange={handleProgressChange}
          isProgressDisabled={isEPUB && !areLocationsReady}
          isLoadingEpubData={isEPUB && !areLocationsReady}
          pageColor={pageColor}
          pagingInfo={pagingInfo || undefined}
        />
      </div>
    </div>
  );
}
