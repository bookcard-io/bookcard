import { useCallback, useState } from "react";

export interface UseDeleteConfirmationOptions {
  /** Callback when delete is confirmed. */
  onConfirm?: () => void;
}

export interface UseDeleteConfirmationResult {
  /** Whether the confirmation modal is open. */
  isOpen: boolean;
  /** Whether the "don't show again" checkbox is checked. */
  dontShowAgain: boolean;
  /** Opens the confirmation modal. */
  open: () => void;
  /** Closes the confirmation modal. */
  close: () => void;
  /** Toggles the "don't show again" checkbox. */
  toggleDontShowAgain: () => void;
  /** Confirms the deletion. */
  confirm: () => void;
}

/**
 * Custom hook for managing delete confirmation modal state.
 *
 * Handles the state and interactions for a delete confirmation modal.
 * Follows SRP by managing only confirmation modal state.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * options : UseDeleteConfirmationOptions
 *     Configuration including confirmation callback.
 *
 * Returns
 * -------
 * UseDeleteConfirmationResult
 *     Object containing modal state and control functions.
 */
export function useDeleteConfirmation({
  onConfirm,
}: UseDeleteConfirmationOptions = {}): UseDeleteConfirmationResult {
  const [isOpen, setIsOpen] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);

  const open = useCallback(() => {
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setDontShowAgain(false);
  }, []);

  const toggleDontShowAgain = useCallback(() => {
    setDontShowAgain((prev) => !prev);
  }, []);

  const confirm = useCallback(() => {
    if (onConfirm) {
      onConfirm();
    }
    close();
  }, [onConfirm, close]);

  return {
    isOpen,
    dontShowAgain,
    open,
    close,
    toggleDontShowAgain,
    confirm,
  };
}
