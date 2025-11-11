"use client";

import { useCallback } from "react";
import { createPortal } from "react-dom";
import { Button } from "@/components/forms/Button";
import { useModal } from "@/hooks/useModal";

export interface DeleteBookConfirmationModalProps {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Whether the "don't show again" checkbox is checked. */
  dontShowAgain: boolean;
  /** Whether to delete files from drive. */
  deleteFilesFromDrive: boolean;
  /** Callback to close the modal. */
  onClose: () => void;
  /** Callback to toggle the "don't show again" checkbox. */
  onToggleDontShowAgain: () => void;
  /** Callback to toggle the "delete files from drive" checkbox. */
  onToggleDeleteFilesFromDrive: () => void;
  /** Callback when delete is confirmed. */
  onConfirm: () => void;
  /** Book title for display in warning message. */
  bookTitle?: string;
}

/**
 * Delete book confirmation modal component.
 *
 * Displays a warning modal before deleting a book.
 * Follows SRP by focusing solely on confirmation UI.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * props : DeleteBookConfirmationModalProps
 *     Component props including modal state and callbacks.
 */
export function DeleteBookConfirmationModal({
  isOpen,
  dontShowAgain,
  deleteFilesFromDrive,
  onClose,
  onToggleDontShowAgain,
  onToggleDeleteFilesFromDrive,
  onConfirm,
  bookTitle,
}: DeleteBookConfirmationModalProps) {
  // Prevent body scroll when modal is open
  useModal(isOpen);

  /**
   * Handles overlay click to close modal.
   */
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  /**
   * Prevents modal content clicks from closing the modal.
   */
  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  /**
   * Handles Escape key to close modal.
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  if (!isOpen) {
    return null;
  }

  const displayTitle = bookTitle || "this book";

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="fixed inset-0 z-[1002] flex items-center justify-center bg-black/70 p-4"
      style={{ animation: "fadeIn 0.2s ease-out" }}
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="presentation"
    >
      <div
        className="relative flex w-full max-w-md flex-col rounded-2xl bg-[var(--color-surface-a10)] shadow-[0_20px_60px_rgba(0,0,0,0.5)]"
        style={{ animation: "slideUp 0.3s ease-out" }}
        role="dialog"
        aria-modal="true"
        aria-label="Confirm book deletion"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 z-10 flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border-none bg-transparent p-2 text-3xl text-[var(--color-text-a30)] leading-none transition-all duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a0)] focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
          aria-label="Close"
        >
          ×
        </button>

        <div className="flex flex-col gap-6 p-6">
          <div className="flex flex-col gap-2 pr-8">
            <h2 className="m-0 font-bold text-2xl text-[var(--color-text-a0)]">
              Delete Book
            </h2>
            <p className="m-0 text-[var(--color-text-a20)] text-base leading-relaxed">
              Are you sure you want to delete <strong>{displayTitle}</strong>?
              This action cannot be undone.
            </p>
          </div>

          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={deleteFilesFromDrive}
              onChange={onToggleDeleteFilesFromDrive}
              className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
            />
            <span className="text-[var(--color-text-a0)] text-base">
              Also delete files from the filesystem.
            </span>
          </label>

          <div className="flex items-center justify-between gap-3 pt-2">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={dontShowAgain}
                onChange={onToggleDontShowAgain}
                className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <span className="text-[var(--color-text-a50)] text-sm">
                Don't show this message again.
              </span>
            </label>
            <div className="flex gap-3">
              <Button
                type="button"
                variant="secondary"
                size="medium"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="danger"
                size="medium"
                onClick={onConfirm}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render modal in a portal to avoid DOM hierarchy conflicts
  return createPortal(modalContent, document.body);
}
