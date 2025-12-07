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

export interface ContinuousComicViewProps {
  bookId: number;
  format: string;
  totalPages: number;
  onPageChange: (page: number, totalPages: number, progress: number) => void;
  onRegisterJump?: (handler: (progress: number) => void) => void;
  zoomLevel?: number;
  className?: string;
  config?: {
    estimatedPageHeight?: number;
    overscan?: number;
    baseWidthPercent?: number;
  };
}

export interface ContinuousComicViewHandle {
  jumpToPage: (page: number) => void;
  jumpToProgress: (progress: number) => void;
}

/**
 * Continuous comic view component.
 *
 * Displays comic pages in a vertical scroll with page snapping.
 * Users can scroll continuously through all pages.
 * Follows SRP by focusing solely on continuous display logic.
 *
 * Parameters
 * ----------
 * props : ContinuousComicViewProps
 *     Component props including page navigation and display options.
 */
export const ContinuousComicView = forwardRef<
  ContinuousComicViewHandle,
  ContinuousComicViewProps
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
    },
    ref,
  ) => {
    const containerRef = useRef<HTMLDivElement>(null);

    const rowVirtualizer = useVirtualizer({
      count: totalPages,
      getScrollElement: () => containerRef.current,
      estimateSize: () => config?.estimatedPageHeight ?? 800,
      overscan: config?.overscan ?? 3,
    });

    const virtualItems = rowVirtualizer.getVirtualItems();
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

    // Imperative handle for jumping
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

    // Backward compatibility for onRegisterJump
    useEffect(() => {
      if (onRegisterJump) {
        onRegisterJump((progress) => {
          const page = Math.ceil(progress * totalPages);
          const target = Math.max(1, Math.min(page, totalPages));
          rowVirtualizer.scrollToIndex(target - 1, { align: "start" });
        });
      }
    }, [onRegisterJump, totalPages, rowVirtualizer]);

    const baseWidth = config?.baseWidthPercent ?? 50;

    return (
      <section
        ref={containerRef}
        aria-label={`Comic reader, page ${currentPage} of ${totalPages}`}
        className={cn(
          "h-screen w-full snap-y snap-proximity overflow-x-auto overflow-y-auto",
          className,
        )}
      >
        <div
          className="relative mx-auto flex flex-col items-center transition-[width] duration-200 ease-out"
          style={{
            width: `${zoomLevel * baseWidth}%`,
            height: `${rowVirtualizer.getTotalSize()}px`,
          }}
        >
          {virtualItems.map((virtualRow) => (
            <div
              key={virtualRow.key}
              data-index={virtualRow.index}
              ref={rowVirtualizer.measureElement}
              className="absolute top-0 left-0 w-full snap-start"
              style={{
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <ComicPage
                bookId={bookId}
                format={format}
                pageNumber={virtualRow.index + 1}
                className="h-full w-full object-contain"
              />
            </div>
          ))}
        </div>
      </section>
    );
  },
);

ContinuousComicView.displayName = "ContinuousComicView";
