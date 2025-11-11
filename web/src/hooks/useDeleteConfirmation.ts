import { useCallback, useState } from "react";

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
  const [isOpen, setIsOpen] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const [deleteFilesFromDrive, setDeleteFilesFromDrive] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const open = useCallback(() => {
    setIsOpen(true);
    setError(null);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setDontShowAgain(false);
    setDeleteFilesFromDrive(false);
    setError(null);
  }, []);

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

    setIsDeleting(true);
    setError(null);

    try {
      const response = await fetch(`/api/books/${bookId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          delete_files_from_drive: deleteFilesFromDrive,
        }),
      });

      if (!response.ok) {
        const data = (await response.json()) as { detail?: string };
        const errorMsg = data.detail || "Failed to delete book";
        setError(errorMsg);
        onError?.(errorMsg);
        return;
      }

      // Success - close modal and call success callback
      close();
      onSuccess?.();
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to delete book";
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setIsDeleting(false);
    }
  }, [bookId, deleteFilesFromDrive, onSuccess, onError, close]);

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
