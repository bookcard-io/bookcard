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
import { useCallback, useMemo, useRef } from "react";
import { useBooksNavigationData } from "@/hooks/useBooksNavigationData";
import { useBooksViewData } from "@/hooks/useBooksViewData";
import { useInfiniteScrollVirtualizer } from "@/hooks/useInfiniteScrollVirtualizer";
import { useResponsiveGridLayout } from "@/hooks/useResponsiveGridLayout";
import type { Book } from "@/types/book";
import { BookCard } from "./BookCard";
import { BooksViewEmpty } from "./BooksViewEmpty";
import { BooksViewError } from "./BooksViewError";
import { BooksViewLoading } from "./BooksViewLoading";
import { BooksViewStatus } from "./BooksViewStatus";
import { ShelfFilterInfoBox } from "./ShelfFilterInfoBox";
import type { FilterValues } from "./widgets/FiltersPanel";

export interface BooksGridProps {
  /** Callback fired when a book card is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback fired when a book edit button is clicked. */
  onBookEdit?: (bookId: number) => void;
  /** Search query to filter books. */
  searchQuery?: string;
  /** Filter values for advanced filtering. */
  filters?: FilterValues;
  /** Shelf ID to filter books by shelf. */
  shelfId?: number;
  /** Sort field. */
  sortBy?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sortOrder?: "asc" | "desc";
  /** Number of items per page. */
  pageSize?: number;
  /** Ref to expose methods for updating book data, cover, removing books, and adding books. */
  bookDataUpdateRef?: React.RefObject<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
    addBook?: (bookId: number) => Promise<void>;
  }>;
  /** Callback to expose book navigation data (bookIds, loadMore, hasMore, isLoading) for modal navigation. */
  onBooksDataChange?: (data: {
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  }) => void;
}

/**
 * Books grid component for displaying a paginated grid of books.
 *
 * Manages data fetching via useBooks hook and renders BookCard components.
 * Follows SOC by separating data fetching (hook) from presentation (component).
 */
export function BooksGrid({
  onBookClick,
  onBookEdit,
  searchQuery,
  filters,
  shelfId,
  sortBy,
  sortOrder,
  pageSize = 20,
  bookDataUpdateRef,
  onBooksDataChange,
}: BooksGridProps) {
  // Fetch and manage books data (SRP: data concerns separated)
  const {
    uniqueBooks,
    isLoading,
    error,
    total,
    loadMore,
    hasMore,
    removeBook,
  } = useBooksViewData({
    filters,
    searchQuery,
    shelfId,
    sortBy,
    sortOrder,
    pageSize,
    bookDataUpdateRef,
  });

  // Expose navigation data to parent (SRP: navigation concerns separated)
  useBooksNavigationData({
    bookIds: uniqueBooks.map((book) => book.id),
    loadMore,
    hasMore,
    isLoading,
    onBooksDataChange,
  });

  // Scroll container ref for virtualizer
  const parentRef = useRef<HTMLDivElement | null>(null);

  // Responsive grid layout shared between CSS and virtualizer math
  const { columnCount, cardWidth, gap } = useResponsiveGridLayout(parentRef);

  // Handle deletion initiated from a card: remove locally from grid
  const handleBookDeleted = useCallback(
    (bookId: number) => {
      removeBook?.(bookId);
    },
    [removeBook],
  );

  // Compute number of virtualized rows based on responsive column count
  const rowCount = useMemo(
    () => Math.max(1, Math.ceil(uniqueBooks.length / Math.max(columnCount, 1))),
    [uniqueBooks.length, columnCount],
  );

  // Estimate row height from card width and aspect ratio; refined via measureElement.
  const estimatedRowHeight = useMemo(() => {
    const coverAspectRatio = 1.5; // approximate height/width for cover
    const metadataHeight = 80; // title + authors + spacing
    const cardHeight = cardWidth * coverAspectRatio + metadataHeight;
    return cardHeight + gap;
  }, [cardWidth, gap]);

  // Virtualizer for efficient rendering of large grids (virtualizing rows).
  const rowVirtualizer = useVirtualizer({
    count: hasMore ? rowCount + 1 : rowCount,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimatedRowHeight,
    overscan: 3,
    // Always measure actual DOM height so row offsets stay accurate
    measureElement: (element) => element?.getBoundingClientRect().height,
  });

  // Infinite scroll: load more when we scroll close to the last row (SRP: scroll concerns separated)
  useInfiniteScrollVirtualizer({
    virtualizer: rowVirtualizer,
    itemCount: rowCount,
    hasMore: hasMore ?? false,
    isLoading,
    loadMore,
    threshold: 2, // within 2 rows of the end
  });

  // Error state (SRP: error display separated)
  if (error) {
    return <BooksViewError error={error} />;
  }

  // Loading state (SRP: loading display separated)
  if (isLoading && uniqueBooks.length === 0) {
    return <BooksViewLoading />;
  }

  // Empty state (SRP: empty display separated)
  if (uniqueBooks.length === 0) {
    return <BooksViewEmpty />;
  }

  return (
    <div className="w-full">
      <BooksViewStatus
        currentCount={uniqueBooks.length}
        total={total}
        hasMore={hasMore ?? false}
      />
      {shelfId && <ShelfFilterInfoBox />}
      <div className="px-8">
        <div
          ref={parentRef}
          className="relative h-[calc(100vh-215px)] w-full overflow-auto [contain:strict] [&::-webkit-scrollbar-thumb]:bg-surface-a20 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:hidden [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar]:w-2 hover:[&::-webkit-scrollbar]:block"
        >
          <div
            className="relative w-full"
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const isLoaderRow = hasMore && virtualRow.index >= rowCount;

              if (isLoaderRow) {
                return (
                  <div
                    key={`loader-${virtualRow.index}`}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      paddingBottom: `${gap}px`,
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    <div className="p-4 text-center text-sm text-text-a40">
                      {isLoading
                        ? "Loading more books..."
                        : "No more books to load"}
                    </div>
                  </div>
                );
              }

              const startIndex = virtualRow.index * columnCount;
              const endIndex = Math.min(
                startIndex + columnCount,
                uniqueBooks.length,
              );
              const rowBooks = uniqueBooks.slice(startIndex, endIndex);

              if (!rowBooks.length) {
                return null;
              }

              return (
                <div
                  key={virtualRow.index}
                  data-index={virtualRow.index}
                  ref={rowVirtualizer.measureElement}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    paddingBottom: `${gap}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  <div
                    className="flex"
                    style={{
                      gap: `${gap}px`,
                    }}
                  >
                    {rowBooks.map((book) => (
                      <div
                        key={book.id}
                        className="flex"
                        style={{
                          flex: `0 0 ${cardWidth}px`,
                          width: `${cardWidth}px`,
                        }}
                      >
                        <BookCard
                          book={book}
                          allBooks={uniqueBooks}
                          onClick={onBookClick}
                          onEdit={onBookEdit}
                          onBookDeleted={handleBookDeleted}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      {!hasMore && !isLoading && uniqueBooks.length > 0 && (
        <div className="p-4 px-8 text-center text-sm text-text-a40">
          No more books to load
        </div>
      )}
    </div>
  );
}
