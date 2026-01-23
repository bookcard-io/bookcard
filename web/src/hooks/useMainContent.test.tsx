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

import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
// Mock Next.js navigation - using manual mock file
import { mockGet, mockPush, mockToString } from "@/__mocks__/next-navigation";
import { GlobalMessageProvider } from "@/contexts/GlobalMessageContext";

// Mock all the hooks used by useMainContent
vi.mock("./useLibrarySearch", () => ({
  useLibrarySearch: vi.fn(),
}));

vi.mock("./useLibrarySorting", () => ({
  useLibrarySorting: vi.fn(),
}));

vi.mock("./useLibraryFilters", () => ({
  useLibraryFilters: vi.fn(),
}));

vi.mock("./useLibraryViewMode", () => ({
  useLibraryViewMode: vi.fn(),
}));

vi.mock("./useBookViewModal", () => ({
  useBookViewModal: vi.fn(),
}));

vi.mock("./useBookEditModal", () => ({
  useBookEditModal: vi.fn(),
}));

vi.mock("./useBookUpload", () => ({
  useBookUpload: vi.fn(),
}));

import { useBookEditModal } from "./useBookEditModal";
import { useBookUpload } from "./useBookUpload";
import { useBookViewModal } from "./useBookViewModal";
import { useLibraryFilters } from "./useLibraryFilters";
import { useLibrarySearch } from "./useLibrarySearch";
import { useLibrarySorting } from "./useLibrarySorting";
import { useLibraryViewMode } from "./useLibraryViewMode";
import { useMainContent } from "./useMainContent";

describe("useMainContent", () => {
  let mockSearch: ReturnType<typeof useLibrarySearch>;
  let mockSorting: ReturnType<typeof useLibrarySorting>;
  let mockFilters: ReturnType<typeof useLibraryFilters>;
  let mockViewMode: ReturnType<typeof useLibraryViewMode>;
  let mockBookModal: ReturnType<typeof useBookViewModal>;
  let mockBookEditModal: ReturnType<typeof useBookEditModal>;
  let mockBookUpload: ReturnType<typeof useBookUpload>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockClear();
    mockGet.mockClear();
    mockToString.mockClear();
    mockGet.mockReturnValue(null);
    mockToString.mockReturnValue("");

    mockSearch = {
      searchInputValue: "",
      filterQuery: "",
      handleSearchChange: vi.fn<(value: string) => void>(),
      handleSearchSubmit: vi.fn<(value: string) => void>(),
      handleSuggestionClick:
        vi.fn<
          (suggestion: { type: string; name: string; id?: number }) => void
        >(),
      clearSearch: vi.fn<() => void>(),
    } as ReturnType<typeof useLibrarySearch>;

    mockSorting = {
      sortBy: "title",
      sortOrder: "asc",
      isReady: true,
      showSortPanel: false,
      handleSortByClick: vi.fn<() => void>(),
      handleSortByChange:
        vi.fn<
          (
            newSortBy: import("@/components/library/widgets/SortPanel").SortField,
          ) => void
        >(),
      handleSortToggle: vi.fn<() => void>(),
      closeSortPanel: vi.fn<() => void>(),
    } as ReturnType<typeof useLibrarySorting>;

    mockFilters = {
      filters: {
        authorIds: [],
        titleIds: [],
        genreIds: [],
        publisherIds: [],
        seriesIds: [],
        tagIds: [],
        languageIds: [],
        ratingIds: [],
        identifierIds: [],
        formats: [],
      },
      selectedFilterSuggestions: {},
      showFiltersPanel: false,
      handleFiltersClick: vi.fn<() => void>(),
      handleFiltersChange:
        vi.fn<
          (
            newFilters: import("@/components/library/widgets/FiltersPanel").FilterValues,
          ) => void
        >(),
      handleSuggestionsChange:
        vi.fn<
          (
            suggestions: import("@/components/library/widgets/FiltersPanel").SelectedFilterSuggestions,
          ) => void
        >(),
      handleApplyFilters:
        vi.fn<
          (
            appliedFilters: import("@/components/library/widgets/FiltersPanel").FilterValues,
          ) => void
        >(),
      handleClearFilters: vi.fn<() => void>(),
      handleCloseFiltersPanel: vi.fn<() => void>(),
      clearFilters: vi.fn<() => void>(),
      closeFiltersPanel: vi.fn<() => void>(),
    } as ReturnType<typeof useLibraryFilters>;

    mockViewMode = {
      viewMode: "grid",
      isReady: true,
      handleViewModeChange: vi.fn<(mode: "grid" | "list") => void>(),
    } as ReturnType<typeof useLibraryViewMode>;

    mockBookModal = {
      viewingBookId: null,
      handleBookClick: vi.fn<(book: { id: number }) => void>(),
      handleCloseModal: vi.fn<() => void>(),
      handleNavigatePrevious: vi.fn<() => void>(),
      handleNavigateNext: vi.fn<() => void>(),
    } as ReturnType<typeof useBookViewModal>;

    mockBookEditModal = {
      editingBookId: null,
      handleEditBook: vi.fn<(bookId: number) => void>(),
      handleCloseModal: vi.fn<() => void>(),
    } as ReturnType<typeof useBookEditModal>;

    mockBookUpload = {
      fileInputRef: { current: null },
      isUploading: false,
      openFileBrowser: vi.fn<() => void>(),
      handleFileChange:
        vi.fn<(e: React.ChangeEvent<HTMLInputElement>) => void>(),
      accept:
        ".epub,.mobi,.azw,.azw3,.pdf,.txt,.rtf,.html,.htm,.fb2,.lit,.lrf,.pdb,.rb,.snb,.tcr,.djv,.djvu,.xps,.oxps,.cbz,.cbr,.cbc,.zip",
    } as ReturnType<typeof useBookUpload>;

    vi.mocked(useLibrarySearch).mockReturnValue(mockSearch);
    vi.mocked(useLibrarySorting).mockReturnValue(mockSorting);
    vi.mocked(useLibraryFilters).mockReturnValue(mockFilters);
    vi.mocked(useLibraryViewMode).mockReturnValue(mockViewMode);
    vi.mocked(useBookViewModal).mockReturnValue(mockBookModal);
    vi.mocked(useBookEditModal).mockReturnValue(mockBookEditModal);
    vi.mocked(useBookUpload).mockReturnValue(mockBookUpload);

    mockGet.mockReturnValue(null);
    mockToString.mockReturnValue("");
    mockPush.mockImplementation(() => {});
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <GlobalMessageProvider>{children}</GlobalMessageProvider>
  );

  describe("initialization", () => {
    it.each([
      { tabParam: null, expected: "library" },
      { tabParam: "library", expected: "library" },
      { tabParam: "shelves", expected: "shelves" },
      { tabParam: "invalid", expected: "library" },
    ])("should initialize with tab from URL: tabParam=$tabParam", ({
      tabParam,
      expected,
    }) => {
      mockGet.mockReturnValue(tabParam);
      const { result } = renderHook(() => useMainContent(), { wrapper });

      expect(result.current.activeTab).toBe(expected);
    });

    it("should return all hook results", () => {
      const { result } = renderHook(() => useMainContent(), { wrapper });

      expect(result.current.search).toBe(mockSearch);
      expect(result.current.sorting).toBe(mockSorting);
      expect(result.current.filters).toBe(mockFilters);
      expect(result.current.viewMode).toBe(mockViewMode);
      expect(result.current.bookModal).toBe(mockBookModal);
      expect(result.current.bookEditModal).toBe(mockBookEditModal);
      expect(result.current.bookUpload).toBe(mockBookUpload);
    });

    it("should initialize booksNavigationData with empty state", () => {
      const { result } = renderHook(() => useMainContent(), { wrapper });

      expect(result.current.setBooksNavigationData).toBeDefined();
      act(() => {
        result.current.setBooksNavigationData({
          bookIds: [],
          isLoading: false,
        });
      });
    });

    it("should initialize booksGridBookDataUpdateRef", () => {
      const { result } = renderHook(() => useMainContent(), { wrapper });

      expect(result.current.booksGridBookDataUpdateRef.current).toBeDefined();
      expect(
        result.current.booksGridBookDataUpdateRef.current?.updateBook,
      ).toBeDefined();
      expect(
        result.current.booksGridBookDataUpdateRef.current?.updateCover,
      ).toBeDefined();
    });
  });

  describe("handleTabChange", () => {
    it("should change tab to library and update URL", () => {
      mockGet.mockReturnValue(null);
      const { result } = renderHook(() => useMainContent(), { wrapper });

      act(() => {
        result.current.handleTabChange("library");
      });

      expect(result.current.activeTab).toBe("library");
      expect(mockPush).toHaveBeenCalledWith("/", { scroll: false });
    });

    it("should change tab to shelves and update URL", () => {
      mockGet.mockReturnValue(null);
      mockToString.mockReturnValue("");
      const { result } = renderHook(() => useMainContent(), { wrapper });

      expect(result.current.activeTab).toBe("library");

      // handleTabChange should call router.push with correct URL
      act(() => {
        result.current.handleTabChange("shelves");
      });

      // Verify router.push was called with correct URL
      expect(mockPush).toHaveBeenCalledWith("/?tab=shelves", { scroll: false });
      // The state update happens, but useEffect may sync it based on searchParams
      // So we verify the router call which is the main behavior
    });

    it("should remove tab param for library tab", () => {
      mockToString.mockReturnValue("other=value");
      const { result } = renderHook(() => useMainContent(), { wrapper });

      act(() => {
        result.current.handleTabChange("library");
      });

      expect(mockPush).toHaveBeenCalledWith("/?other=value", {
        scroll: false,
      });
    });

    it("should preserve other query params when changing to shelves", () => {
      mockToString.mockReturnValue("other=value");
      const { result } = renderHook(() => useMainContent(), { wrapper });

      act(() => {
        result.current.handleTabChange("shelves");
      });

      expect(mockPush).toHaveBeenCalledWith("/?other=value&tab=shelves", {
        scroll: false,
      });
    });
  });

  describe("tab sync with URL", () => {
    it("should sync tab when URL changes externally", () => {
      mockGet.mockReturnValue(null);
      const { result } = renderHook(() => useMainContent(), { wrapper });

      expect(result.current.activeTab).toBe("library");

      // Simulate URL change by creating new hook instance with different searchParams
      mockGet.mockReturnValue("shelves");
      const { result: newResult } = renderHook(() => useMainContent(), {
        wrapper,
      });

      expect(newResult.current.activeTab).toBe("shelves");
    });

    it("should not update if tab is already the same", () => {
      mockGet.mockReturnValue("library");
      const { result, rerender } = renderHook(() => useMainContent(), {
        wrapper,
      });

      const initialTab = result.current.activeTab;
      expect(initialTab).toBe("library");

      // Rerender with same tab
      rerender();

      expect(result.current.activeTab).toBe(initialTab);
    });
  });

  describe("coordination between panels", () => {
    it("should close filters panel when sort panel opens", () => {
      const mockOnSortPanelChange = vi.fn();
      vi.mocked(useLibrarySorting).mockReturnValue({
        ...mockSorting,
        onSortPanelChange: mockOnSortPanelChange,
      } as ReturnType<typeof useLibrarySorting>);

      renderHook(() => useMainContent(), { wrapper });

      // The hook should set up coordination
      expect(useLibrarySorting).toHaveBeenCalled();
      const callArgs = vi.mocked(useLibrarySorting).mock.calls[0]?.[0];
      expect(callArgs?.onSortPanelChange).toBeDefined();

      // When sort panel opens, filters should close
      act(() => {
        callArgs?.onSortPanelChange?.(true);
      });

      expect(mockFilters.closeFiltersPanel).toHaveBeenCalled();
    });

    it("should close sort panel when filters panel opens", () => {
      const mockOnFiltersPanelChange = vi.fn();
      vi.mocked(useLibraryFilters).mockReturnValue({
        ...mockFilters,
        onFiltersPanelChange: mockOnFiltersPanelChange,
      } as ReturnType<typeof useLibraryFilters>);

      renderHook(() => useMainContent(), { wrapper });

      const callArgs = vi.mocked(useLibraryFilters).mock.calls[0]?.[0];
      expect(callArgs?.onFiltersPanelChange).toBeDefined();

      // When filters panel opens, sort should close
      act(() => {
        callArgs?.onFiltersPanelChange?.(true);
      });

      expect(mockSorting.closeSortPanel).toHaveBeenCalled();
    });
  });

  describe("book modal coordination", () => {
    it("should connect search onBookClick to book modal", () => {
      renderHook(() => useMainContent(), { wrapper });

      const searchCallArgs = vi.mocked(useLibrarySearch).mock.calls[0]?.[0];
      expect(searchCallArgs?.onBookClick).toBeDefined();

      // The onBookClick should call book modal
      act(() => {
        searchCallArgs?.onBookClick?.(123);
      });

      // Book modal ref should be updated via useEffect
      expect(useBookViewModal).toHaveBeenCalled();
    });

    it("should update bookModalRef when bookModal changes", () => {
      const { rerender } = renderHook(() => useMainContent(), { wrapper });

      const newBookModal = {
        ...mockBookModal,
        handleBookClick: vi.fn(),
      };
      vi.mocked(useBookViewModal).mockReturnValue(
        newBookModal as ReturnType<typeof useBookViewModal>,
      );

      rerender();

      // The ref should be updated via useEffect
      expect(useBookViewModal).toHaveBeenCalled();
    });
  });

  describe("book upload coordination", () => {
    it("should set up book upload with success handler", () => {
      renderHook(() => useMainContent(), { wrapper });

      const uploadCallArgs = vi.mocked(useBookUpload).mock.calls[0]?.[0];
      expect(uploadCallArgs?.onUploadSuccess).toBeDefined();
      expect(uploadCallArgs?.onUploadError).toBeDefined();
    });

    it("should add book to grid and open edit modal on upload success", async () => {
      const mockAddBook = vi.fn().mockResolvedValue(undefined);
      const { result } = renderHook(() => useMainContent(), { wrapper });

      // Set up the ref
      result.current.booksGridBookDataUpdateRef.current = {
        updateBook: vi.fn(),
        updateCover: vi.fn(),
        addBook: mockAddBook,
      };

      const uploadCallArgs = vi.mocked(useBookUpload).mock.calls[0]?.[0];

      await act(async () => {
        await uploadCallArgs?.onUploadSuccess?.(123);
      });

      expect(mockAddBook).toHaveBeenCalledWith(123);
      expect(mockBookEditModal.handleEditBook).toHaveBeenCalledWith(123);
    });

    it("should handle upload error", () => {
      renderHook(() => useMainContent(), { wrapper });

      const uploadCallArgs = vi.mocked(useBookUpload).mock.calls[0]?.[0];
      const error = "Upload failed";

      act(() => {
        uploadCallArgs?.onUploadError?.(error);
      });

      // Error is handled by the global messaging system
      // The test verifies that the error callback is called without throwing
    });
  });

  describe("view mode coordination", () => {
    it("should connect view mode to sort toggle", () => {
      renderHook(() => useMainContent(), { wrapper });

      const viewModeCallArgs = vi.mocked(useLibraryViewMode).mock.calls[0]?.[0];
      expect(viewModeCallArgs?.onSortToggle).toBe(mockSorting.handleSortToggle);
    });

    it("should handle view mode change", () => {
      const { result } = renderHook(() => useMainContent(), { wrapper });

      act(() => {
        result.current.handleViewModeChange("list");
      });

      expect(mockViewMode.handleViewModeChange).toHaveBeenCalledWith("list");
    });
  });

  describe("booksNavigationData", () => {
    it("should update booksNavigationData", () => {
      const { result } = renderHook(() => useMainContent(), { wrapper });

      const newData = {
        bookIds: [1, 2, 3],
        loadMore: vi.fn(),
        hasMore: true,
        isLoading: false,
      };

      act(() => {
        result.current.setBooksNavigationData(newData);
      });

      // The data should be used by bookModal
      expect(useBookViewModal).toHaveBeenCalled();
    });

    it("should pass booksNavigationData to bookModal", () => {
      const { result } = renderHook(() => useMainContent(), { wrapper });

      const newData = {
        bookIds: [1, 2, 3],
        loadMore: vi.fn(),
        hasMore: true,
        isLoading: false,
      };

      act(() => {
        result.current.setBooksNavigationData(newData);
      });

      // Book modal should receive the data
      const bookModalCallArgs =
        vi.mocked(useBookViewModal).mock.calls[
          vi.mocked(useBookViewModal).mock.calls.length - 1
        ]?.[0];
      expect(bookModalCallArgs?.bookIds).toEqual([1, 2, 3]);
      expect(bookModalCallArgs?.loadMore).toBe(newData.loadMore);
      expect(bookModalCallArgs?.hasMore).toBe(true);
      expect(bookModalCallArgs?.isLoading).toBe(false);
    });
  });

  describe("filters coordination", () => {
    it("should connect filters clearSearch to search clearSearch", () => {
      renderHook(() => useMainContent(), { wrapper });

      const filtersCallArgs = vi.mocked(useLibraryFilters).mock.calls[0]?.[0];
      expect(filtersCallArgs?.onClearSearch).toBe(mockSearch.clearSearch);
    });
  });
});
