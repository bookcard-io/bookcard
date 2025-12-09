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

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/libs/utils";
import { ComicPage } from "./ComicPage";

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
}

/**
 * Paged comic view component.
 *
 * Displays comic pages one at a time with navigation controls.
 * Supports spread mode for two-page displays.
 * Follows SRP by focusing solely on paged display logic.
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
}: PagedComicViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(
    null,
  );
  const SWIPE_THRESHOLD = 50; // Minimum distance for swipe
  const SWIPE_TIME_THRESHOLD = 300; // Maximum time for swipe (ms)

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key) {
        case "ArrowRight":
        case " ": // Spacebar
          if (readingDirection === "ltr" && canGoNext) {
            e.preventDefault();
            onNext();
          } else if (readingDirection === "rtl" && canGoPrevious) {
            e.preventDefault();
            onPrevious();
          }
          break;
        case "ArrowLeft":
          if (readingDirection === "ltr" && canGoPrevious) {
            e.preventDefault();
            onPrevious();
          } else if (readingDirection === "rtl" && canGoNext) {
            e.preventDefault();
            onNext();
          }
          break;
        case "Home":
          e.preventDefault();
          onPageChange(1);
          break;
        case "End":
          e.preventDefault();
          onPageChange(totalPages);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [
    canGoNext,
    canGoPrevious,
    onNext,
    onPrevious,
    onPageChange,
    readingDirection,
    totalPages,
  ]);

  // Handle touch gestures
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    if (!touch) {
      return;
    }
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now(),
    };
  }, []);

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (!touchStartRef.current) {
        return;
      }

      const touch = e.changedTouches[0];
      if (!touch) {
        touchStartRef.current = null;
        return;
      }

      const deltaX = touch.clientX - touchStartRef.current.x;
      const deltaY = touch.clientY - touchStartRef.current.y;
      const deltaTime = Date.now() - touchStartRef.current.time;

      // Check if it's a quick swipe
      if (deltaTime > SWIPE_TIME_THRESHOLD) {
        touchStartRef.current = null;
        return;
      }

      const absDeltaX = Math.abs(deltaX);
      const absDeltaY = Math.abs(deltaY);

      // Determine if horizontal or vertical swipe
      if (absDeltaX > absDeltaY && absDeltaX > SWIPE_THRESHOLD) {
        // Horizontal swipe
        if (readingDirection === "ltr") {
          if (deltaX > 0 && canGoPrevious) {
            onPrevious();
          } else if (deltaX < 0 && canGoNext) {
            onNext();
          }
        } else if (readingDirection === "rtl") {
          // RTL: reversed
          if (deltaX > 0 && canGoNext) {
            onNext();
          } else if (deltaX < 0 && canGoPrevious) {
            onPrevious();
          }
        }
      } else if (absDeltaY > absDeltaX && absDeltaY > SWIPE_THRESHOLD) {
        // Vertical swipe - not used in paged mode, but handle for consistency
        // Vertical reading direction would use continuous/webtoon modes
      }

      touchStartRef.current = null;
    },
    [canGoNext, canGoPrevious, onNext, onPrevious, readingDirection],
  );

  // Handle click zones for navigation
  const handleContainerClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!containerRef.current) {
        return;
      }

      const rect = containerRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const width = rect.width;

      // Left third: previous page
      // Right third: next page
      // Middle third: no action (or could toggle UI)
      if (readingDirection === "ltr") {
        if (clickX < width / 3 && canGoPrevious) {
          onPrevious();
        } else if (clickX > (width * 2) / 3 && canGoNext) {
          onNext();
        }
      } else {
        // RTL: reversed
        if (clickX < width / 3 && canGoNext) {
          onNext();
        } else if (clickX > (width * 2) / 3 && canGoPrevious) {
          onPrevious();
        }
      }
    },
    [canGoNext, canGoPrevious, onNext, onPrevious, readingDirection],
  );

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        // Simulate click at center for keyboard navigation
        if (canGoNext) {
          onNext();
        } else if (canGoPrevious) {
          onPrevious();
        }
      }
    },
    [canGoNext, canGoPrevious, onNext, onPrevious],
  );

  // Calculate pages to display (spread mode or single page)
  const pagesToDisplay =
    spreadMode && currentPage < totalPages
      ? [currentPage, currentPage + 1]
      : [currentPage];

  return (
    <section
      ref={containerRef}
      className={cn("flex h-screen w-full overflow-auto", className)}
      onClick={handleContainerClick}
      onKeyDown={handleKeyDown}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      aria-label="Comic page viewer"
    >
      <div
        className={cn(
          "m-auto flex items-center justify-center transition-[width,height] duration-200 ease-out",
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
            onLoad={() => setIsLoading(false)}
            className={cn(
              "h-full w-full object-contain",
              spreadMode && "w-1/2",
            )}
          />
        ))}
      </div>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-surface-tonal-a0">
          <span className="text-text-a40">Loading page...</span>
        </div>
      )}
    </section>
  );
}
