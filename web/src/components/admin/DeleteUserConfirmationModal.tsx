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

"use client";

import { useCallback } from "react";
import { createPortal } from "react-dom";
import { Button } from "@/components/forms/Button";
import { useModal } from "@/hooks/useModal";

export interface DeleteUserConfirmationModalProps {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Callback to close the modal. */
  onClose: () => void;
  /** Callback when delete is confirmed. */
  onConfirm: () => void | Promise<void>;
  /** Whether deletion is in progress. */
  isDeleting?: boolean;
  /** Error message if deletion failed. */
  error?: string | null;
  /** Username for display in warning message. */
  username?: string;
}

/**
 * Delete user confirmation modal component.
 *
 * Displays a warning modal before deleting a user.
 * Follows SRP by focusing solely on confirmation UI.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * props : DeleteUserConfirmationModalProps
 *     Component props including modal state and callbacks.
 */
export function DeleteUserConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  username,
  isDeleting = false,
  error = null,
}: DeleteUserConfirmationModalProps) {
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

  const displayUsername = username || "this user";

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-large w-full max-w-md flex-col"
        role="dialog"
        aria-modal="true"
        aria-label="Confirm user deletion"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="modal-close-button modal-close-button-sm cursor-pointer transition-all hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a0)]"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>

        <div className="flex flex-col gap-6 p-6">
          <div className="flex flex-col gap-2 pr-8">
            <h2 className="m-0 font-bold text-2xl text-[var(--color-text-a0)]">
              Delete User
            </h2>
            <p className="m-0 text-[var(--color-text-a20)] text-base leading-relaxed">
              Are you sure you want to delete user{" "}
              <strong>{displayUsername}</strong>? This action cannot be undone.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              size="medium"
              onClick={onClose}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              size="medium"
              onClick={onConfirm}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </div>
          {error && (
            <p className="m-0 text-[var(--color-danger-a0)] text-sm">{error}</p>
          )}
        </div>
      </div>
    </div>
  );

  // Render modal in a portal to avoid DOM hierarchy conflicts
  return createPortal(modalContent, document.body);
}
