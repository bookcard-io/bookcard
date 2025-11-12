import { useCallback, useRef, useState } from "react";
import { useUser } from "@/contexts/UserContext";
import { useBook } from "@/hooks/useBook";
import { useBookForm } from "@/hooks/useBookForm";
import { useCoverFromUrl } from "@/hooks/useCoverFromUrl";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { useStagedCoverUrl } from "@/hooks/useStagedCoverUrl";
import type { Book } from "@/types/book";
import { getCoverUrlWithCacheBuster } from "@/utils/books";
import {
  applyBookUpdateToForm,
  convertMetadataRecordToBookUpdate,
} from "@/utils/metadata";

export interface UseBookEditFormOptions {
  /** Book ID to edit. */
  bookId: number | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when cover is saved (for updating grid). */
  onCoverSaved?: (bookId: number) => void;
  /** Callback when book is saved (for updating grid). */
  onBookSaved?: (book: Book) => void;
}

export interface UseBookEditFormResult {
  /** Book data. */
  book: Book | null;
  /** Whether book data is loading. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Form data. */
  formData: ReturnType<typeof useBookForm>["formData"];
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Whether update was successful. */
  showSuccess: boolean;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Error message if update failed. */
  updateError: string | null;
  /** Currently staged cover URL. */
  stagedCoverUrl: string | null;
  /** Whether metadata modal is visible. */
  showMetadataModal: boolean;
  /** Handler for field changes. */
  handleFieldChange: ReturnType<typeof useBookForm>["handleFieldChange"];
  /** Handler for form submission. */
  handleSubmit: ReturnType<typeof useBookForm>["handleSubmit"];
  /** Handler for closing the modal (with cleanup). */
  handleClose: () => void;
  /** Handler for opening metadata modal. */
  handleOpenMetadataModal: () => void;
  /** Handler for closing metadata modal. */
  handleCloseMetadataModal: () => void;
  /** Handler for selecting metadata record. */
  handleSelectMetadata: (record: MetadataRecord) => void;
  /** Handler for cover save completion. */
  handleCoverSaved: () => void;
}

/**
 * Custom hook for managing book edit form business logic.
 *
 * Handles book data fetching, form state management, metadata selection,
 * and form lifecycle. Follows SRP by separating form logic from modal state.
 * Uses IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseBookEditFormOptions
 *     Configuration including book ID and callbacks.
 *
 * Returns
 * -------
 * UseBookEditFormResult
 *     Form state and all handlers needed for the form UI.
 */
export function useBookEditForm({
  bookId,
  onClose,
  onCoverSaved,
  onBookSaved,
}: UseBookEditFormOptions): UseBookEditFormResult {
  const { book, isLoading, error, updateBook, isUpdating, updateError } =
    useBook({
      bookId: bookId || 0,
      enabled: bookId !== null,
      full: true,
    });

  const { getSetting } = useUser();

  // Use ref to store close handler so it can be accessed in onUpdateSuccess
  const handleCloseRef = useRef<(() => void) | null>(null);

  const {
    formData,
    hasChanges,
    showSuccess,
    handleFieldChange,
    handleSubmit: handleFormSubmit,
    resetForm,
  } = useBookForm({
    book,
    updateBook,
    onUpdateSuccess: (updatedBook) => {
      if (onBookSaved) {
        onBookSaved(updatedBook);
      }
      // Clear staged cover after book data is refreshed
      // This prevents the flash of old cover
      clearStagedCoverUrl();
      // Check if auto-dismiss is enabled
      const autoDismiss = getSetting("auto_dismiss_book_edit_modal");
      if (autoDismiss !== "false") {
        // Default to true if setting is not set
        handleCloseRef.current?.();
      }
    },
  });

  const [showMetadataModal, setShowMetadataModal] = useState(false);

  const { stagedCoverUrl, setStagedCoverUrl, clearStagedCoverUrl } =
    useStagedCoverUrl({
      bookId,
    });

  /**
   * Handles cover save completion.
   */
  const handleCoverSaved = useCallback(() => {
    if (bookId && onCoverSaved) {
      onCoverSaved(bookId);
    }
  }, [bookId, onCoverSaved]);

  const { downloadCover: downloadCoverFromUrl } = useCoverFromUrl({
    bookId: bookId || 0,
    onSuccess: (tempUrl) => {
      // Update staged cover to the new cover URL to prevent flash
      // The staged cover will be cleared after book data is refreshed
      if (bookId !== null) {
        // Use the temp URL from API, or generate cache-busted URL
        const newCoverUrl = tempUrl || getCoverUrlWithCacheBuster(bookId);
        setStagedCoverUrl(newCoverUrl);
      }
      handleCoverSaved();
    },
  });

  /**
   * Handles metadata record selection and populates the form.
   *
   * Parameters
   * ----------
   * record : MetadataRecord
   *     Metadata record from external source.
   */
  const handleSelectMetadata = useCallback(
    (record: MetadataRecord) => {
      const update = convertMetadataRecordToBookUpdate(record);
      applyBookUpdateToForm(update, handleFieldChange);
      setShowMetadataModal(false);

      // Check if cover replacement is enabled
      const replaceCoverSetting = getSetting(
        "replace_cover_on_metadata_selection",
      );
      const shouldReplaceCover = replaceCoverSetting === "true";
      if (shouldReplaceCover && record.cover_url && bookId !== null) {
        // Stage the cover URL without saving to backend
        // User can cancel to discard the staged cover
        setStagedCoverUrl(record.cover_url);
      }
    },
    [handleFieldChange, getSetting, bookId, setStagedCoverUrl],
  );

  /**
   * Handles closing the modal with cleanup.
   */
  const handleClose = useCallback(() => {
    resetForm();
    clearStagedCoverUrl();
    onClose();
  }, [resetForm, clearStagedCoverUrl, onClose]);

  // Update ref whenever handleClose changes
  handleCloseRef.current = handleClose;

  /**
   * Handles Escape key press to close modal.
   */
  const handleEscape = useCallback(() => {
    handleClose();
  }, [handleClose]);

  // Setup keyboard navigation
  useKeyboardNavigation({
    onEscape: handleEscape,
    enabled: !isLoading && !!book && bookId !== null,
  });

  /**
   * Handles opening the metadata modal.
   */
  const handleOpenMetadataModal = useCallback(() => {
    setShowMetadataModal(true);
  }, []);

  /**
   * Handles closing the metadata modal.
   */
  const handleCloseMetadataModal = useCallback(() => {
    setShowMetadataModal(false);
  }, []);

  /**
   * Wraps form submit to handle staged cover URL before submission.
   *
   * If there's a staged cover URL (from metadata selection), download it
   * before submitting the form. This ensures the cover is saved when the
   * user clicks Save, not when they select the metadata.
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      // If there's a staged cover URL, download it first
      // Check if it's an external URL (not a temp URL from backend)
      if (
        stagedCoverUrl &&
        bookId !== null &&
        !stagedCoverUrl.startsWith("/api/books/temp-covers/") &&
        !stagedCoverUrl.startsWith("/api/books/") &&
        (stagedCoverUrl.startsWith("http://") ||
          stagedCoverUrl.startsWith("https://"))
      ) {
        try {
          await downloadCoverFromUrl(stagedCoverUrl);
        } catch (err) {
          // Error is handled by useCoverFromUrl hook
          // Continue with form submission even if cover download fails
          // eslint-disable-next-line no-console
          console.error("Failed to download staged cover:", err);
        }
      }

      // Submit the form after cover is downloaded (or if no staged cover)
      await handleFormSubmit(e);
    },
    [handleFormSubmit, stagedCoverUrl, bookId, downloadCoverFromUrl],
  );

  return {
    book,
    isLoading,
    error,
    formData,
    hasChanges,
    showSuccess,
    isUpdating,
    updateError,
    stagedCoverUrl,
    showMetadataModal,
    handleFieldChange,
    handleSubmit,
    handleClose,
    handleOpenMetadataModal,
    handleCloseMetadataModal,
    handleSelectMetadata,
    handleCoverSaved,
  };
}
