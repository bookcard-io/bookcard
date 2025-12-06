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

export interface ContinuousComicViewProps {
  bookId: number;
  format: string;
  totalPages: number;
  onPageChange: (page: number, totalPages: number, progress: number) => void;
  readingDirection?: "ltr" | "rtl" | "vertical";
  className?: string;
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
export function ContinuousComicView({
  bookId,
  format,
  totalPages,
  onPageChange,
  className,
}: ContinuousComicViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [visiblePages, setVisiblePages] = useState<Set<number>>(new Set([1]));
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Track which page is currently in view
  const updateVisiblePage = useCallback(() => {
    if (!containerRef.current) {
      return;
    }

    const container = containerRef.current;
    const scrollTop = container.scrollTop;
    const containerHeight = container.clientHeight;
    const viewportCenter = scrollTop + containerHeight / 2;

    // Find the page that's closest to the viewport center
    let closestPage = 1;
    let closestDistance = Infinity;

    pageRefs.current.forEach((pageElement, pageNum) => {
      const pageTop = pageElement.offsetTop;
      const pageHeight = pageElement.offsetHeight;
      const pageCenter = pageTop + pageHeight / 2;
      const distance = Math.abs(viewportCenter - pageCenter);

      if (distance < closestDistance) {
        closestDistance = distance;
        closestPage = pageNum;
      }
    });

    // Update progress
    const progress = closestPage / totalPages;
    onPageChange(closestPage, totalPages, progress);
  }, [totalPages, onPageChange]);

  // Handle scroll events with debouncing
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const handleScroll = useCallback(() => {
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    scrollTimeoutRef.current = setTimeout(() => {
      updateVisiblePage();
    }, 100);
  }, [updateVisiblePage]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    container.addEventListener("scroll", handleScroll);
    return () => {
      container.removeEventListener("scroll", handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  // Register page refs
  const registerPageRef = useCallback(
    (pageNum: number, element: HTMLDivElement | null) => {
      if (element) {
        pageRefs.current.set(pageNum, element);
      } else {
        pageRefs.current.delete(pageNum);
      }
    },
    [],
  );

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const newVisiblePages = new Set(visiblePages);
        entries.forEach((entry) => {
          const pageNum = parseInt(
            entry.target.getAttribute("data-page") || "1",
            10,
          );
          if (entry.isIntersecting) {
            newVisiblePages.add(pageNum);
          } else {
            newVisiblePages.delete(pageNum);
          }
        });
        setVisiblePages(newVisiblePages);
      },
      {
        root: containerRef.current,
        rootMargin: "200px",
      },
    );

    pageRefs.current.forEach((element) => {
      observer.observe(element);
    });

    return () => {
      observer.disconnect();
    };
  }, [visiblePages]);

  return (
    <div
      ref={containerRef}
      className={cn("h-full w-full overflow-y-auto", className)}
    >
      <div className="flex flex-col items-center">
        {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
          <div
            key={pageNum}
            ref={(el) => registerPageRef(pageNum, el)}
            data-page={pageNum}
            className="w-full"
          >
            {visiblePages.has(pageNum) && (
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
