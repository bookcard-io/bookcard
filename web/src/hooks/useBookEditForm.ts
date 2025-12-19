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

import { useCallback, useRef, useState } from "react";
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
import type { Book } from "@/types/book";
import { getCoverUrlWithCacheBuster } from "@/utils/books";
import {
  applyBookUpdateToForm,
  calculateProvidersForBackend,
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
  /** React Hook Form instance. */
  form: ReturnType<typeof useBookForm>["form"];
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
  /** Whether lucky search is in progress. */
  isLuckySearching: boolean;
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
  /** Handler for 'I'm feelin' lucky!' button. */
  handleFeelinLucky: () => Promise<void>;
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
    form,
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
  const [isLuckySearching, setIsLuckySearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { stagedCoverUrl, setStagedCoverUrl, clearStagedCoverUrl } =
    useStagedCoverUrl({
      bookId,
    });

  // Get provider settings for lucky search
  const { enabledProviders } = useProviderSettings();
  const { preferredProviders } = usePreferredProviders();

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
   * Handles 'I'm feelin' lucky!' button click.
   *
   * Automatically searches for metadata using SSE stream and applies the first result
   * as soon as it arrives. Cancels the search immediately after getting the first result.
   * Uses the same provider settings as the metadata modal.
   */
  const handleFeelinLucky = useCallback(async () => {
    if (!book || isLuckySearching || isUpdating) {
      return;
    }

    // Get search query from book/form data
    const formValues = form.getValues();
    const searchQuery = getInitialSearchQuery(book, formValues);
    if (!searchQuery.trim()) {
      // eslint-disable-next-line no-console
      console.warn("No search query available for lucky search");
      return;
    }

    setIsLuckySearching(true);

    // Calculate providers to use (preferred AND enabled)
    const providersForBackend = calculateProvidersForBackend(
      preferredProviders,
      enabledProviders,
    );

    // Build SSE stream URL
    const url = new URL("/api/metadata/search/stream", window.location.origin);
    url.searchParams.set("query", searchQuery);
    url.searchParams.set("locale", "en");
    url.searchParams.set("max_results_per_provider", "20"); // Get enough results to find a good first one
    if (providersForBackend.length > 0) {
      url.searchParams.set("enable_providers", providersForBackend.join(","));
    }
    url.searchParams.set(
      "request_id",
      `req_${Date.now()}_${Math.random().toString(36).substring(7)}`,
    );

    const abortController = new AbortController();
    let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;

    try {
      // Fetch SSE stream
      const response = await fetch(url.toString(), {
        signal: abortController.signal,
        headers: {
          Accept: "text/event-stream",
        },
      });

      if (!response.ok || !response.body) {
        const text = await response.text().catch(() => "Failed to open stream");
        throw new Error(text || "Failed to open stream");
      }

      reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      // Parse SSE stream and cancel as soon as first result arrives
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (dataStr) {
              try {
                const data = JSON.parse(dataStr) as {
                  event: string;
                  results?: MetadataRecord[];
                };

                // Check for search.progress event with results
                if (data.event === "search.progress" && data.results) {
                  const results = Array.isArray(data.results)
                    ? data.results
                    : [];
                  const firstResult = results[0];
                  if (firstResult) {
                    // Got first result! Cancel search and apply it
                    reader.cancel().catch(() => {
                      // Ignore cancellation errors
                    });
                    abortController.abort();
                    handleSelectMetadata(firstResult);
                    setIsLuckySearching(false);
                    return;
                  }
                }

                // Check for search.completed event
                if (data.event === "search.completed") {
                  const results = Array.isArray(data.results)
                    ? data.results
                    : [];
                  const firstResult = results[0];
                  if (firstResult) {
                    handleSelectMetadata(firstResult);
                  } else {
                    // eslint-disable-next-line no-console
                    console.info("No metadata results found for lucky search");
                  }
                  reader.cancel().catch(() => {
                    // Ignore cancellation errors
                  });
                  abortController.abort();
                  setIsLuckySearching(false);
                  return;
                }
              } catch (error) {
                const message =
                  error instanceof Error
                    ? error.message
                    : "Failed to parse event";
                // eslint-disable-next-line no-console
                console.error("Lucky search parse error:", message);
                reader.cancel().catch(() => {
                  // Ignore cancellation errors
                });
                abortController.abort();
                setIsLuckySearching(false);
                return;
              }
            }
          }
        }
      }

      // Stream ended without results
      setIsLuckySearching(false);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        // Search was cancelled (expected when we get first result)
        setIsLuckySearching(false);
        return;
      }
      // Error handling
      const message =
        error instanceof Error ? error.message : "Failed to search metadata";
      // eslint-disable-next-line no-console
      console.error("Lucky search failed:", message);
      setIsLuckySearching(false);
    } finally {
      // Cleanup
      if (reader) {
        reader.cancel().catch(() => {
          // Ignore cancellation errors
        });
      }
      abortController.abort();
    }
  }, [
    book,
    form,
    isLuckySearching,
    isUpdating,
    preferredProviders,
    enabledProviders,
    handleSelectMetadata,
  ]);

  /**
   * Wraps form submit to handle staged cover URL before submission.
   *
   * If there's a staged cover URL (from metadata selection), download it
   * before submitting the form. This ensures the cover is saved when the
   * user clicks Save, not when they select the metadata.
   */
  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<boolean> => {
      e.preventDefault();
      setIsSubmitting(true);

      try {
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
        const success = await handleFormSubmit(e);

        // Only stop submitting if validation failed or an error occurred.
        // If successful, we want to keep the spinner while the modal dismisses
        // (which happens in onUpdateSuccess callback in useBookForm)
        if (!success) {
          setIsSubmitting(false);
        }
        return success;
      } catch (_err) {
        setIsSubmitting(false);
        return false;
      }
    },
    [handleFormSubmit, stagedCoverUrl, bookId, downloadCoverFromUrl],
  );

  return {
    book,
    isLoading,
    error,
    form,
    hasChanges,
    showSuccess,
    isUpdating: isUpdating || isSubmitting,
    updateError,
    stagedCoverUrl,
    showMetadataModal,
    isLuckySearching,
    handleFieldChange,
    handleSubmit,
    handleClose,
    handleOpenMetadataModal,
    handleCloseMetadataModal,
    handleSelectMetadata,
    handleFeelinLucky,
    handleCoverSaved,
  };
}
