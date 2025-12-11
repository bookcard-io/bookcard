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

export interface ReplaceFormatConfirmationModalProps {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Callback to close the modal. */
  onClose: () => void;
  /** Callback when replace is confirmed. */
  onConfirm: () => void;
  /** Format name being replaced. */
  format: string;
  /** Whether replacement is in progress. */
  isReplacing: boolean;
}

/**
 * Replace format confirmation modal component.
 *
 * Displays a warning modal before replacing an existing book format.
 * Follows SRP by focusing solely on confirmation UI.
 *
 * Parameters
 * ----------
 * props : ReplaceFormatConfirmationModalProps
 *     Component props including modal state and callbacks.
 */
export function ReplaceFormatConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  format,
  isReplacing,
}: ReplaceFormatConfirmationModalProps) {
  useModal(isOpen);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

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
        aria-label="Confirm replace format"
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
              Replace Format?
            </h2>
            <p className="m-0 text-[var(--color-text-a20)] text-base leading-relaxed">
              The <strong>{format}</strong> format already exists for this book.
              Do you want to replace it?
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              size="medium"
              onClick={onClose}
              disabled={isReplacing}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              size="medium"
              onClick={onConfirm}
              disabled={isReplacing}
            >
              {isReplacing ? "Replacing..." : "Replace"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  if (typeof document === "undefined") return null;
  return createPortal(modalContent, document.body);
}
