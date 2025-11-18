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

/**Custom hook for file upload operations.

Follows SRP by focusing solely on file upload API calls.
Follows IOC by accepting callbacks as dependencies.
*/

import { useCallback } from "react";

export interface FileUploadResponse {
  /**Book IDs if upload completed synchronously. */
  book_ids: number[] | null;
  /**Task ID if upload is asynchronous. */
  task_id: number | null;
}

export interface UseFileUploadOptions {
  /**Callback when upload starts. */
  onUploadStart?: () => void;
  /**Callback when upload completes (file sent to server). */
  onUploadComplete?: () => void;
  /**Callback when upload fails. */
  onError?: (error: string) => void;
  /**Callback to set error message for display. */
  onSetErrorMessage?: (message: string) => void;
}

export interface UseFileUploadResult {
  /**Upload a file to the server. */
  uploadFile: (file: File) => Promise<FileUploadResponse | null>;
}

/**
 * Hook for uploading files to the server.
 *
 * Handles file upload API calls and response parsing.
 * Follows SRP by handling only upload logic.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseFileUploadOptions
 *     Configuration including callbacks.
 *
 * Returns
 * -------
 * UseFileUploadResult
 *     Upload function.
 */
export function useFileUpload(
  options: UseFileUploadOptions = {},
): UseFileUploadResult {
  const { onUploadStart, onUploadComplete, onError, onSetErrorMessage } =
    options;

  /**
   * Create a fresh copy of the file to avoid stream locking issues.
   */
  const createFreshFile = useCallback(async (file: File): Promise<File> => {
    const fileBuffer = await file.arrayBuffer();
    return new File([fileBuffer], file.name, {
      type: file.type,
      lastModified: file.lastModified,
    });
  }, []);

  const uploadFile = useCallback(
    async (file: File): Promise<FileUploadResponse | null> => {
      onUploadStart?.();

      try {
        const freshFile = await createFreshFile(file);

        const formData = new FormData();
        formData.append("file", freshFile);

        const response = await fetch("/api/books/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          let errorMessage = `Upload failed with status ${response.status}`;
          try {
            const data = (await response.json()) as { detail?: string };
            if (data.detail) {
              errorMessage = data.detail;
            }
          } catch {
            // If JSON parsing fails, use the default status-based message
          }

          onSetErrorMessage?.(errorMessage);
          onError?.(errorMessage);
          return null;
        }

        const data = (await response.json()) as FileUploadResponse;
        onUploadComplete?.();

        return data;
      } catch (error) {
        const errorMsg =
          error instanceof Error ? error.message : "Upload failed";
        onSetErrorMessage?.(errorMsg);
        onError?.(errorMsg);
        return null;
      }
    },
    [
      createFreshFile,
      onUploadStart,
      onUploadComplete,
      onError,
      onSetErrorMessage,
    ],
  );

  return {
    uploadFile,
  };
}
