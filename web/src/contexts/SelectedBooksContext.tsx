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
 * Provider for managing selected books state.
 *
 * Implements multi-select functionality with Ctrl+click (toggle) and
 * Shift+click (range selection) support.
 */
export function SelectedBooksProvider({ children }: { children: ReactNode }) {
  const [selectedBookIds, setSelectedBookIds] = useState<Set<number>>(
    new Set(),
  );
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(
    null,
  );

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

      // Clear selection when clicking outside book cards
      clearSelection();
    };

    document.addEventListener("click", handleClickOutside);
    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, [selectedBookIds.size, clearSelection]);

  return (
    <SelectedBooksContext.Provider
      value={{
        selectedBookIds,
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
