"use client";

import { useCallback, useRef } from "react";
import { BookViewModal } from "@/components/books/BookViewModal";
import { BooksGrid } from "@/components/library/BooksGrid";
import { LibraryHeader } from "@/components/library/LibraryHeader";
import { SearchWidgetBar } from "@/components/library/SearchWidgetBar";
import { FiltersPanel } from "@/components/library/widgets/FiltersPanel";
import { useSidebar } from "@/contexts/SidebarContext";
import { useBookViewModal } from "@/hooks/useBookViewModal";
import { useLibraryFilters } from "@/hooks/useLibraryFilters";
import { useLibrarySearch } from "@/hooks/useLibrarySearch";
import { useLibrarySorting } from "@/hooks/useLibrarySorting";
import { useLibraryViewMode } from "@/hooks/useLibraryViewMode";
import styles from "./MainContent.module.scss";

/**
 * Main content area for the library view.
 *
 * Composes specialized hooks for search, filtering, sorting, view mode, and book viewing.
 * Follows SRP by delegating state management to specialized hooks.
 * Follows IOC by composing hooks with coordination callbacks.
 * Follows SOC by separating concerns into independent hooks.
 */
export function MainContent() {
  const { isCollapsed } = useSidebar();

  // Book view modal state
  const bookModal = useBookViewModal();

  // Search state (needs book modal handler)
  const search = useLibrarySearch({
    onBookClick: (bookId: number) => {
      bookModal.handleBookClick({ id: bookId });
    },
  });

  // Use refs to store coordination methods to avoid circular dependencies
  const sortCloseRef = useRef<(() => void) | undefined>(undefined);
  const filtersCloseRef = useRef<(() => void) | undefined>(undefined);

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
    <main
      className={`${styles.mainContent} ${isCollapsed ? styles.collapsed : ""}`}
    >
      <div className={styles.contentWrapper}>
        <LibraryHeader />
        <div className={styles.widgetBarContainer}>
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
          />
        )}
      </div>
      <BookViewModal
        bookId={bookModal.viewingBookId}
        onClose={bookModal.handleCloseModal}
        onNavigatePrevious={bookModal.handleNavigatePrevious}
        onNavigateNext={bookModal.handleNavigateNext}
      />
    </main>
  );
}
