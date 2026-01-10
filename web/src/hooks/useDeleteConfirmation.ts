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

import { useCallback, useEffect, useState } from "react";
import { useUser } from "@/contexts/UserContext";

export interface UseDeleteConfirmationOptions {
  /** Book ID to delete. */
  bookId: number | null;
  /** Callback when delete is successful. */
  onSuccess?: () => void;
  /** Callback when delete fails. */
  onError?: (error: string) => void;
}

export interface UseDeleteConfirmationResult {
  /** Whether the confirmation modal is open. */
  isOpen: boolean;
  /** Whether the "don't show again" checkbox is checked. */
  dontShowAgain: boolean;
  /** Whether to delete files from drive. */
  deleteFilesFromDrive: boolean;
  /** Whether deletion is in progress. */
  isDeleting: boolean;
  /** Error message if deletion failed. */
  error: string | null;
  /** Opens the confirmation modal. */
  open: () => void;
  /** Closes the confirmation modal. */
  close: () => void;
  /** Toggles the "don't show again" checkbox. */
  toggleDontShowAgain: () => void;
  /** Toggles the "delete files from drive" checkbox. */
  toggleDeleteFilesFromDrive: () => void;
  /** Confirms the deletion. */
  confirm: () => Promise<void>;
}

/**
 * Custom hook for managing delete confirmation modal state and deletion.
 *
 * Handles the state and interactions for a delete confirmation modal,
 * and performs the actual deletion via API call.
 * Follows SRP by managing confirmation modal state and deletion logic.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * options : UseDeleteConfirmationOptions
 *     Configuration including book ID and callbacks.
 *
 * Returns
 * -------
 * UseDeleteConfirmationResult
 *     Object containing modal state and control functions.
 */
export function useDeleteConfirmation({
  bookId,
  onSuccess,
  onError,
}: UseDeleteConfirmationOptions): UseDeleteConfirmationResult {
  const { getSetting, updateSetting } = useUser();
  const [isOpen, setIsOpen] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const [deleteFilesFromDrive, setDeleteFilesFromDrive] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize deleteFilesFromDrive from setting when modal opens
  useEffect(() => {
    if (isOpen) {
      const defaultDeleteFiles = getSetting("default_delete_files_from_drive");
      const shouldDeleteFiles =
        defaultDeleteFiles !== null ? defaultDeleteFiles === "true" : false;
      setDeleteFilesFromDrive(shouldDeleteFiles);
    }
  }, [isOpen, getSetting]);

  const close = useCallback(() => {
    setIsOpen(false);
    setDontShowAgain(false);
    setDeleteFilesFromDrive(false);
    setError(null);
  }, []);

  /**
   * Performs the actual deletion API call.
   */
  const performDelete = useCallback(
    async (id: number, deleteFiles: boolean) => {
      setIsDeleting(true);
      setError(null);

      try {
        const response = await fetch(`/api/books/${id}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            delete_files_from_drive: deleteFiles,
          }),
        });

        if (!response.ok) {
          let errorMsg = "Failed to delete book";
          try {
            const data = (await response.json()) as { detail?: string };
            errorMsg = data.detail || errorMsg;
          } catch {
            // Non-JSON error response (e.g., plain text / HTML)
            try {
              const text = await response.text();
              if (text) {
                errorMsg = text;
              }
            } catch {
              // Ignore secondary parse failures; keep default message
            }
          }
          setError(errorMsg);
          onError?.(errorMsg);
          return;
        }

        // Success - close modal and call success callback
        setIsOpen(false);
        setDontShowAgain(false);
        setDeleteFilesFromDrive(false);
        setError(null);
        onSuccess?.();
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : "Failed to delete book";
        setError(errorMsg);
        onError?.(errorMsg);
      } finally {
        setIsDeleting(false);
      }
    },
    [onSuccess, onError],
  );

  const open = useCallback(() => {
    // Check if warning should be shown
    const alwaysWarn = getSetting("always_warn_on_delete");
    const shouldWarn = alwaysWarn === null || alwaysWarn === "true";

    if (!shouldWarn && bookId) {
      // Skip modal and delete directly using default setting
      const defaultDeleteFiles = getSetting("default_delete_files_from_drive");
      const shouldDeleteFiles =
        defaultDeleteFiles !== null ? defaultDeleteFiles === "true" : false;
      void performDelete(bookId, shouldDeleteFiles);
      return;
    }

    setIsOpen(true);
    setError(null);
  }, [getSetting, bookId, performDelete]);

  const toggleDontShowAgain = useCallback(() => {
    setDontShowAgain((prev) => !prev);
  }, []);

  const toggleDeleteFilesFromDrive = useCallback(() => {
    setDeleteFilesFromDrive((prev) => !prev);
  }, []);

  const confirm = useCallback(async () => {
    if (!bookId) {
      const errorMsg = "No book ID provided";
      setError(errorMsg);
      onError?.(errorMsg);
      return;
    }

    // If "don't show again" is checked, update the setting
    if (dontShowAgain) {
      updateSetting("always_warn_on_delete", "false");
    }

    await performDelete(bookId, deleteFilesFromDrive);
  }, [
    bookId,
    deleteFilesFromDrive,
    dontShowAgain,
    updateSetting,
    performDelete,
    onError,
  ]);

  return {
    isOpen,
    dontShowAgain,
    deleteFilesFromDrive,
    isDeleting,
    error,
    open,
    close,
    toggleDontShowAgain,
    toggleDeleteFilesFromDrive,
    confirm,
  };
}
