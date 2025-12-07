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
import { useEffect, useRef, useState } from "react";
import { cn } from "@/libs/utils";
import { ComicPage } from "./ComicPage";

export interface WebtoonComicViewProps {
  bookId: number;
  format: string;
  totalPages: number;
  onPageChange: (page: number, totalPages: number, progress: number) => void;
  onRegisterJump?: (handler: (progress: number) => void) => void;
  zoomLevel?: number;
  className?: string;
}

/**
 * Webtoon-style comic view component.
 *
 * Displays comic pages in an infinite vertical scroll.
 * Pages are loaded as the user scrolls down.
 * Follows SRP by focusing solely on webtoon display logic.
 *
 * Parameters
 * ----------
 * props : WebtoonComicViewProps
 *     Component props including page navigation and display options.
 */
export function WebtoonComicView({
  bookId,
  format,
  totalPages,
  onPageChange,
  onRegisterJump,
  zoomLevel = 1.0,
  className,
}: WebtoonComicViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const rowVirtualizer = useVirtualizer({
    count: totalPages,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 800,
    overscan: 5, // Higher overscan for smoother webtoon scrolling
  });

  // Handle jump registration
  useEffect(() => {
    if (onRegisterJump) {
      onRegisterJump((progress) => {
        const targetPage = Math.max(
          1,
          Math.min(Math.ceil(progress * totalPages), totalPages),
        );
        rowVirtualizer.scrollToIndex(targetPage - 1, { align: "start" });
      });
    }
  }, [onRegisterJump, totalPages, rowVirtualizer]);

  // Track which page is currently in view
  const virtualItems = rowVirtualizer.getVirtualItems();

  useEffect(() => {
    if (!containerRef.current || virtualItems.length === 0) {
      return;
    }

    const container = containerRef.current;
    const containerHeight = container.clientHeight;
    const scrollTop = container.scrollTop;
    const viewportCenterOffset = scrollTop + containerHeight / 2;

    let closestPage = currentPage;
    let closestDistance = Infinity;

    for (const item of virtualItems) {
      const itemCenter = (item.start + item.end) / 2;
      const distance = Math.abs(viewportCenterOffset - itemCenter);

      if (distance < closestDistance) {
        closestDistance = distance;
        closestPage = item.index + 1;
      }
    }

    if (closestPage !== currentPage) {
      setCurrentPage(closestPage);
      const progress = closestPage / totalPages;
      onPageChange(closestPage, totalPages, progress);
    }
  }, [virtualItems, currentPage, totalPages, onPageChange]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "h-screen w-full overflow-x-auto overflow-y-auto",
        className,
      )}
    >
      <div
        className="relative mx-auto flex flex-col items-center transition-[width] duration-200 ease-out"
        style={{
          width: `${zoomLevel * 50}%`,
          height: `${rowVirtualizer.getTotalSize()}px`,
        }}
      >
        {virtualItems.map((virtualRow) => (
          <div
            key={virtualRow.key}
            data-index={virtualRow.index}
            ref={rowVirtualizer.measureElement}
            className="absolute top-0 left-0 w-full"
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
    </div>
  );
}
