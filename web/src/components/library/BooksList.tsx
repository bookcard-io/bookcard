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
import { useCallback } from "react";
import { useBookRating } from "@/hooks/useBookRating";
import { useBooksNavigationData } from "@/hooks/useBooksNavigationData";
import { useBooksViewData } from "@/hooks/useBooksViewData";
import { useInfiniteScrollVirtualizer } from "@/hooks/useInfiniteScrollVirtualizer";
import type { Book } from "@/types/book";
import { BookListItem } from "./BookListItem";
import { BooksViewEmpty } from "./BooksViewEmpty";
import { BooksViewError } from "./BooksViewError";
import { BooksViewLoading } from "./BooksViewLoading";
import { BooksViewStatus } from "./BooksViewStatus";
import { ListHeader } from "./ListHeader";
import { ShelfFilterInfoBox } from "./ShelfFilterInfoBox";
import { ColumnSelectorButton } from "./widgets/ColumnSelectorButton";
import type { FilterValues } from "./widgets/FiltersPanel";

export interface BooksListProps {
  /** Callback fired when a book item is clicked. */
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
 * Books list component for displaying a paginated list of books.
 *
 * Manages data fetching via useLibraryBooks hook and renders BookListItem components.
 * Follows SOC by separating data fetching (hook) from presentation (component).
 */
export function BooksList({
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
}: BooksListProps) {
  // Fetch and manage books data (SRP: data concerns separated)
  const {
    uniqueBooks,
    isLoading,
    error,
    total,
    loadMore,
    hasMore,
    removeBook,
    updateBook: updateBookLocal,
  } = useBooksViewData({
    filters,
    searchQuery,
    shelfId,
    sortBy,
    sortOrder,
    pageSize,
    full: true, // Always fetch full details for list view to support additional columns
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

  // Virtualizer for efficient rendering of large lists
  const rowVirtualizer = useVirtualizer({
    count: hasMore ? uniqueBooks.length + 1 : uniqueBooks.length,
    // Use the main page scroll container defined in PageLayout so that
    // virtual rows respond to the actual scrollable area, not window scroll.
    getScrollElement: () =>
      typeof document !== "undefined"
        ? (document.querySelector(
            '[data-page-scroll-container="true"]',
          ) as HTMLElement | null)
        : null,
    estimateSize: () => 60, // Estimated height for a list item (will be measured dynamically)
    overscan: 5, // Render 5 extra items above and below viewport
    // Always measure actual DOM height so vertical offsets are accurate
    measureElement: (element) => element?.getBoundingClientRect().height,
  });

  // Infinite scroll: load more when scrolling near the end (SRP: scroll concerns separated)
  useInfiniteScrollVirtualizer({
    virtualizer: rowVirtualizer,
    itemCount: uniqueBooks.length,
    hasMore: hasMore ?? false,
    isLoading,
    loadMore,
    threshold: 5, // within 5 items of the end
  });

  // Handle deletion initiated from an item: remove locally from list
  const handleBookDeleted = useCallback(
    (bookId: number) => {
      removeBook?.(bookId);
    },
    [removeBook],
  );

  // Handle rating change: update via API and local state (SRP: rating concerns separated)
  const { updateRating: handleRatingChange } = useBookRating({
    onOptimisticUpdate: useCallback(
      (bookId: number, rating: number | null) => {
        updateBookLocal(bookId, { rating });
      },
      [updateBookLocal],
    ),
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
        actions={<ColumnSelectorButton />}
        disableSticky
      />
      {shelfId && <ShelfFilterInfoBox />}
      <div className="flex flex-col px-8">
        <ListHeader allBooks={uniqueBooks} />
        <div className="relative w-full">
          <div
            className="relative w-full"
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const isLoaderRow = virtualRow.index > uniqueBooks.length - 1;
              const book = uniqueBooks[virtualRow.index];

              if (isLoaderRow) {
                return (
                  <div
                    key={`loader-${virtualRow.index}`}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    {hasMore ? (
                      <div className="p-4 px-8 text-center text-sm text-text-a40">
                        Loading more books...
                      </div>
                    ) : (
                      <div className="p-4 px-8 text-center text-sm text-text-a40">
                        No more books to load
                      </div>
                    )}
                  </div>
                );
              }

              if (!book) {
                return null;
              }

              return (
                <div
                  key={book.id}
                  data-index={virtualRow.index}
                  ref={rowVirtualizer.measureElement}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  <BookListItem
                    book={book}
                    allBooks={uniqueBooks}
                    onClick={onBookClick}
                    onEdit={onBookEdit}
                    onBookDeleted={handleBookDeleted}
                    onRatingChange={handleRatingChange}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
