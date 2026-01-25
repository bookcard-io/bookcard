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
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      ariaLabel="Delete permission confirmation"
      title="Delete Permission"
      message={`Are you sure you want to delete the permission ${permissionName}? This action cannot be undone.`}
      confirmLabel="Delete permission"
      confirmVariant="danger"
      confirmLoading={isDeleting}
      cancelVariant="ghost"
      error={error}
    />
  );
}
