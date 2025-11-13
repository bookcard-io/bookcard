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

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import type { LibraryTabId } from "@/components/library/LibraryTabs";
import type { Book } from "@/types/book";
import { useBookEditModal } from "./useBookEditModal";
import { useBookUpload } from "./useBookUpload";
import { useBookViewModal } from "./useBookViewModal";
import { useLibraryFilters } from "./useLibraryFilters";
import { useLibrarySearch } from "./useLibrarySearch";
import { useLibrarySorting } from "./useLibrarySorting";
import { useLibraryViewMode } from "./useLibraryViewMode";

export interface UseMainContentResult {
  // Tab state
  activeTab: LibraryTabId;
  handleTabChange: (tabId: LibraryTabId) => void;

  // Search state
  search: ReturnType<typeof useLibrarySearch>;

  // Sorting state
  sorting: ReturnType<typeof useLibrarySorting>;

  // Filters state
  filters: ReturnType<typeof useLibraryFilters>;

  // Book navigation data setter
  setBooksNavigationData: React.Dispatch<
    React.SetStateAction<{
      bookIds: number[];
      loadMore?: () => void;
      hasMore?: boolean;
      isLoading: boolean;
    }>
  >;

  // Book view modal state
  bookModal: ReturnType<typeof useBookViewModal>;

  // Book edit modal state
  bookEditModal: ReturnType<typeof useBookEditModal>;

  // Book upload state
  bookUpload: ReturnType<typeof useBookUpload>;

  // View mode state
  viewMode: ReturnType<typeof useLibraryViewMode>;

  // Book data update ref
  booksGridBookDataUpdateRef: React.RefObject<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
    addBook?: (bookId: number) => Promise<void>;
  }>;

  // View mode change handler
  handleViewModeChange: (mode: string) => void;
}

/**
 * Custom hook for coordinating main content area state and logic.
 *
 * Manages tab state, coordinates specialized hooks for search, filtering,
 * sorting, view mode, and book viewing/editing.
 * Handles coordination between panels (sort/filters) and modal interactions.
 * Follows SRP by delegating to specialized hooks.
 * Follows SOC by separating concerns into independent hooks.
 * Follows IOC by composing hooks with coordination callbacks.
 *
 * Returns
 * -------
 * UseMainContentResult
 *     All state and handlers needed for MainContent component rendering.
 */
export function useMainContent(): UseMainContentResult {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Get initial tab from URL query parameter, default to "library"
  const getInitialTab = (): LibraryTabId => {
    const tabParam = searchParams.get("tab");
    if (tabParam === "shelves" || tabParam === "library") {
      return tabParam;
    }
    return "library";
  };

  // Active tab state - initialize from URL query parameter
  const [activeTab, setActiveTab] = useState<LibraryTabId>(getInitialTab);

  // Sync tab state with URL query parameter changes (only when URL changes externally)
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    const newTab: LibraryTabId = tabParam === "shelves" ? "shelves" : "library";
    // Only update if different from current state to avoid unnecessary updates
    if (newTab !== activeTab) {
      setActiveTab(newTab);
    }
  }, [searchParams, activeTab]);

  // Handle tab change with URL sync
  const handleTabChange = useCallback(
    (tabId: LibraryTabId) => {
      setActiveTab(tabId);
      // Update URL query parameter
      const params = new URLSearchParams(searchParams.toString());
      if (tabId === "library") {
        // Remove tab param for library (default)
        params.delete("tab");
      } else {
        params.set("tab", tabId);
      }
      const newUrl = params.toString() ? `/?${params.toString()}` : "/";
      router.push(newUrl, { scroll: false });
    },
    [searchParams, router],
  );

  // Use refs to store coordination methods to avoid circular dependencies
  const sortCloseRef = useRef<(() => void) | undefined>(undefined);
  const filtersCloseRef = useRef<(() => void) | undefined>(undefined);
  const bookModalRef = useRef<{
    handleBookClick: (book: { id: number }) => void;
  } | null>(null);
  const booksGridBookDataUpdateRef = useRef<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
    addBook?: (bookId: number) => Promise<void>;
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

  // Store book navigation data from BooksGrid (to avoid duplicate fetch)
  const [booksNavigationData, setBooksNavigationData] = useState<{
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  }>({
    bookIds: [],
    isLoading: false,
  });

  // Book view modal state with book IDs and infinite scroll support for navigation
  const bookModal = useBookViewModal({
    bookIds: booksNavigationData.bookIds,
    loadMore: booksNavigationData.loadMore,
    hasMore: booksNavigationData.hasMore,
    isLoading: booksNavigationData.isLoading,
  });

  // Update ref so search can access book modal
  useEffect(() => {
    bookModalRef.current = bookModal;
  }, [bookModal]);

  // Book edit modal state
  const bookEditModal = useBookEditModal();

  // Book upload state - adds book to grid and opens edit modal on success
  const bookUpload = useBookUpload({
    onUploadSuccess: async (bookId) => {
      // Add book to grid so it appears immediately
      await booksGridBookDataUpdateRef.current?.addBook?.(bookId);
      // Open edit modal for the newly uploaded book
      bookEditModal.handleEditBook(bookId);
    },
    onUploadError: (error) => {
      // TODO: Show error notification to user
      // eslint-disable-next-line no-console
      console.error("Book upload failed:", error);
    },
  });

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

  return {
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
  };
}
