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

import { vi } from "vitest";

vi.mock("@/contexts/UserContext", () => ({
  useUser: vi.fn(),
}));

vi.mock("@/hooks/useBook", () => ({
  useBook: vi.fn(),
}));

vi.mock("@/hooks/useBookForm", () => ({
  useBookForm: vi.fn(),
}));

vi.mock("@/hooks/useStagedCoverUrl", () => ({
  useStagedCoverUrl: vi.fn(),
}));

vi.mock("@/hooks/useCoverFromUrl", () => ({
  useCoverFromUrl: vi.fn(),
}));

vi.mock("@/hooks/useKeyboardNavigation", () => ({
  useKeyboardNavigation: vi.fn(),
}));

vi.mock("@/hooks/usePreferredProviders", () => ({
  usePreferredProviders: vi.fn(),
}));

vi.mock("@/hooks/useProviderSettings", () => ({
  useProviderSettings: vi.fn(),
}));

vi.mock("@/components/metadata/getInitialSearchQuery", () => ({
  getInitialSearchQuery: vi.fn(),
}));

vi.mock("@/utils/metadata", () => ({
  convertMetadataRecordToBookUpdate: vi.fn(),
  applyBookUpdateToForm: vi.fn(),
  calculateProvidersForBackend: vi.fn(() => []), // Default return empty array
}));

vi.mock("@/utils/books", () => ({
  getCoverUrlWithCacheBuster: vi.fn(),
}));

import { act, renderHook } from "@testing-library/react";
import type { UseFormReturn } from "react-hook-form";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { getInitialSearchQuery } from "@/components/metadata/getInitialSearchQuery";
import { useUser } from "@/contexts/UserContext";
import { useBook } from "@/hooks/useBook";
import { useBookForm } from "@/hooks/useBookForm";
import { useCoverFromUrl } from "@/hooks/useCoverFromUrl";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { usePreferredProviders } from "@/hooks/usePreferredProviders";
import { useProviderSettings } from "@/hooks/useProviderSettings";
import { useStagedCoverUrl } from "@/hooks/useStagedCoverUrl";
import type { BookUpdateFormData } from "@/schemas/bookUpdateSchema";
import type { Book, BookUpdate } from "@/types/book";
import { getCoverUrlWithCacheBuster } from "@/utils/books";
import {
  applyBookUpdateToForm,
  calculateProvidersForBackend,
  convertMetadataRecordToBookUpdate,
} from "@/utils/metadata";
import { useBookEditForm } from "./useBookEditForm";

describe("useBookEditForm", () => {
  const mockBook: Book = {
    id: 1,
    title: "Test Book",
    authors: ["Author 1"],
    author_sort: "Author 1",
    title_sort: null,
    pubdate: "2024-01-15T00:00:00Z",
    timestamp: null,
    series: null,
    series_id: null,
    series_index: null,
    isbn: null,
    uuid: "uuid-1",
    thumbnail_url: null,
    has_cover: false,
  };

  let mockUpdateBook: ReturnType<
    typeof vi.fn<(update: BookUpdate) => Promise<Book | null>>
  >;
  let mockGetSetting: ReturnType<typeof vi.fn<(key: string) => string | null>>;
  let mockHandleFieldChange: ReturnType<typeof vi.fn>;
  let mockHandleFormSubmit: ReturnType<typeof vi.fn>;
  let mockResetForm: ReturnType<typeof vi.fn>;
  let mockSetStagedCoverUrl: ReturnType<
    typeof vi.fn<(url: string | null) => void>
  >;
  let mockClearStagedCoverUrl: ReturnType<typeof vi.fn<() => void>>;
  let mockDownloadCover: ReturnType<
    typeof vi.fn<(url: string) => Promise<void>>
  >;
  let mockOnClose: ReturnType<typeof vi.fn<() => void>>;
  let mockOnCoverSaved: ReturnType<typeof vi.fn<(bookId: number) => void>>;
  let mockOnBookSaved: ReturnType<typeof vi.fn<(book: Book) => void>>;
  let mockOnUpdateSuccess: ((book: Book) => void) | undefined;

  beforeEach(() => {
    vi.clearAllMocks();

    mockUpdateBook = vi
      .fn<(update: BookUpdate) => Promise<Book | null>>()
      .mockResolvedValue(mockBook);
    mockGetSetting = vi.fn<(key: string) => string | null>(
      (_key: string) => null,
    );
    mockHandleFieldChange = vi.fn();
    mockResetForm = vi.fn<() => void>();
    mockSetStagedCoverUrl = vi.fn<(url: string | null) => void>();
    mockClearStagedCoverUrl = vi.fn<() => void>();
    mockDownloadCover = vi
      .fn<(url: string) => Promise<void>>()
      .mockResolvedValue(undefined);
    mockOnClose = vi.fn<() => void>();
    mockOnCoverSaved = vi.fn<(bookId: number) => void>();
    mockOnBookSaved = vi.fn<(book: Book) => void>();

    // Create handleFormSubmit that calls onUpdateSuccess
    mockHandleFormSubmit = vi.fn().mockImplementation(async () => {
      const updatedBook = await mockUpdateBook({});
      if (mockOnUpdateSuccess && updatedBook) {
        mockOnUpdateSuccess(updatedBook);
      }
    });

    vi.mocked(useUser).mockReturnValue({
      user: null,
      isLoading: false,
      error: null,
      refresh: vi.fn(),
      refreshTimestamp: 0,
      updateUser: vi.fn(),
      profilePictureUrl: null,
      invalidateProfilePictureCache: vi.fn(),
      settings: {},
      isSaving: false,
      getSetting: mockGetSetting,
      updateSetting: vi.fn(),
      defaultDevice: null,
      hasPermission: vi.fn(() => false),
      canPerformAction: vi.fn(() => false),
    });

    vi.mocked(useBook).mockReturnValue({
      book: mockBook,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    // Mock useBookForm to capture onUpdateSuccess callback
    const mockFormData = {
      title: "Test Book",
      author_names: ["Author 1"],
      pubdate: "2024-01-15",
      series_name: null,
      series_index: null,
      description: null,
      publisher_name: null,
      language_codes: null,
      tag_names: [],
      identifiers: [],
      rating_value: null,
    };

    vi.mocked(useBookForm).mockImplementation((options) => {
      mockOnUpdateSuccess = options.onUpdateSuccess;
      return {
        form: {
          getValues: vi.fn(() => mockFormData),
          watch: vi.fn(),
          control: {} as UseFormReturn<BookUpdateFormData>["control"],
          formState: { errors: {}, isDirty: false },
        } as unknown as UseFormReturn<BookUpdateFormData>,
        hasChanges: false,
        showSuccess: false,
        handleFieldChange: mockHandleFieldChange,
        handleSubmit: mockHandleFormSubmit,
        resetForm: mockResetForm,
      } as ReturnType<typeof useBookForm>;
    });

    vi.mocked(useStagedCoverUrl).mockReturnValue({
      stagedCoverUrl: null,
      setStagedCoverUrl: mockSetStagedCoverUrl,
      clearStagedCoverUrl: mockClearStagedCoverUrl,
    });

    vi.mocked(useCoverFromUrl).mockReturnValue({
      isLoading: false,
      error: null,
      downloadCover: mockDownloadCover,
      clearError: vi.fn(),
    });

    vi.mocked(useKeyboardNavigation).mockImplementation(() => {});

    vi.mocked(convertMetadataRecordToBookUpdate).mockReturnValue({
      title: "Updated Title",
    });

    vi.mocked(getCoverUrlWithCacheBuster).mockReturnValue(
      "/api/books/1/cover?t=123",
    );

    vi.mocked(usePreferredProviders).mockReturnValue({
      preferredProviders: new Set(["google", "openlibrary"]),
      preferredProviderNames: ["google", "openlibrary"],
      isLoading: false,
      togglePreferred: vi.fn(),
    });

    vi.mocked(useProviderSettings).mockReturnValue({
      enabledProviders: new Set(["google", "openlibrary"]),
      enabledProviderNames: ["google", "openlibrary"],
      isLoading: false,
      toggleProvider: vi.fn(),
    });

    vi.mocked(getInitialSearchQuery).mockReturnValue("Test Book Author 1");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with book data when bookId is provided", () => {
    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    expect(result.current.book).toEqual(mockBook);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should initialize with null book when bookId is null", () => {
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: null,
        onClose: mockOnClose,
      }),
    );

    expect(result.current.book).toBeNull();
  });

  it("should pass loading state from useBook", () => {
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    expect(result.current.isLoading).toBe(true);
  });

  it("should pass error state from useBook", () => {
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: false,
      error: "Failed to load book",
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    expect(result.current.error).toBe("Failed to load book");
  });

  it("should pass isUpdating and updateError from useBook", () => {
    vi.mocked(useBook).mockReturnValue({
      book: mockBook,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: true,
      updateError: "Update failed",
    } as ReturnType<typeof useBook>);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    expect(result.current.isUpdating).toBe(true);
    expect(result.current.updateError).toBe("Update failed");
  });

  it("should open metadata modal", () => {
    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleOpenMetadataModal();
    });

    expect(result.current.showMetadataModal).toBe(true);
  });

  it("should close metadata modal", () => {
    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleOpenMetadataModal();
    });

    act(() => {
      result.current.handleCloseMetadataModal();
    });

    expect(result.current.showMetadataModal).toBe(false);
  });

  it("should handle metadata selection and populate form", () => {
    const metadataRecord: MetadataRecord = {
      title: "New Title",
      authors: ["New Author"],
      cover_url: "https://example.com/cover.jpg",
      source_id: "test",
      external_id: "123",
      url: "https://example.com/book",
    };

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleSelectMetadata(metadataRecord);
    });

    expect(convertMetadataRecordToBookUpdate).toHaveBeenCalledWith(
      metadataRecord,
    );
    expect(applyBookUpdateToForm).toHaveBeenCalled();
    expect(result.current.showMetadataModal).toBe(false);
  });

  it("should stage cover URL when metadata has cover and replace setting is true", () => {
    mockGetSetting.mockReturnValue("true");
    const metadataRecord: MetadataRecord = {
      title: "New Title",
      authors: ["New Author"],
      cover_url: "https://example.com/cover.jpg",
      source_id: "test",
      external_id: "123",
      url: "https://example.com/book",
    };

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleSelectMetadata(metadataRecord);
    });

    expect(mockSetStagedCoverUrl).toHaveBeenCalledWith(
      "https://example.com/cover.jpg",
    );
  });

  it("should not stage cover URL when replace setting is false", () => {
    mockGetSetting.mockReturnValue("false");
    const metadataRecord: MetadataRecord = {
      title: "New Title",
      authors: ["New Author"],
      cover_url: "https://example.com/cover.jpg",
      source_id: "test",
      external_id: "123",
      url: "https://example.com/book",
    };

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleSelectMetadata(metadataRecord);
    });

    expect(mockSetStagedCoverUrl).not.toHaveBeenCalled();
  });

  it("should not stage cover URL when bookId is null", () => {
    mockGetSetting.mockReturnValue("true");
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    const metadataRecord: MetadataRecord = {
      title: "New Title",
      authors: ["New Author"],
      cover_url: "https://example.com/cover.jpg",
      source_id: "test",
      external_id: "123",
      url: "https://example.com/book",
    };

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: null,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleSelectMetadata(metadataRecord);
    });

    expect(mockSetStagedCoverUrl).not.toHaveBeenCalled();
  });

  it("should handle close and reset form", () => {
    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleClose();
    });

    expect(mockResetForm).toHaveBeenCalled();
    expect(mockClearStagedCoverUrl).toHaveBeenCalled();
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should call onCoverSaved when handleCoverSaved is called", () => {
    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
        onCoverSaved: mockOnCoverSaved,
      }),
    );

    act(() => {
      result.current.handleCoverSaved();
    });

    expect(mockOnCoverSaved).toHaveBeenCalledWith(1);
  });

  it("should not call onCoverSaved when bookId is null", () => {
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: null,
        onClose: mockOnClose,
        onCoverSaved: mockOnCoverSaved,
      }),
    );

    act(() => {
      result.current.handleCoverSaved();
    });

    expect(mockOnCoverSaved).not.toHaveBeenCalled();
  });

  it("should not call onCoverSaved when callback is not provided", () => {
    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      result.current.handleCoverSaved();
    });

    expect(mockOnCoverSaved).not.toHaveBeenCalled();
  });

  it("should handle form submit without staged cover", async () => {
    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(mockHandleFormSubmit).toHaveBeenCalledWith(submitEvent);
    expect(mockDownloadCover).not.toHaveBeenCalled();
  });

  it("should download staged cover before form submit when cover is external URL", async () => {
    vi.mocked(useStagedCoverUrl).mockReturnValue({
      stagedCoverUrl: "https://example.com/cover.jpg",
      setStagedCoverUrl: mockSetStagedCoverUrl,
      clearStagedCoverUrl: mockClearStagedCoverUrl,
    });

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(mockDownloadCover).toHaveBeenCalledWith(
      "https://example.com/cover.jpg",
    );
    expect(mockHandleFormSubmit).toHaveBeenCalledWith(submitEvent);
  });

  it("should not download staged cover when it's a temp URL", async () => {
    vi.mocked(useStagedCoverUrl).mockReturnValue({
      stagedCoverUrl: "/api/books/temp-covers/123",
      setStagedCoverUrl: mockSetStagedCoverUrl,
      clearStagedCoverUrl: mockClearStagedCoverUrl,
    });

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(mockDownloadCover).not.toHaveBeenCalled();
    expect(mockHandleFormSubmit).toHaveBeenCalledWith(submitEvent);
  });

  it("should not download staged cover when it's an API URL", async () => {
    vi.mocked(useStagedCoverUrl).mockReturnValue({
      stagedCoverUrl: "/api/books/1/cover",
      setStagedCoverUrl: mockSetStagedCoverUrl,
      clearStagedCoverUrl: mockClearStagedCoverUrl,
    });

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(mockDownloadCover).not.toHaveBeenCalled();
    expect(mockHandleFormSubmit).toHaveBeenCalledWith(submitEvent);
  });

  it("should not download staged cover when bookId is null", async () => {
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    vi.mocked(useStagedCoverUrl).mockReturnValue({
      stagedCoverUrl: "https://example.com/cover.jpg",
      setStagedCoverUrl: mockSetStagedCoverUrl,
      clearStagedCoverUrl: mockClearStagedCoverUrl,
    });

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: null,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(mockDownloadCover).not.toHaveBeenCalled();
    expect(mockHandleFormSubmit).toHaveBeenCalledWith(submitEvent);
  });

  it("should handle cover download error and continue with form submit", async () => {
    mockDownloadCover.mockRejectedValue(new Error("Download failed"));
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    vi.mocked(useStagedCoverUrl).mockReturnValue({
      stagedCoverUrl: "https://example.com/cover.jpg",
      setStagedCoverUrl: mockSetStagedCoverUrl,
      clearStagedCoverUrl: mockClearStagedCoverUrl,
    });

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(mockDownloadCover).toHaveBeenCalled();
    expect(mockHandleFormSubmit).toHaveBeenCalledWith(submitEvent);
    expect(consoleSpy).toHaveBeenCalledWith(
      "Failed to download staged cover:",
      expect.any(Error),
    );

    consoleSpy.mockRestore();
  });

  it("should call onBookSaved when book is updated successfully", async () => {
    const updatedBook = { ...mockBook, title: "Updated Title" };
    mockUpdateBook.mockResolvedValue(updatedBook);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
        onBookSaved: mockOnBookSaved,
      }),
    );

    // Trigger form submission which will call onUpdateSuccess
    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // onUpdateSuccess should be called synchronously within handleSubmit
    expect(mockOnBookSaved).toHaveBeenCalledWith(updatedBook);
  });

  it("should clear staged cover after book update", async () => {
    const updatedBook = { ...mockBook, title: "Updated Title" };
    mockUpdateBook.mockResolvedValue(updatedBook);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // onUpdateSuccess should be called synchronously within handleSubmit
    expect(mockClearStagedCoverUrl).toHaveBeenCalled();
  });

  it("should auto-dismiss modal when auto_dismiss_book_edit_modal is not 'false'", async () => {
    mockGetSetting.mockReturnValue("true");
    const updatedBook = { ...mockBook, title: "Updated Title" };
    mockUpdateBook.mockResolvedValue(updatedBook);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // onUpdateSuccess should be called synchronously within handleSubmit
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should not auto-dismiss modal when auto_dismiss_book_edit_modal is 'false'", async () => {
    mockGetSetting.mockReturnValue("false");
    const updatedBook = { ...mockBook, title: "Updated Title" };
    mockUpdateBook.mockResolvedValue(updatedBook);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // onClose should not be called when auto-dismiss is disabled
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it("should auto-dismiss modal when auto_dismiss_book_edit_modal is null (default true)", async () => {
    mockGetSetting.mockReturnValue(null);
    const updatedBook = { ...mockBook, title: "Updated Title" };
    mockUpdateBook.mockResolvedValue(updatedBook);

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // onUpdateSuccess should be called synchronously within handleSubmit
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should set staged cover URL from temp URL when cover is downloaded", async () => {
    const tempUrl = "/api/books/temp-covers/123";
    let onSuccessCallback: ((tempUrl: string) => void) | undefined;

    vi.mocked(useCoverFromUrl).mockImplementation((options) => {
      onSuccessCallback = options.onSuccess;
      return {
        isLoading: false,
        error: null,
        downloadCover: mockDownloadCover,
        clearError: vi.fn(),
      };
    });

    renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
        onCoverSaved: mockOnCoverSaved,
      }),
    );

    // Simulate cover download success by calling the onSuccess callback
    await act(async () => {
      onSuccessCallback?.(tempUrl);
    });

    // The onSuccess callback should set staged cover URL and call onCoverSaved
    expect(mockSetStagedCoverUrl).toHaveBeenCalledWith(tempUrl);
    expect(mockOnCoverSaved).toHaveBeenCalledWith(1);
  });

  it("should set staged cover URL with cache buster when temp URL is null", async () => {
    let onSuccessCallback: ((tempUrl: string) => void) | undefined;

    vi.mocked(useCoverFromUrl).mockImplementation((options) => {
      onSuccessCallback = options.onSuccess;
      return {
        isLoading: false,
        error: null,
        downloadCover: mockDownloadCover,
        clearError: vi.fn(),
      };
    });

    renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    // The onSuccess callback should use cache-busted URL when tempUrl is null
    // Note: onSuccess expects string, but we test with empty string to simulate null behavior
    await act(async () => {
      onSuccessCallback?.("");
    });

    expect(getCoverUrlWithCacheBuster).toHaveBeenCalledWith(1);
    expect(mockSetStagedCoverUrl).toHaveBeenCalledWith(
      "/api/books/1/cover?t=123",
    );
  });

  it("should not set staged cover URL when bookId is null in onSuccess callback", async () => {
    let onSuccessCallback: ((tempUrl: string) => void) | undefined;

    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    vi.mocked(useCoverFromUrl).mockImplementation((options) => {
      onSuccessCallback = options.onSuccess;
      return {
        isLoading: false,
        error: null,
        downloadCover: mockDownloadCover,
        clearError: vi.fn(),
      };
    });

    renderHook(() =>
      useBookEditForm({
        bookId: null,
        onClose: mockOnClose,
      }),
    );

    await act(async () => {
      onSuccessCallback?.("/api/books/temp-covers/123");
    });

    expect(mockSetStagedCoverUrl).not.toHaveBeenCalled();
    expect(getCoverUrlWithCacheBuster).not.toHaveBeenCalled();
  });

  it("should setup keyboard navigation when book is loaded", () => {
    renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    expect(useKeyboardNavigation).toHaveBeenCalledWith({
      onEscape: expect.any(Function),
      enabled: true,
    });
  });

  it("should disable keyboard navigation when book is loading", () => {
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    expect(useKeyboardNavigation).toHaveBeenCalledWith({
      onEscape: expect.any(Function),
      enabled: false,
    });
  });

  it("should disable keyboard navigation when book is null", () => {
    vi.mocked(useBook).mockReturnValue({
      book: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      updateBook: mockUpdateBook as (
        update: BookUpdate,
      ) => Promise<Book | null>,
      isUpdating: false,
      updateError: null,
    } as ReturnType<typeof useBook>);

    renderHook(() =>
      useBookEditForm({
        bookId: null,
        onClose: mockOnClose,
      }),
    );

    expect(useKeyboardNavigation).toHaveBeenCalledWith({
      onEscape: expect.any(Function),
      enabled: false,
    });
  });

  it("should call handleClose when Escape key is pressed", () => {
    let escapeHandler: (() => void) | undefined;
    vi.mocked(useKeyboardNavigation).mockImplementation((options) => {
      escapeHandler = options.onEscape;
    });

    renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    act(() => {
      escapeHandler?.();
    });

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should handle staged cover URL with http protocol", async () => {
    vi.mocked(useStagedCoverUrl).mockReturnValue({
      stagedCoverUrl: "http://example.com/cover.jpg",
      setStagedCoverUrl: mockSetStagedCoverUrl,
      clearStagedCoverUrl: mockClearStagedCoverUrl,
    });

    const { result } = renderHook(() =>
      useBookEditForm({
        bookId: 1,
        onClose: mockOnClose,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(mockDownloadCover).toHaveBeenCalledWith(
      "http://example.com/cover.jpg",
    );
  });

  describe("handleFeelinLucky", () => {
    beforeEach(() => {
      vi.stubGlobal("fetch", vi.fn());
      // Mock calculateProvidersForBackend to return an array
      vi.mocked(calculateProvidersForBackend).mockReturnValue([
        "google",
        "openlibrary",
      ]);
    });

    it("should not run if book is null", () => {
      vi.mocked(useBook).mockReturnValue({
        book: null,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateBook: mockUpdateBook as (
          update: BookUpdate,
        ) => Promise<Book | null>,
        isUpdating: false,
        updateError: null,
      } as ReturnType<typeof useBook>);

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      act(() => {
        result.current.handleFeelinLucky();
      });

      expect(globalThis.fetch).not.toHaveBeenCalled();
    });

    it("should not run if already searching", () => {
      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      // Set isLuckySearching to true by starting a search
      vi.mocked(getInitialSearchQuery).mockReturnValue("Test Query");
      let _readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          _readCallCount++;
          // Always return done: true immediately to prevent hanging
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };
      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      // Start first search
      act(() => {
        result.current.handleFeelinLucky();
      });

      // Try to start second search immediately after (should be blocked if still searching)
      act(() => {
        result.current.handleFeelinLucky();
      });

      // Should only have been called once (second call should be blocked)
      expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    });

    it("should not run if no search query", () => {
      vi.mocked(getInitialSearchQuery).mockReturnValue("");

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      act(() => {
        result.current.handleFeelinLucky();
      });

      expect(globalThis.fetch).not.toHaveBeenCalled();
    });

    it("should not run if isUpdating is true", () => {
      vi.mocked(useBook).mockReturnValue({
        book: mockBook,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
        updateBook: mockUpdateBook as (
          update: BookUpdate,
        ) => Promise<Book | null>,
        isUpdating: true,
        updateError: null,
      } as ReturnType<typeof useBook>);

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      act(() => {
        result.current.handleFeelinLucky();
      });

      expect(globalThis.fetch).not.toHaveBeenCalled();
    });

    it("should handle response not ok", async () => {
      const mockResponse = {
        ok: false,
        text: vi.fn().mockResolvedValue("Error message"),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Lucky search failed:",
        "Error message",
      );

      consoleErrorSpy.mockRestore();
    });

    it("should handle response with no body", async () => {
      const mockResponse = {
        ok: true,
        body: null,
        text: vi.fn().mockResolvedValue(""),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Lucky search failed:",
        "Failed to open stream",
      );

      consoleErrorSpy.mockRestore();
    });

    it("should handle response.text() failure", async () => {
      const mockResponse = {
        ok: false,
        text: vi.fn().mockRejectedValue(new Error("Text parse failed")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Lucky search failed:",
        "Failed to open stream",
      );

      consoleErrorSpy.mockRestore();
    });

    it("should handle search.progress event with results", async () => {
      const metadataRecord: MetadataRecord = {
        title: "Found Book",
        authors: ["Found Author"],
        cover_url: "https://example.com/cover.jpg",
        source_id: "test",
        external_id: "123",
        url: "https://example.com/book",
      };

      const encoder = new TextEncoder();
      const sseData = encoder.encode(
        'data: {"event":"search.progress","results":[{"title":"Found Book","authors":["Found Author"],"cover_url":"https://example.com/cover.jpg","source_id":"test","external_id":"123","url":"https://example.com/book"}]}\n\n',
      );

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).toHaveBeenCalledWith(
        metadataRecord,
      );
      expect(applyBookUpdateToForm).toHaveBeenCalled();
      expect(mockReader.cancel).toHaveBeenCalled();
    });

    it("should handle search.progress event with empty results array", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode(
        'data: {"event":"search.progress","results":[]}\n\n',
      );

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).not.toHaveBeenCalled();
      expect(applyBookUpdateToForm).not.toHaveBeenCalled();
    });

    it("should handle search.progress event with non-array results", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode(
        'data: {"event":"search.progress","results":{}}\n\n',
      );

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).not.toHaveBeenCalled();
      expect(applyBookUpdateToForm).not.toHaveBeenCalled();
    });

    it("should handle search.completed event with results", async () => {
      const metadataRecord: MetadataRecord = {
        title: "Completed Book",
        authors: ["Completed Author"],
        cover_url: "https://example.com/cover.jpg",
        source_id: "test",
        external_id: "456",
        url: "https://example.com/book2",
      };

      const encoder = new TextEncoder();
      const sseData = encoder.encode(
        'data: {"event":"search.completed","results":[{"title":"Completed Book","authors":["Completed Author"],"cover_url":"https://example.com/cover.jpg","source_id":"test","external_id":"456","url":"https://example.com/book2"}]}\n\n',
      );

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).toHaveBeenCalledWith(
        metadataRecord,
      );
      expect(applyBookUpdateToForm).toHaveBeenCalled();
      expect(mockReader.cancel).toHaveBeenCalled();
    });

    it("should handle search.completed event with no results", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode(
        'data: {"event":"search.completed","results":[]}\n\n',
      );

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleInfoSpy = vi
        .spyOn(console, "info")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).not.toHaveBeenCalled();
      expect(applyBookUpdateToForm).not.toHaveBeenCalled();
      expect(consoleInfoSpy).toHaveBeenCalledWith(
        "No metadata results found for lucky search",
      );
      expect(mockReader.cancel).toHaveBeenCalled();

      consoleInfoSpy.mockRestore();
    });

    it("should handle search.completed event with non-array results", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode(
        'data: {"event":"search.completed","results":{}}\n\n',
      );

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleInfoSpy = vi
        .spyOn(console, "info")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).not.toHaveBeenCalled();
      expect(applyBookUpdateToForm).not.toHaveBeenCalled();
      expect(consoleInfoSpy).toHaveBeenCalledWith(
        "No metadata results found for lucky search",
      );

      consoleInfoSpy.mockRestore();
    });

    it("should handle JSON parse error in SSE stream", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode("data: invalid json\n\n");

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Lucky search parse error:",
        expect.any(String),
      );
      expect(mockReader.cancel).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it("should handle non-Error exception in JSON parse catch block", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode("data: test\n\n");

      // Mock JSON.parse to throw a non-Error value
      const parseSpy = vi.spyOn(JSON, "parse").mockImplementation(() => {
        // Throw a non-Error value to test the defensive check
        throw "String error";
      });

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Lucky search parse error:",
        "Failed to parse event",
      );
      expect(mockReader.cancel).toHaveBeenCalled();

      parseSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });

    it("should handle stream ending without results", async () => {
      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).not.toHaveBeenCalled();
      expect(applyBookUpdateToForm).not.toHaveBeenCalled();
    });

    it("should handle AbortError", async () => {
      const abortError = new Error("Aborted");
      abortError.name = "AbortError";

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
        abortError,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
    });

    it("should handle other errors", async () => {
      const error = new Error("Network error");
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(error);

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Lucky search failed:",
        "Network error",
      );

      consoleErrorSpy.mockRestore();
    });

    it("should handle non-Error rejection", async () => {
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
        "String error",
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Lucky search failed:",
        "Failed to search metadata",
      );

      consoleErrorSpy.mockRestore();
    });

    it("should handle empty providersForBackend", async () => {
      vi.mocked(calculateProvidersForBackend).mockReturnValue([]);

      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls[0];
      if (fetchCall?.[0]) {
        const url = new URL(fetchCall[0] as string);
        expect(url.searchParams.has("enable_providers")).toBe(false);
      }
    });

    it("should handle empty dataStr in SSE line", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode("data: \n\n");

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).not.toHaveBeenCalled();
      expect(applyBookUpdateToForm).not.toHaveBeenCalled();
    });

    it("should handle lines not starting with 'data: '", async () => {
      const encoder = new TextEncoder();
      const sseData = encoder.encode("event: ping\n\n");

      let readCallCount = 0;
      const mockReader = {
        read: vi.fn().mockImplementation(async () => {
          readCallCount++;
          if (readCallCount === 1) {
            return { done: false, value: sseData };
          }
          return { done: true, value: undefined };
        }),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(convertMetadataRecordToBookUpdate).not.toHaveBeenCalled();
      expect(applyBookUpdateToForm).not.toHaveBeenCalled();
    });

    it("should handle reader cleanup in finally block", async () => {
      const mockReader = {
        read: vi.fn().mockRejectedValue(new Error("Read error")),
        cancel: vi.fn().mockResolvedValue(undefined),
      };

      const mockResponse = {
        ok: true,
        body: {
          getReader: vi.fn().mockReturnValue(mockReader),
        },
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const { result } = renderHook(() =>
        useBookEditForm({
          bookId: 1,
          onClose: mockOnClose,
        }),
      );

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      await act(async () => {
        await result.current.handleFeelinLucky();
      });

      expect(result.current.isLuckySearching).toBe(false);
      expect(mockReader.cancel).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });
});
