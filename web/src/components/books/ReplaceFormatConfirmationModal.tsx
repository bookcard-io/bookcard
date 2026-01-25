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

import { ConfirmationModal } from "@/components/common/ConfirmationModal";

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
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      ariaLabel="Confirm replace format"
      title="Replace Format?"
      message={`The ${format} format already exists for this book. Do you want to replace it?`}
      confirmLabel="Replace"
      confirmLoadingLabel="Replacing..."
      confirmVariant="primary"
      confirmLoading={isReplacing}
    />
  );
}
