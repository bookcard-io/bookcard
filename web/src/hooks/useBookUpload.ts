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
import { getBookFormatsAcceptString } from "@/constants/bookFormats";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useBookUploadOrchestrator } from "./useBookUploadOrchestrator";
import { useFileUpload } from "./useFileUpload";
import { useTaskPolling } from "./useTaskPolling";

export interface UseBookUploadOptions {
  /**
   * Callback fired when a book is successfully uploaded.
   *
   * Parameters
   * ----------
   * bookId : number
   *     ID of the newly uploaded book.
   */
  onUploadSuccess?: (bookId: number) => void;
  /**
   * Callback fired when a book is added (for multi-upload, no modal).
   * If provided, this will be used instead of onUploadSuccess for multi-file uploads.
   *
   * Parameters
   * ----------
   * bookId : number
   *     ID of the newly uploaded book.
   */
  onBookAdded?: (bookId: number) => void;
  /**
   * Callback fired when upload fails.
   *
   * Parameters
   * ----------
   * error : string
   *     Error message.
   */
  onUploadError?: (error: string) => void;
}

export interface UseBookUploadResult {
  /**
   * Ref to attach to the hidden file input element.
   */
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  /**
   * Whether an upload is currently in progress.
   */
  isUploading: boolean;
  /**
   * Opens the file browser dialog.
   */
  openFileBrowser: () => void;
  /**
   * Handler for file input change event.
   */
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /**
   * Accepted file extensions for book formats.
   */
  accept: string;
}

/**
 * Custom hook for book upload functionality.
 *
 * Handles file selection, upload to server, and success/error callbacks.
 * Follows SRP by handling only book upload concerns.
 * Follows IOC by accepting callbacks for upload results.
 *
 * Parameters
 * ----------
 * options : UseBookUploadOptions
 *     Configuration options for book upload.
 *
 * Returns
 * -------
 * UseBookUploadResult
 *     Object containing refs, state, and event handlers.
 */
export function useBookUpload(
  options: UseBookUploadOptions = {},
): UseBookUploadResult {
  const { onUploadSuccess, onBookAdded, onUploadError } = options;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Track if we're in a multi-file upload session to suppress modals
  const isMultiFileUploadRef = useRef(false);
  const multiFileTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Global message publisher (SRP: message dispatch, independent of UI position)
  const { showSuccess, showDanger } = useGlobalMessages();

  const showSuccessMessage = useCallback(
    (message: string) => {
      showSuccess(message, { durationMs: 2000 });
    },
    [showSuccess],
  );

  const showErrorMessage = useCallback(
    (message: string) => {
      showDanger(message, { durationMs: 5000 });
    },
    [showDanger],
  );

  // File upload (SRP: upload API calls)
  const fileUpload = useFileUpload({
    onUploadStart: () => setIsUploading(true),
    onUploadComplete: () => setIsUploading(false),
    onError: onUploadError,
    onSetErrorMessage: showErrorMessage,
  });

  // Task polling (SRP: polling logic)
  // Note: onSuccess is not set here because the orchestrator handles success
  // via handleBookIds, which ensures consistent message handling for both sync and async uploads
  const taskPolling = useTaskPolling({
    onError: onUploadError,
    onSetErrorMessage: showErrorMessage,
  });

  // Upload orchestrator (SRP: workflow coordination)
  const orchestrator = useBookUploadOrchestrator({
    fileUpload,
    taskPolling,
    onSetErrorMessage: showErrorMessage,
    onSetSuccessMessage: showSuccessMessage,
    onUploadSuccess,
    onBookAdded,
    onUploadError,
    getIsMultiFileUpload: () => isMultiFileUploadRef.current,
  });

  const openFileBrowser = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length === 0) {
        return;
      }

      // Track if this is a multi-file upload to suppress modals
      const isMultiFile = files.length > 1;

      // Clear any existing timeout
      if (multiFileTimeoutRef.current) {
        clearTimeout(multiFileTimeoutRef.current);
      }

      isMultiFileUploadRef.current = isMultiFile;

      // Upload files in parallel - each upload unblocks the button once file is sent
      // Polling continues in the background without blocking the UI
      for (const file of files) {
        // Fire and forget - each upload will unblock itself once file is sent to server
        void orchestrator.uploadBook(file);
      }

      // Reset the flag after a delay to allow polling callbacks to check it
      // The flag is checked during polling when bookIds are extracted
      // We keep it set for a reasonable duration to cover typical polling time
      if (isMultiFile) {
        multiFileTimeoutRef.current = setTimeout(() => {
          isMultiFileUploadRef.current = false;
          multiFileTimeoutRef.current = null;
        }, 300000); // 5 minutes - covers typical polling duration
      } else {
        // Single file - reset immediately (modal will show)
        isMultiFileUploadRef.current = false;
      }

      // Reset input to allow selecting the same file again immediately
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [orchestrator],
  );

  // Use shared constant for supported formats (single source of truth)
  const accept = getBookFormatsAcceptString();

  return {
    fileInputRef,
    isUploading,
    openFileBrowser,
    handleFileChange,
    accept,
  };
}
