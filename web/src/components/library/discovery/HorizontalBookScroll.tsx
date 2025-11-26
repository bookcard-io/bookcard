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
import { useCallback, useEffect, useRef, useState } from "react";
import { BookCard } from "@/components/library/BookCard";
import type { Book } from "@/types/book";

export interface HorizontalBookScrollProps {
  /** Title of the section. */
  title: string;
  /** Books to display. */
  books: Book[];
  /** Whether more books can be loaded. */
  hasMore?: boolean;
  /** Whether books are currently loading. */
  isLoading: boolean;
  /** Callback to load more books. */
  loadMore?: () => void;
  /** Callback when book is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback when book edit is requested. */
  onBookEdit?: (bookId: number) => void;
  /** Callback when book is deleted. */
  onBookDeleted?: (bookId: number) => void;
  /** Callback when books data changes (for navigation). */
  onBooksDataChange?: (data: {
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  }) => void;
}

/**
 * Horizontal scrolling book list component.
 *
 * Uses tanstack/react-virtual for efficient horizontal scrolling.
 * Follows SRP by handling only horizontal scroll rendering.
 * Uses IOC via callbacks.
 */
export function HorizontalBookScroll({
  title,
  books,
  hasMore = false,
  isLoading,
  loadMore,
  onBookClick,
  onBookEdit,
  onBookDeleted,
  onBooksDataChange,
}: HorizontalBookScrollProps) {
  const scrollElementRef = useRef<HTMLDivElement>(null);
  const cardWidth = 150; // Fixed card width for horizontal scroll
  const gap = 16; // Gap between cards
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // Virtualizer for horizontal scrolling
  const virtualizer = useVirtualizer({
    horizontal: true,
    count: hasMore ? books.length + 1 : books.length,
    getScrollElement: () => scrollElementRef.current,
    estimateSize: () => cardWidth + gap,
    overscan: 3,
  });

  const virtualItems = virtualizer.getVirtualItems();

  const checkScrollButtons = useCallback(() => {
    if (!scrollElementRef.current) return;

    const { scrollLeft, scrollWidth, clientWidth } = scrollElementRef.current;
    // Use a small threshold for floating point differences
    setCanScrollLeft(scrollLeft > 1);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1);
  }, []);

  // Load more when scrolling near the end
  useEffect(() => {
    if (!hasMore || isLoading || !loadMore) {
      return;
    }

    const lastItem = virtualItems[virtualItems.length - 1];
    if (!lastItem) {
      return;
    }

    // Load more if we're within 3 items of the end
    if (lastItem.index >= books.length - 3) {
      loadMore();
    }
  }, [hasMore, isLoading, loadMore, books.length, virtualItems]);

  // Notify parent of books data changes
  useEffect(() => {
    onBooksDataChange?.({
      bookIds: books.map((book) => book.id),
      loadMore,
      hasMore,
      isLoading,
    });
  }, [books, loadMore, hasMore, isLoading, onBooksDataChange]);

  // Check scroll buttons on resize, data change, and initial load
  useEffect(() => {
    checkScrollButtons();
    window.addEventListener("resize", checkScrollButtons);
    return () => window.removeEventListener("resize", checkScrollButtons);
  }, [checkScrollButtons]);

  const handleBookClick = useCallback(
    (book: Book) => {
      onBookClick?.(book);
    },
    [onBookClick],
  );

  const handleBookEdit = useCallback(
    (bookId: number) => {
      onBookEdit?.(bookId);
    },
    [onBookEdit],
  );

  const handleBookDeleted = useCallback(
    (bookId: number) => {
      onBookDeleted?.(bookId);
    },
    [onBookDeleted],
  );

  const scrollRight = useCallback(() => {
    if (scrollElementRef.current) {
      const containerWidth = scrollElementRef.current.clientWidth;
      scrollElementRef.current.scrollBy({
        left: containerWidth * 0.8, // Scroll 80% of container width
        behavior: "smooth",
      });
    }
  }, []);

  const scrollLeft = useCallback(() => {
    if (scrollElementRef.current) {
      const containerWidth = scrollElementRef.current.clientWidth;
      scrollElementRef.current.scrollBy({
        left: -(containerWidth * 0.8), // Scroll back 80% of container width
        behavior: "smooth",
      });
    }
  }, []);

  if (books.length === 0 && !isLoading) {
    return null;
  }

  const showChevrons = books.length > 19;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="m-0 font-bold text-[var(--color-text-a0)] text-xl">
          {title}
        </h2>
        {showChevrons && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={scrollLeft}
              className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-surface-a10 active:bg-surface-a20 ${
                !canScrollLeft ? "pointer-events-none invisible" : ""
              }`}
              aria-label="Scroll left"
              disabled={!canScrollLeft}
            >
              <i className="pi pi-chevron-left text-[var(--color-text-a0)]" />
            </button>
            <button
              type="button"
              onClick={scrollRight}
              className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-surface-a10 active:bg-surface-a20 ${
                !canScrollRight ? "pointer-events-none invisible" : ""
              }`}
              aria-label="Scroll right"
              disabled={!canScrollRight}
            >
              <i className="pi pi-chevron-right text-[var(--color-text-a0)]" />
            </button>
          </div>
        )}
      </div>
      <div className="h-[300px]">
        <div
          ref={scrollElementRef}
          className="scrollbar-hide h-full overflow-x-auto overflow-y-hidden"
          style={{
            scrollbarWidth: "none", // Firefox
            msOverflowStyle: "none", // IE/Edge
          }}
          onScroll={checkScrollButtons}
        >
          <style jsx>{`
            .scrollbar-hide::-webkit-scrollbar {
              display: none;
            }
          `}</style>
          <div
            style={{
              width: `${virtualizer.getTotalSize()}px`,
              height: "100%",
              position: "relative",
            }}
          >
            {virtualItems.map((virtualItem) => {
              const index = virtualItem.index;
              if (index >= books.length) {
                // Loading indicator at the end
                return (
                  <div
                    key="loading"
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: `${virtualItem.size}px`,
                      height: "100%",
                      transform: `translateX(${virtualItem.start}px)`,
                    }}
                    className="flex items-center justify-center"
                  >
                    <div className="text-[var(--color-text-a30)] text-sm">
                      Loading...
                    </div>
                  </div>
                );
              }

              const book = books[index];
              if (!book) {
                return null;
              }
              return (
                <div
                  key={book.id}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: `${virtualItem.size}px`,
                    height: "100%",
                    transform: `translateX(${virtualItem.start}px)`,
                  }}
                >
                  <div className="flex h-full flex-col pr-4">
                    <BookCard
                      book={book}
                      allBooks={books}
                      onClick={handleBookClick}
                      onEdit={handleBookEdit}
                      onBookDeleted={handleBookDeleted}
                      showSelection={false}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
