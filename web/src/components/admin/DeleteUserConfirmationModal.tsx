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
  const displayUsername = username || "this user";

  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      ariaLabel="Confirm user deletion"
      title="Delete User"
      message={`Are you sure you want to delete user ${displayUsername}? This action cannot be undone.`}
      confirmLabel="Delete"
      confirmLoadingLabel="Deleting..."
      confirmVariant="danger"
      confirmLoading={isDeleting}
      error={error}
    />
  );
}
