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

import { useCallback, useState } from "react";
import { uploadFormat } from "@/services/formatService";

/**
 * Options for format upload hook.
 */
export interface UseFormatUploadOptions {
  /** Book ID to upload format for. */
  bookId: number;
  /** Callback when upload succeeds. */
  onSuccess?: () => void;
  /** Callback when upload fails. */
  onError?: (error: Error) => void;
}

/**
 * Result of format upload hook.
 */
export interface UseFormatUploadResult {
  /** Whether upload is in progress. */
  isUploading: boolean;
  /** Whether replace confirmation modal should be shown. */
  showReplaceModal: boolean;
  /** Pending file waiting for replace confirmation. */
  pendingFile: File | null;
  /** Upload a file. */
  upload: (file: File, replace?: boolean) => Promise<void>;
  /** Confirm replace operation. */
  confirmReplace: () => Promise<void>;
  /** Cancel replace operation. */
  cancelReplace: () => void;
  /** Error message if upload failed. */
  error: string | null;
}

/**
 * Custom hook for managing format upload workflow.
 *
 * Handles file upload, conflict detection, and replace confirmation.
 * Follows SRP by separating upload business logic from UI.
 * Follows IOC by using injectable service layer.
 *
 * Parameters
 * ----------
 * options : UseFormatUploadOptions
 *     Configuration including book ID and callbacks.
 *
 * Returns
 * -------
 * UseFormatUploadResult
 *     Upload state and control functions.
 */
export function useFormatUpload({
  bookId,
  onSuccess,
  onError,
}: UseFormatUploadOptions): UseFormatUploadResult {
  const [isUploading, setIsUploading] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [showReplaceModal, setShowReplaceModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (file: File, replace: boolean = false) => {
      setIsUploading(true);
      setError(null);
      try {
        const result = await uploadFormat(bookId, file, replace);

        if (result.status === "conflict") {
          setPendingFile(file);
          setShowReplaceModal(true);
          return;
        }

        // Success
        setPendingFile(null);
        setShowReplaceModal(false);
        onSuccess?.();
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to upload format";
        setError(errorMessage);
        onError?.(err instanceof Error ? err : new Error(errorMessage));
      } finally {
        setIsUploading(false);
      }
    },
    [bookId, onSuccess, onError],
  );

  const confirmReplace = useCallback(async () => {
    if (pendingFile) {
      await upload(pendingFile, true);
    }
  }, [pendingFile, upload]);

  const cancelReplace = useCallback(() => {
    setShowReplaceModal(false);
    setPendingFile(null);
  }, []);

  return {
    isUploading,
    showReplaceModal,
    pendingFile,
    upload,
    confirmReplace,
    cancelReplace,
    error,
  };
}
