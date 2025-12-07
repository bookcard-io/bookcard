// Copyright (C) 2025 khoa and others
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

import { useRouter } from "next/navigation";
import { useMemo } from "react";
import { BookCard } from "@/components/library/BookCard";
import { useBooks } from "@/hooks/useBooks";
import { ThemeSettingsPanel } from "./components/ThemeSettingsPanel";

export interface ReadingSeriesPanelProps {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
  /** Name of the series to display. */
  seriesName: string | null;
  /** ID of the current book. */
  currentBookId: number;
  /** Optional className. */
  className?: string;
}

/**
 * Slide-out series panel for the reading page.
 *
 * Displays books in the same series, allowing navigation.
 *
 * Follows SRP by delegating to specialized components.
 * Follows SOC by separating concerns into components and hooks.
 * Follows IOC by accepting callbacks as props.
 * Follows DRY by reusing shared components.
 */
export function ReadingSeriesPanel({
  isOpen,
  onClose,
  seriesName,
  currentBookId,
  className,
}: ReadingSeriesPanelProps) {
  const router = useRouter();

  const { books, isLoading } = useBooks({
    enabled: isOpen && !!seriesName,
    search: seriesName ? `series:"=${seriesName}"` : undefined,
    sort_by: "series_index",
    sort_order: "asc",
    page_size: 100, // Reasonable limit for a series
  });

  // Find current book index
  const currentIndex = useMemo(() => {
    if (!books) return -1;
    return books.findIndex((b) => b.id === currentBookId);
  }, [books, currentBookId]);

  const currentBook = currentIndex >= 0 ? books[currentIndex] : null;
  const prevBook = currentIndex > 0 ? books[currentIndex - 1] : null;
  const nextBook =
    currentIndex >= 0 && currentIndex < books.length - 1
      ? books[currentIndex + 1]
      : null;

  const handleBookClick = (book: import("@/types/book").Book) => {
    // Determine the best format to use
    // Prefer EPUB, then try others, fallback to first available
    let format = "EPUB";
    if (book.formats && book.formats.length > 0) {
      const formats = book.formats;
      const hasEpub = formats.some((f) => f.format.toUpperCase() === "EPUB");
      if (!hasEpub && formats[0]) {
        format = formats[0].format.toUpperCase();
      }
    }

    router.push(`/reading/${book.id}/${format}`);
    onClose();
  };

  return (
    <ThemeSettingsPanel
      isOpen={isOpen}
      onClose={onClose}
      className={className}
      title="Series"
      ariaLabel="Series navigation"
      closeAriaLabel="Close series panel"
    >
      <div className="flex h-full flex-col gap-6">
        {/* Section 1: Current item and navigation */}
        {currentBook && (
          <div className="flex flex-col gap-3 border-surface-a20 border-b pb-6">
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm text-text-a40">
                Current Book
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={!prevBook}
                  onClick={() => prevBook && handleBookClick(prevBook)}
                  className="flex h-8 w-8 items-center justify-center rounded-full border border-surface-a20 text-text-a0 transition-colors hover:bg-surface-a10 disabled:opacity-50 disabled:hover:bg-transparent"
                  aria-label="Previous book in series"
                  title={
                    prevBook
                      ? `Previous: ${prevBook.title}`
                      : "No previous book"
                  }
                >
                  <i className="pi pi-chevron-left text-sm" />
                </button>
                <button
                  type="button"
                  disabled={!nextBook}
                  onClick={() => nextBook && handleBookClick(nextBook)}
                  className="flex h-8 w-8 items-center justify-center rounded-full border border-surface-a20 text-text-a0 transition-colors hover:bg-surface-a10 disabled:opacity-50 disabled:hover:bg-transparent"
                  aria-label="Next book in series"
                  title={nextBook ? `Next: ${nextBook.title}` : "No next book"}
                >
                  <i className="pi pi-chevron-right text-sm" />
                </button>
              </div>
            </div>

            {/* Current Book Card - minimal info */}
            <div className="flex items-start gap-3">
              {/* Reusing BookCard but simplified via props */}
              <div className="h-32 w-full">
                <BookCard
                  book={currentBook}
                  allBooks={books}
                  hideActions={true}
                  variant="compact"
                  onClick={() => {}} // Current book, no action
                />
              </div>
            </div>
          </div>
        )}

        {/* Section 2: List of all items */}
        <div className="flex flex-1 flex-col gap-3">
          <span className="font-medium text-sm text-text-a40">
            All Books ({books.length})
          </span>

          <div className="flex flex-col gap-2">
            {isLoading && (
              <div className="py-4 text-center text-sm text-text-a40">
                Loading series...
              </div>
            )}

            {!isLoading && books.length === 0 && (
              <div className="py-4 text-center text-sm text-text-a40">
                No books found in series.
              </div>
            )}

            {books.map((book) => (
              <div
                key={book.id}
                className={`h-24 w-full ${book.id === currentBookId ? "pointer-events-none opacity-50" : ""}`}
              >
                <BookCard
                  book={book}
                  allBooks={books}
                  hideActions={true}
                  variant="compact"
                  onClick={(b) => handleBookClick(b)}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </ThemeSettingsPanel>
  );
}
