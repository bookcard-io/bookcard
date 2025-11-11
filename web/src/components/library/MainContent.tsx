"use client";

import { useCallback, useMemo, useRef } from "react";
import { BookEditModal } from "@/components/books/BookEditModal";
import { BookViewModal } from "@/components/books/BookViewModal";
import { BooksGrid } from "@/components/library/BooksGrid";
import { LibraryHeader } from "@/components/library/LibraryHeader";
import { SearchWidgetBar } from "@/components/library/SearchWidgetBar";
import { FiltersPanel } from "@/components/library/widgets/FiltersPanel";
import { useBookEditModal } from "@/hooks/useBookEditModal";
import { useBookViewModal } from "@/hooks/useBookViewModal";
import { useLibraryBooks } from "@/hooks/useLibraryBooks";
import { useLibraryFilters } from "@/hooks/useLibraryFilters";
import { useLibrarySearch } from "@/hooks/useLibrarySearch";
import { useLibrarySorting } from "@/hooks/useLibrarySorting";
import { useLibraryViewMode } from "@/hooks/useLibraryViewMode";
import type { Book } from "@/types/book";

/**
 * Main content area for the library view.
 *
 * Composes specialized hooks for search, filtering, sorting, view mode, and book viewing.
 * Follows SRP by delegating state management to specialized hooks.
 * Follows IOC by composing hooks with coordination callbacks.
 * Follows SOC by separating concerns into independent hooks.
 */
export function MainContent() {
  // Use refs to store coordination methods to avoid circular dependencies
  const sortCloseRef = useRef<(() => void) | undefined>(undefined);
  const filtersCloseRef = useRef<(() => void) | undefined>(undefined);
  const bookModalRef = useRef<{
    handleBookClick: (book: { id: number }) => void;
  } | null>(null);
  const booksGridBookDataUpdateRef = useRef<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
  }>({ updateBook: () => {}, updateCover: () => {} });

  // Search state - use ref for book click to avoid circular dependency
  const search = useLibrarySearch({
    onBookClick: (bookId: number) => {
      bookModalRef.current?.handleBookClick({ id: bookId });
    },
  });

  // Sorting state with coordination
  const sorting = useLibrarySorting({
    onSortPanelChange: (isOpen) => {
      // Close filters panel when sort panel opens
      if (isOpen) {
        filtersCloseRef.current?.();
      }
    },
  });
  sortCloseRef.current = sorting.closeSortPanel;

  // Filters state with coordination
  const filters = useLibraryFilters({
    onClearSearch: search.clearSearch,
    onFiltersPanelChange: (isOpen) => {
      // Close sort panel when filters panel opens
      if (isOpen) {
        sortCloseRef.current?.();
      }
    },
  });
  filtersCloseRef.current = filters.closeFiltersPanel;

  // Fetch books using centralized hook to eliminate DRY violation
  const { books, loadMore, hasMore, isLoading } = useLibraryBooks({
    filters: filters.filters,
    searchQuery: search.filterQuery,
    sortBy: sorting.sortBy,
    sortOrder: sorting.sortOrder,
    pageSize: 20,
  });

  // Extract book IDs for navigation
  const bookIds = useMemo(() => books.map((book) => book.id), [books]);

  // Book view modal state with book IDs and infinite scroll support for navigation
  const bookModal = useBookViewModal({
    bookIds,
    loadMore,
    hasMore,
    isLoading,
  });

  // Update ref so search can access book modal
  bookModalRef.current = bookModal;

  // Book edit modal state
  const bookEditModal = useBookEditModal();

  // View mode state
  const viewMode = useLibraryViewMode({
    onSortToggle: sorting.handleSortToggle,
  });

  // Combined view mode change handler
  const handleViewModeChange = useCallback(
    (mode: string) => {
      viewMode.handleViewModeChange(mode as typeof viewMode.viewMode);
    },
    [viewMode],
  );

  return (
    <>
      <div className="flex min-h-full flex-col">
        <LibraryHeader />
        <div className="relative">
          <SearchWidgetBar
            searchValue={search.searchInputValue}
            onSearchChange={search.handleSearchChange}
            onSearchSubmit={search.handleSearchSubmit}
            onSuggestionClick={search.handleSuggestionClick}
            onFiltersClick={filters.handleFiltersClick}
            filters={filters.filters}
            onSortByClick={sorting.handleSortByClick}
            sortBy={sorting.sortBy}
            showSortPanel={sorting.showSortPanel}
            onSortByChange={sorting.handleSortByChange}
            activeViewMode={viewMode.viewMode}
            sortOrder={sorting.sortOrder}
            onViewModeChange={handleViewModeChange}
          />
          {filters.showFiltersPanel && (
            <FiltersPanel
              filters={filters.filters}
              selectedSuggestions={filters.selectedFilterSuggestions}
              onFiltersChange={filters.handleFiltersChange}
              onSuggestionsChange={filters.handleSuggestionsChange}
              onApply={filters.handleApplyFilters}
              onClear={filters.handleClearFilters}
              onClose={filters.handleCloseFiltersPanel}
            />
          )}
        </div>
        {viewMode.viewMode === "grid" && (
          <BooksGrid
            searchQuery={search.filterQuery}
            filters={filters.filters}
            sortBy={sorting.sortBy}
            sortOrder={sorting.sortOrder}
            onBookClick={bookModal.handleBookClick}
            onBookEdit={bookEditModal.handleEditBook}
            bookDataUpdateRef={booksGridBookDataUpdateRef}
          />
        )}
      </div>
      <BookViewModal
        bookId={bookModal.viewingBookId}
        onClose={bookModal.handleCloseModal}
        onNavigatePrevious={bookModal.handleNavigatePrevious}
        onNavigateNext={bookModal.handleNavigateNext}
        onEdit={bookEditModal.handleEditBook}
      />
      <BookEditModal
        bookId={bookEditModal.editingBookId}
        onClose={bookEditModal.handleCloseModal}
        onCoverSaved={(bookId) => {
          // Update cover in grid when cover is saved (O(1) operation)
          booksGridBookDataUpdateRef.current?.updateCover(bookId);
        }}
        onBookSaved={(book) => {
          // Update book data in grid when book is saved (O(1) operation)
          booksGridBookDataUpdateRef.current?.updateBook(book.id, {
            title: book.title,
            authors: book.authors,
            thumbnail_url: book.thumbnail_url,
          });
        }}
      />
    </>
  );
}
