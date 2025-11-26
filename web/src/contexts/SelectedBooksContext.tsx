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

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { Book } from "@/types/book";

interface SelectedBooksContextType {
  /** Set of selected book IDs. */
  selectedBookIds: Set<number>;
  /** Current array of books in the view. */
  books: Book[];
  /** Update the books array. */
  setBooks: (books: Book[]) => void;
  /** Whether a book is selected. */
  isSelected: (bookId: number) => boolean;
  /** Handle book click with multi-select support (Ctrl/Shift modifiers). */
  handleBookClick: (book: Book, books: Book[], event: React.MouseEvent) => void;
  /** Clear all selections. */
  clearSelection: () => void;
  /** Select all books. */
  selectAll: (books: Book[]) => void;
  /** Number of selected books. */
  selectedCount: number;
}

const SelectedBooksContext = createContext<
  SelectedBooksContextType | undefined
>(undefined);

/**
 * Provider for managing selected books state and current books array.
 *
 * Implements multi-select functionality with Ctrl+click (toggle) and
 * Shift+click (range selection) support.
 * Also manages the current books array for the view, allowing components
 * to publish/subscribe to books without prop drilling.
 */
export function SelectedBooksProvider({ children }: { children: ReactNode }) {
  const [selectedBookIds, setSelectedBookIds] = useState<Set<number>>(
    new Set(),
  );
  const [books, setBooks] = useState<Book[]>([]);
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(
    null,
  );

  const handleSetBooks = useCallback((newBooks: Book[]) => {
    setBooks(newBooks);
  }, []);

  const isSelected = useCallback(
    (bookId: number) => {
      return selectedBookIds.has(bookId);
    },
    [selectedBookIds],
  );

  const handleBookClick = useCallback(
    (book: Book, books: Book[], event: React.MouseEvent) => {
      const bookIndex = books.findIndex((b) => b.id === book.id);
      if (bookIndex === -1) {
        return;
      }

      if (event.shiftKey && lastSelectedIndex !== null) {
        // Shift+click: select range from last selected to current
        const startIndex = lastSelectedIndex;
        const endIndex = bookIndex;
        const minIndex = Math.min(startIndex, endIndex);
        const maxIndex = Math.max(startIndex, endIndex);

        setSelectedBookIds((prev) => {
          const next = new Set(prev);
          for (let i = minIndex; i <= maxIndex; i++) {
            const book = books[i];
            if (book) {
              next.add(book.id);
            }
          }
          return next;
        });
        setLastSelectedIndex(bookIndex);
      } else if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd+click: toggle selection
        setSelectedBookIds((prev) => {
          const next = new Set(prev);
          if (next.has(book.id)) {
            next.delete(book.id);
          } else {
            next.add(book.id);
          }
          return next;
        });
        setLastSelectedIndex(bookIndex);
      } else {
        // Regular click: clear and select single
        setSelectedBookIds(new Set([book.id]));
        setLastSelectedIndex(bookIndex);
      }
    },
    [lastSelectedIndex],
  );

  const clearSelection = useCallback(() => {
    setSelectedBookIds(new Set());
    setLastSelectedIndex(null);
  }, []);

  const selectAll = useCallback((books: Book[]) => {
    const allIds = new Set(books.map((book) => book.id));
    setSelectedBookIds(allIds);
    if (books.length > 0) {
      setLastSelectedIndex(books.length - 1);
    }
  }, []);

  // Handle click-outside to clear selection
  // Use mousedown instead of click to avoid issues with React's synthetic events
  // and to catch the event before any onClick handlers that might close modals
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Only clear if there are selected books
      if (selectedBookIds.size === 0) {
        return;
      }

      const target = event.target as HTMLElement;

      // Check if click is on a book card using data attribute
      const isBookCard = target.closest("[data-book-card]");
      // Don't clear if clicking on a book card
      if (isBookCard) {
        return;
      }

      // Check if click originated from within preserved elements (check both target and all parents)
      // This handles event bubbling - if any parent has the attribute, preserve selection
      const preservedSelectors = [
        "[data-with-selected-button]",
        "[data-with-selected-panel]",
        "[data-keep-selection]",
      ];
      const isPreserved = preservedSelectors.some((selector) =>
        target.closest(selector),
      );

      // Don't clear if clicking on preserved elements
      if (isPreserved) {
        return;
      }

      // Clear selection when clicking outside book cards
      clearSelection();
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [selectedBookIds.size, clearSelection]);

  return (
    <SelectedBooksContext.Provider
      value={{
        selectedBookIds,
        books,
        setBooks: handleSetBooks,
        isSelected,
        handleBookClick,
        clearSelection,
        selectAll,
        selectedCount: selectedBookIds.size,
      }}
    >
      {children}
    </SelectedBooksContext.Provider>
  );
}

export function useSelectedBooks() {
  const context = useContext(SelectedBooksContext);
  if (context === undefined) {
    throw new Error(
      "useSelectedBooks must be used within a SelectedBooksProvider",
    );
  }
  return context;
}
