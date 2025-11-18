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

/**Orchestrator hook for book upload workflow.

Follows SRP by coordinating upload, polling, and callbacks.
Follows IOC by accepting dependencies via options.
*/

import { useCallback } from "react";
import type { UseFileUploadResult } from "./useFileUpload";
import type { UseTaskPollingResult } from "./useTaskPolling";

export interface UseBookUploadOrchestratorOptions {
  /**File upload hook result. */
  fileUpload: UseFileUploadResult;
  /**Task polling hook result. */
  taskPolling: UseTaskPollingResult;
  /**Callback to set a success message for display. */
  onSetSuccessMessage?: (message: string) => void;
  /**Callback to set an error message for display. */
  onSetErrorMessage?: (message: string) => void;
  /**Callback when single book upload succeeds (shows modal). */
  onUploadSuccess?: (bookId: number) => void;
  /**Callback when book is added (multi-upload, no modal). */
  onBookAdded?: (bookId: number) => void;
  /**Callback when upload fails. */
  onUploadError?: (error: string) => void;
  /**Getter function to check if we're in a multi-file upload session. */
  getIsMultiFileUpload: () => boolean;
}

export interface UseBookUploadOrchestratorResult {
  /**Upload a book file and handle the workflow. */
  uploadBook: (file: File) => Promise<void>;
}

/**
 * Orchestrator hook for book upload workflow.
 *
 * Coordinates file upload, task polling, and success/error handling.
 * Follows SRP by orchestrating the upload workflow.
 * Follows IOC by accepting dependencies via options.
 *
 * Parameters
 * ----------
 * options : UseBookUploadOrchestratorOptions
 *     Configuration including hooks and callbacks.
 *
 * Returns
 * -------
 * UseBookUploadOrchestratorResult
 *     Upload function.
 */
export function useBookUploadOrchestrator(
  options: UseBookUploadOrchestratorOptions,
): UseBookUploadOrchestratorResult {
  const {
    fileUpload,
    taskPolling,
    onSetSuccessMessage,
    onSetErrorMessage,
    onUploadSuccess,
    onBookAdded,
    onUploadError,
    getIsMultiFileUpload,
  } = options;

  /**
   * Handle successful book upload with book IDs.
   */
  const handleBookIds = useCallback(
    (bookIds: number[]) => {
      onSetSuccessMessage?.("Books processed! ✅");

      const isMultiFile = getIsMultiFileUpload();
      if (isMultiFile) {
        // Multi-file upload - add all books without modal
        for (const bookId of bookIds) {
          onBookAdded?.(bookId);
        }
      } else if (bookIds.length === 1 && bookIds[0] !== undefined) {
        // Single file upload - show modal
        onUploadSuccess?.(bookIds[0]);
      } else {
        // Multi-book from single task - use onBookAdded (no modal)
        for (const bookId of bookIds) {
          onBookAdded?.(bookId);
        }
      }
    },
    [getIsMultiFileUpload, onSetSuccessMessage, onUploadSuccess, onBookAdded],
  );

  const uploadBook = useCallback(
    async (file: File): Promise<void> => {
      const response = await fileUpload.uploadFile(file);

      if (!response) {
        return; // Error already handled by fileUpload
      }

      // Synchronous upload - book_ids available immediately
      if (response.book_ids && response.book_ids.length > 0) {
        handleBookIds(response.book_ids);
        return;
      }

      // Asynchronous upload - poll task and handle success
      if (response.task_id) {
        // Show processing message when async upload starts
        if (!response.book_ids) {
          onSetSuccessMessage?.("🚀 Now processing...");
        }
        const bookIds = await taskPolling.pollTask(response.task_id);
        if (bookIds && bookIds.length > 0) {
          handleBookIds(bookIds);
        }
        return;
      }

      // Invalid response
      const errorMsg = "Upload response missing both book_ids and task_id";
      onSetErrorMessage?.(errorMsg);
      onUploadError?.(errorMsg);
    },
    [
      fileUpload,
      taskPolling,
      onSetErrorMessage,
      onSetSuccessMessage,
      handleBookIds,
      onUploadError,
    ],
  );

  return {
    uploadBook,
  };
}
