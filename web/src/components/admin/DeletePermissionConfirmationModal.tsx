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

import { Button } from "@/components/forms/Button";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { cn } from "@/libs/utils";
import { renderModalPortal } from "@/utils/modal";

export interface DeletePermissionConfirmationModalProps {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Permission name to display. */
  permissionName: string;
  /** Whether deletion is in progress. */
  isDeleting: boolean;
  /** Error message to display. */
  error: string | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when deletion is confirmed. */
  onConfirm: () => void;
}

/**
 * Delete permission confirmation modal component.
 *
 * Displays a confirmation dialog before deleting a permission.
 * Follows SRP by focusing solely on delete confirmation UI.
 * Follows IOC by accepting callbacks for all operations.
 */
export function DeletePermissionConfirmationModal({
  isOpen,
  permissionName,
  isDeleting,
  error,
  onClose,
  onConfirm,
}: DeletePermissionConfirmationModalProps) {
  // Use standardized modal interaction handlers (DRY, SRP)
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  if (!isOpen) {
    return null;
  }

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-default w-full max-w-md flex-col",
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Delete permission confirmation"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="modal-close-button modal-close-button-sm focus:outline"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>

        <div className="flex items-start justify-between gap-4 border-surface-a20 border-b pt-6 pr-16 pb-4 pl-6">
          <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
            Delete Permission
          </h2>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-6">
          <p className="m-0 text-sm text-text-a0">
            Are you sure you want to delete the permission{" "}
            <strong>{permissionName}</strong>? This action cannot be undone.
          </p>
          {error && (
            <p className="m-0 text-[var(--color-danger-a0)] text-sm">{error}</p>
          )}
        </div>

        <div className={cn("modal-footer-end flex-shrink-0")}>
          <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
            <Button
              type="button"
              variant="ghost"
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
              loading={isDeleting}
            >
              Delete Permission
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render modal in a portal to avoid DOM hierarchy conflicts (DRY via utility)
  return renderModalPortal(modalContent);
}
