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

/**Custom hook for multi-file book uploads.

Handles multiple file uploads with progress tracking via background tasks.
Follows SRP by focusing solely on multi-file upload concerns.
Follows IOC by accepting callbacks for success/error handling.
*/

import { useCallback, useRef, useState } from "react";
import { getBookFormatsAcceptString } from "@/constants/bookFormats";

export interface UseMultiBookUploadOptions {
  /**Callback when upload task is created successfully. */
  onUploadStart?: (taskId: number, fileCount: number) => void;
  /**Callback when upload completes. */
  onUploadSuccess?: (taskId: number) => void;
  /**Callback when upload fails. */
  onUploadError?: (error: string) => void;
}

export interface UseMultiBookUploadResult {
  /**Upload multiple files. */
  uploadBooks: (files: File[]) => Promise<void>;
  /**Whether upload is in progress. */
  isUploading: boolean;
  /**Error message if upload failed. */
  error: string | null;
  /**Task ID of current upload. */
  taskId: number | null;
  /**Clear error message. */
  clearError: () => void;
  /**File input props for use with input element. */
  fileInputProps: {
    multiple: true;
    accept: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  };
}

/**
 * Hook for uploading multiple book files.
 *
 * Parameters
 * ----------
 * options : UseMultiBookUploadOptions
 *     Configuration including callbacks.
 *
 * Returns
 * -------
 * UseMultiBookUploadResult
 *     Upload function, state, and file input props.
 */
export function useMultiBookUpload(
  options: UseMultiBookUploadOptions = {},
): UseMultiBookUploadResult {
  const { onUploadStart, onUploadError } = options;

  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const isUploadingRef = useRef(false);

  const uploadBooks = useCallback(
    async (files: File[]): Promise<void> => {
      if (files.length === 0) {
        return;
      }

      if (isUploadingRef.current) {
        return;
      }

      isUploadingRef.current = true;
      setIsUploading(true);
      setError(null);
      setTaskId(null);

      try {
        const formData = new FormData();
        for (const file of files) {
          // Create a fresh copy of the file to avoid stream locking issues
          // when the same file is selected multiple times
          const freshFile = new File([file], file.name, {
            type: file.type,
            lastModified: file.lastModified,
          });
          formData.append("files", freshFile);
        }

        const response = await fetch("/api/books/upload/batch", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          const errorMessage = errorData.detail || "Failed to upload books";
          setError(errorMessage);
          onUploadError?.(errorMessage);
          return;
        }

        const data = (await response.json()) as {
          task_id: number;
          total_files: number;
        };
        setTaskId(data.task_id);
        onUploadStart?.(data.task_id, data.total_files);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to upload books";
        setError(message);
        onUploadError?.(message);
      } finally {
        isUploadingRef.current = false;
        setIsUploading(false);
      }
    },
    [onUploadStart, onUploadError],
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) {
        void uploadBooks(files);
      }
      // Reset input to allow selecting the same files again
      e.target.value = "";
    },
    [uploadBooks],
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    uploadBooks,
    isUploading,
    error,
    taskId,
    clearError,
    fileInputProps: {
      multiple: true,
      // Use shared constant for supported formats (single source of truth)
      accept: getBookFormatsAcceptString(),
      onChange: handleFileChange,
    },
  };
}
