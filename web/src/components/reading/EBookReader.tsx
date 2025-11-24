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
import { useReadingProgress } from "@/hooks/useReadingProgress";
import { useReadingSession } from "@/hooks/useReadingSession";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/libs/utils";
import { EPUBReader } from "./EPUBReader";
import { PDFReader } from "./PDFReader";
import { ReaderControls } from "./ReaderControls";
import type { FontFamily, PageColor } from "./ReadingThemeSettings";

export interface EBookReaderProps {
  /** Book ID. */
  bookId: number;
  /** Book format (EPUB, PDF, etc.). */
  format: string;
  /** Callback to register TOC toggle handler. Receives a function that toggles TOC. */
  onTocToggle?: (handler: (() => void) | null) => void;
  /** Font family. */
  fontFamily?: FontFamily;
  /** Font size in pixels. */
  fontSize?: number;
  /** Page color theme. */
  pageColor?: PageColor;
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
  fontFamily = "Bookerly",
  fontSize: externalFontSize = 16,
  pageColor = "light",
  className,
}: EBookReaderProps) {
  const [fontSize, setFontSize] = useState(externalFontSize);
  const { theme, toggleTheme } = useTheme();

  // Sync internal fontSize state with external prop
  useEffect(() => {
    setFontSize(externalFontSize);
  }, [externalFontSize]);
  const [isFullscreen, setIsFullscreen] = useState(false);
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
      console.log("[EBookReader] handleLocationChange called:", {
        cfi,
        newProgress,
        currentProgressState: currentProgress,
        skipBackendUpdate,
      });
      setCurrentProgress(newProgress);
      console.log("[EBookReader] Updated currentProgress to:", newProgress);
      // Only update backend if not skipping (i.e., not during initial load)
      if (!skipBackendUpdate) {
        debouncedUpdateProgress(newProgress, cfi);
      } else {
        console.log("[EBookReader] Skipping backend update (initial load)");
      }
    },
    [debouncedUpdateProgress, currentProgress],
  );

  const handlePageChange = useCallback(
    (page: number, _totalPages: number, newProgress: number) => {
      setCurrentProgress(newProgress);
      debouncedUpdateProgress(newProgress, undefined, page);
    },
    [debouncedUpdateProgress],
  );

  const jumpToProgressRef = useRef<((progress: number) => void) | null>(null);
  const tocToggleRef = useRef<(() => void) | null>(null);
  const [areLocationsReady, setAreLocationsReady] = useState(true); // Default to true for PDF

  // Register TOC toggle handler with parent
  useEffect(() => {
    if (onTocToggle) {
      onTocToggle(tocToggleRef.current);
    }
  }, [onTocToggle]);

  const handleProgressChange = useCallback(
    (newProgress: number) => {
      // Jump to position in reader immediately
      if (jumpToProgressRef.current) {
        jumpToProgressRef.current(newProgress);
      }
      // Also update progress in backend (debounced)
      debouncedUpdateProgress(newProgress);
    },
    [debouncedUpdateProgress],
  );

  const handleFullscreenToggle = useCallback(() => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  const handleThemeChange = useCallback(
    (_newTheme: "light" | "dark") => {
      // Ignore the parameter and just toggle - this ensures global theme sync
      toggleTheme();
    },
    [toggleTheme],
  );

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Update currentProgress when persisted progress is loaded
  // This handles the case where progress data loads after component mount
  useEffect(() => {
    const progressValue = progress?.progress;
    console.log("[EBookReader] Progress data changed:", {
      progressValue,
      currentProgressState: currentProgress,
      fullProgress: progress,
    });
    if (progressValue !== undefined) {
      console.log(
        "[EBookReader] Setting currentProgress from API:",
        progressValue,
      );
      setCurrentProgress(progressValue);
    }
  }, [progress, currentProgress]);

  if (!isEPUB && !isPDF) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <span className="text-text-a40">
          Format {format} is not supported for reading.
        </span>
      </div>
    );
  }

  return (
    <div className={cn("flex h-screen flex-col", className)}>
      <div className="flex-1 overflow-hidden">
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
            fontFamily={fontFamily}
            fontSize={fontSize}
            theme={theme}
            pageColor={pageColor}
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
      </div>
      <ReaderControls
        progress={(() => {
          console.log("[EBookReader] Rendering ReaderControls with progress:", {
            currentProgress,
            progressFromAPI: progress?.progress,
          });
          return currentProgress;
        })()}
        onProgressChange={handleProgressChange}
        isProgressDisabled={isEPUB && !areLocationsReady}
        fontSize={fontSize}
        onFontSizeChange={setFontSize}
        theme={theme}
        onThemeChange={handleThemeChange}
        pageColor={pageColor}
        isFullscreen={isFullscreen}
        onFullscreenToggle={handleFullscreenToggle}
      />
    </div>
  );
}
