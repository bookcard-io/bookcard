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

import dynamic from "next/dynamic";
import { BookEditModal } from "@/components/books/BookEditModal";
import { BookViewModal } from "@/components/books/BookViewModal";
import { LibraryHeader } from "@/components/library/LibraryHeader";
import { LibraryTabs } from "@/components/library/LibraryTabs";
import { SearchWidgetBar } from "@/components/library/SearchWidgetBar";
import { FiltersPanel } from "@/components/library/widgets/FiltersPanel";
import { ShelvesGrid } from "@/components/shelves/ShelvesGrid";
import { ShelvesList } from "@/components/shelves/ShelvesList";
import { useSelectedShelf } from "@/contexts/SelectedShelfContext";
import { useMainContent } from "@/hooks/useMainContent";

// Lazily load views to ensure only the active one mounts and fetches on first paint
const BooksGrid = dynamic(
  () => import("@/components/library/BooksGrid").then((m) => m.BooksGrid),
  { ssr: false },
);
const BooksList = dynamic(
  () => import("@/components/library/BooksList").then((m) => m.BooksList),
  { ssr: false },
);

/**
 * Main content area for the library view.
 *
 * Pure presentation component that renders UI based on coordinated state.
 * All business logic is delegated to useMainContent hook.
 * Follows SRP by focusing solely on rendering.
 * Follows IOC by using hook for all state and logic.
 * Follows SOC by separating presentation from business logic.
 */
export function MainContent() {
  const {
    activeTab,
    handleTabChange,
    search,
    sorting,
    filters,
    setBooksNavigationData,
    bookModal,
    bookEditModal,
    bookUpload,
    viewMode,
    booksGridBookDataUpdateRef,
    handleViewModeChange,
  } = useMainContent();

  const { selectedShelfId } = useSelectedShelf();

  return (
    <>
      <div className="flex min-h-full flex-col">
        <LibraryHeader
          onAddBooksClick={bookUpload.openFileBrowser}
          fileInputRef={bookUpload.fileInputRef}
          onFileChange={bookUpload.handleFileChange}
          accept={bookUpload.accept}
          isUploading={bookUpload.isUploading}
        />
        <div className="relative">
          {activeTab === "library" && (
            <>
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
            </>
          )}
        </div>
        <LibraryTabs activeTab={activeTab} onTabChange={handleTabChange} />
        {activeTab === "library" && (
          <>
            {viewMode.isReady && viewMode.viewMode === "grid" && (
              <BooksGrid
                searchQuery={search.filterQuery}
                filters={filters.filters}
                shelfId={selectedShelfId}
                sortBy={sorting.sortBy}
                sortOrder={sorting.sortOrder}
                onBookClick={bookModal.handleBookClick}
                onBookEdit={bookEditModal.handleEditBook}
                bookDataUpdateRef={booksGridBookDataUpdateRef}
                onBooksDataChange={setBooksNavigationData}
              />
            )}
            {viewMode.isReady && viewMode.viewMode === "list" && (
              <BooksList
                searchQuery={search.filterQuery}
                filters={filters.filters}
                shelfId={selectedShelfId}
                sortBy={sorting.sortBy}
                sortOrder={sorting.sortOrder}
                onBookClick={bookModal.handleBookClick}
                onBookEdit={bookEditModal.handleEditBook}
                bookDataUpdateRef={booksGridBookDataUpdateRef}
                onBooksDataChange={setBooksNavigationData}
              />
            )}
          </>
        )}
        {activeTab === "shelves" && (
          <>
            {viewMode.isReady && viewMode.viewMode === "grid" && (
              <ShelvesGrid />
            )}
            {viewMode.isReady && viewMode.viewMode === "list" && (
              <ShelvesList />
            )}
          </>
        )}
      </div>
      <BookViewModal
        bookId={bookModal.viewingBookId}
        onClose={bookModal.handleCloseModal}
        onNavigatePrevious={bookModal.handleNavigatePrevious}
        onNavigateNext={bookModal.handleNavigateNext}
        onEdit={bookEditModal.handleEditBook}
        onBookDeleted={(bookId) => {
          booksGridBookDataUpdateRef.current?.removeBook?.(bookId);
        }}
      />
      {bookEditModal.editingBookId !== null && (
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
      )}
    </>
  );
}
