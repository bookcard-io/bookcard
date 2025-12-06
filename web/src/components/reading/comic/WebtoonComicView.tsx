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

export interface WebtoonComicViewProps {
  bookId: number;
  format: string;
  totalPages: number;
  onPageChange: (page: number, totalPages: number, progress: number) => void;
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
  className,
}: WebtoonComicViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loadedPages, setLoadedPages] = useState<Set<number>>(new Set([1]));
  const [lastVisiblePage, setLastVisiblePage] = useState(1);

  // Load more pages as user scrolls
  const loadMorePages = useCallback(() => {
    if (!containerRef.current) {
      return;
    }

    const container = containerRef.current;
    const scrollTop = container.scrollTop;
    const containerHeight = container.clientHeight;
    const scrollBottom = scrollTop + containerHeight;

    // Find the last visible page
    const pageElements = container.querySelectorAll("[data-page]");
    let newLastVisiblePage = lastVisiblePage;

    pageElements.forEach((element) => {
      const pageNum = parseInt(element.getAttribute("data-page") || "1", 10);
      const rect = element.getBoundingClientRect();
      const elementTop = rect.top + scrollTop - container.offsetTop;
      const elementBottom = elementTop + rect.height;

      if (elementBottom <= scrollBottom + 500) {
        // Load pages within 500px of viewport
        newLastVisiblePage = Math.max(newLastVisiblePage, pageNum);
      }
    });

    if (newLastVisiblePage > lastVisiblePage) {
      setLastVisiblePage(newLastVisiblePage);
      const newLoadedPages = new Set(loadedPages);
      // Load current page and next 2 pages
      for (
        let i = newLastVisiblePage;
        i <= Math.min(newLastVisiblePage + 2, totalPages);
        i++
      ) {
        newLoadedPages.add(i);
      }
      setLoadedPages(newLoadedPages);

      // Update progress
      const progress = newLastVisiblePage / totalPages;
      onPageChange(newLastVisiblePage, totalPages, progress);
    }
  }, [lastVisiblePage, loadedPages, totalPages, onPageChange]);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    loadMorePages();
  }, [loadMorePages]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    container.addEventListener("scroll", handleScroll);
    // Initial load
    loadMorePages();

    return () => {
      container.removeEventListener("scroll", handleScroll);
    };
  }, [handleScroll, loadMorePages]);

  return (
    <div
      ref={containerRef}
      className={cn("h-full w-full overflow-y-auto", className)}
    >
      <div className="flex flex-col items-center">
        {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
          <div key={pageNum} data-page={pageNum} className="w-full">
            {loadedPages.has(pageNum) && (
              <ComicPage
                bookId={bookId}
                format={format}
                pageNumber={pageNum}
                className="w-full"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
