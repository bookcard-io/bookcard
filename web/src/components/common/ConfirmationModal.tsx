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

import type { ReactNode } from "react";
import { Button } from "@/components/forms/Button";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { renderModalPortal } from "@/utils/modal";

type ConfirmVariant = "primary" | "danger";
type CancelVariant = "secondary" | "ghost";

export interface ConfirmationModalProps {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Callback to close the modal. */
  onClose: () => void;
  /** Callback when confirmation is accepted. */
  onConfirm: () => void | Promise<void>;

  /** Accessible label for the dialog. */
  ariaLabel: string;
  /** Title text shown in the modal header area. */
  title: string;
  /** Main descriptive message shown under the title. */
  message: string;

  /** Optional additional body content (e.g., checkbox options). */
  children?: ReactNode;
  /** Optional leading footer content (e.g., "don't show again" checkbox). */
  footerLeading?: ReactNode;

  /** Confirm button label. */
  confirmLabel: string;
  /** Confirm button label while loading (optional). */
  confirmLoadingLabel?: string;
  /** Confirm button variant (default: danger). */
  confirmVariant?: ConfirmVariant;
  /** Whether confirm action is disabled. */
  confirmDisabled?: boolean;
  /** Whether confirm action is loading. */
  confirmLoading?: boolean;

  /** Cancel button label (default: Cancel). */
  cancelLabel?: string;
  /** Cancel button variant (default: secondary). */
  cancelVariant?: CancelVariant;
  /** Whether cancel action is disabled. */
  cancelDisabled?: boolean;

  /** Error message to display at the bottom (optional). */
  error?: string | null;
}

/**
 * Shared confirmation modal component.
 *
 * This component centralizes the common confirmation-modal UI and interaction
 * patterns (overlay click, Escape-to-close, portal rendering). Domain-specific
 * confirmation modals should wrap this component and supply text/controls.
 *
 * Parameters
 * ----------
 * props : ConfirmationModalProps
 *     Modal content and callback props.
 */
export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  ariaLabel,
  title,
  message,
  children,
  footerLeading,
  confirmLabel,
  confirmLoadingLabel,
  confirmVariant = "danger",
  confirmDisabled = false,
  confirmLoading = false,
  cancelLabel = "Cancel",
  cancelVariant = "secondary",
  cancelDisabled = false,
  error = null,
}: ConfirmationModalProps) {
  useModal(isOpen);
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  if (!isOpen) {
    return null;
  }
  if (typeof document === "undefined") {
    return null;
  }

  const footerLayoutClassName = footerLeading
    ? "flex items-center justify-between gap-3 pt-2"
    : "flex items-center justify-end gap-3 pt-2";

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-large w-full max-w-md flex-col"
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel}
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
              {title}
            </h2>
            <p className="m-0 text-[var(--color-text-a20)] text-base leading-relaxed">
              {message}
            </p>
          </div>

          {children}

          <div className={footerLayoutClassName}>
            {footerLeading}
            <div className="flex gap-3">
              <Button
                type="button"
                variant={cancelVariant}
                size="medium"
                onClick={onClose}
                disabled={cancelDisabled || confirmLoading}
              >
                {cancelLabel}
              </Button>
              <Button
                type="button"
                variant={confirmVariant}
                size="medium"
                onClick={onConfirm}
                disabled={confirmDisabled || confirmLoading}
                loading={confirmLoading}
              >
                {confirmLoading && confirmLoadingLabel
                  ? confirmLoadingLabel
                  : confirmLabel}
              </Button>
            </div>
          </div>

          {error && (
            <p className="m-0 text-[var(--color-danger-a0)] text-sm">{error}</p>
          )}
        </div>
      </div>
    </div>
  );

  return renderModalPortal(modalContent);
}
