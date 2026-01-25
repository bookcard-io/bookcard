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

export interface CancelAllTasksConfirmationModalProps {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Callback to close the modal. */
  onClose: () => void;
  /** Callback when cancel is confirmed. */
  onConfirm: () => void | Promise<void>;
  /** Number of tasks that will be cancelled. */
  taskCount: number;
  /** Whether cancellation is in progress. */
  isCancelling?: boolean;
  /** Error message if cancellation failed. */
  error?: string | null;
}

/**
 * Cancel all tasks confirmation modal component.
 *
 * Displays a warning modal before cancelling all pending/running tasks.
 * Follows SRP by focusing solely on confirmation UI.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * props : CancelAllTasksConfirmationModalProps
 *     Component props including modal state and callbacks.
 */
export function CancelAllTasksConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  taskCount,
  isCancelling = false,
  error = null,
}: CancelAllTasksConfirmationModalProps) {
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      ariaLabel="Confirm cancel all tasks"
      title="Cancel All Tasks"
      message={`Are you sure you want to cancel all ${taskCount} ${
        taskCount === 1 ? "task" : "tasks"
      }? This action cannot be undone.`}
      confirmLabel="Cancel all"
      confirmLoadingLabel="Cancelling..."
      confirmVariant="danger"
      confirmLoading={isCancelling}
      error={error}
    />
  );
}
