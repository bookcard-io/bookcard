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

import { useVirtualizer } from "@tanstack/react-virtual";
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { cn } from "@/libs/utils";
import { ComicPage } from "./ComicPage";
import { useVisiblePage } from "./hooks/useVisiblePage";

// ============================================================================
// Types
// ============================================================================

export interface VirtualizedViewConfig {
  /** Estimated height of each page in pixels */
  estimatedPageHeight: number;
  /** Number of pages to render outside the visible area */
  overscan: number;
  /** Enable CSS scroll snapping */
  enableSnap: boolean;
}

export interface BaseVirtualizedComicViewProps {
  bookId: number;
  format: string;
  totalPages: number;
  onPageChange: (page: number, totalPages: number, progress: number) => void;
  onRegisterJump?: (handler: ((progress: number) => void) | null) => void;
  zoomLevel?: number;
  className?: string;
  /** Configuration for virtualization behavior */
  config: VirtualizedViewConfig;
  /** Initial page number to jump to on load (1-based) */
  initialPage?: number | null;
}

export interface VirtualizedComicViewHandle {
  jumpToPage: (page: number) => void;
  jumpToProgress: (progress: number) => void;
}

// ============================================================================
// Default Configurations
// ============================================================================

export const CONTINUOUS_CONFIG: VirtualizedViewConfig = {
  estimatedPageHeight: 800,
  overscan: 3,
  enableSnap: true,
};

export const WEBTOON_CONFIG: VirtualizedViewConfig = {
  estimatedPageHeight: 800,
  overscan: 5,
  enableSnap: false,
};

// ============================================================================
// Component
// ============================================================================

/**
 * Base virtualized comic view component.
 *
 * Provides shared virtualization logic for continuous and webtoon reading modes.
 * Uses @tanstack/react-virtual for efficient rendering of large page lists.
 *
 * This component follows:
 * - DRY: Shared logic for all virtualized views
 * - SRP: Focuses solely on virtualized scrolling display
 * - OCP: Config-driven behavior allows extension without modification
 * - DIP: Depends on abstractions (config object) not concrete implementations
 *
 * Parameters
 * ----------
 * props : BaseVirtualizedComicViewProps
 *     Component props including book data, callbacks, and configuration.
 * ref : VirtualizedComicViewHandle
 *     Imperative handle for programmatic navigation.
 */
export const BaseVirtualizedComicView = forwardRef<
  VirtualizedComicViewHandle,
  BaseVirtualizedComicViewProps
>(
  (
    {
      bookId,
      format,
      totalPages,
      onPageChange,
      onRegisterJump,
      zoomLevel = 1.0,
      className,
      config,
      initialPage,
    },
    ref,
  ) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const hasJumpedToInitialPageRef = useRef(false);

    // Virtualization setup
    const rowVirtualizer = useVirtualizer({
      count: totalPages,
      getScrollElement: () => containerRef.current,
      estimateSize: () => config.estimatedPageHeight,
      overscan: config.overscan,
    });

    const virtualItems = rowVirtualizer.getVirtualItems();

    // Track visible page using shared hook (DRY)
    const currentPage = useVisiblePage(containerRef, virtualItems);

    // Notify parent of page changes
    const lastReportedPageRef = useRef(currentPage);
    useEffect(() => {
      if (currentPage !== lastReportedPageRef.current) {
        lastReportedPageRef.current = currentPage;
        const progress = currentPage / totalPages;
        onPageChange(currentPage, totalPages, progress);
      }
    }, [currentPage, totalPages, onPageChange]);

    // Imperative handle for external navigation control
    useImperativeHandle(
      ref,
      () => ({
        jumpToPage: (page: number) => {
          const clamped = Math.max(1, Math.min(page, totalPages));
          rowVirtualizer.scrollToIndex(clamped - 1, { align: "start" });
        },
        jumpToProgress: (progress: number) => {
          const page = Math.ceil(progress * totalPages);
          const target = Math.max(1, Math.min(page, totalPages));
          rowVirtualizer.scrollToIndex(target - 1, { align: "start" });
        },
      }),
      [totalPages, rowVirtualizer],
    );

    // Jump to initial page on mount when available
    useEffect(() => {
      if (
        initialPage &&
        totalPages > 0 &&
        !hasJumpedToInitialPageRef.current &&
        initialPage >= 1 &&
        initialPage <= totalPages
      ) {
        hasJumpedToInitialPageRef.current = true;
        // Use setTimeout to ensure virtualizer is fully initialized
        setTimeout(() => {
          rowVirtualizer.scrollToIndex(initialPage - 1, { align: "start" });
        }, 0);
      }
    }, [initialPage, totalPages, rowVirtualizer]);

    // Backward compatibility for onRegisterJump callback pattern
    useEffect(() => {
      if (!onRegisterJump) {
        return;
      }

      onRegisterJump((progress) => {
        const page = Math.ceil(progress * totalPages);
        const target = Math.max(1, Math.min(page, totalPages));
        rowVirtualizer.scrollToIndex(target - 1, { align: "start" });
      });

      // Cleanup: unregister handler when unmounting or changing modes
      return () => {
        onRegisterJump(null);
      };
    }, [onRegisterJump, totalPages, rowVirtualizer]);

    return (
      <section
        ref={containerRef}
        aria-label={`Comic reader, page ${currentPage} of ${totalPages}`}
        className={cn(
          "h-screen w-full overflow-x-auto overflow-y-auto",
          config.enableSnap && "snap-y snap-mandatory",
          className,
        )}
      >
        <div
          className="relative mx-auto flex flex-col items-center transition-[width] duration-200 ease-out"
          style={{
            width: `${zoomLevel * 100}%`,
            height: `${rowVirtualizer.getTotalSize()}px`,
          }}
        >
          {virtualItems.map((virtualRow) => (
            <div
              key={virtualRow.key}
              data-index={virtualRow.index}
              ref={rowVirtualizer.measureElement}
              className={cn(
                "absolute top-0 left-0 flex w-full",
                config.enableSnap && "snap-start",
              )}
              style={{
                transform: `translateY(${virtualRow.start}px)`,
                height: `${zoomLevel * 100}vh`,
              }}
            >
              <ComicPage
                bookId={bookId}
                format={format}
                pageNumber={virtualRow.index + 1}
                className="mx-auto h-full w-full object-contain"
              />
            </div>
          ))}
        </div>
      </section>
    );
  },
);

BaseVirtualizedComicView.displayName = "BaseVirtualizedComicView";
