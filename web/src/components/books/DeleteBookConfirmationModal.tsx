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
import { useUser } from "@/contexts/UserContext";
import type { Book } from "@/types/book";
import { buildBookPermissionContext } from "@/utils/permissions";

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
  onConfirm: () => void | Promise<void>;
  /** Whether deletion is in progress. */
  isDeleting?: boolean;
  /** Error message if deletion failed. */
  error?: string | null;
  /** Book title for display in warning message. */
  bookTitle?: string;
  /** Book data for permission checking. */
  book?: Book | null;
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
  book,
  isDeleting = false,
  error = null,
}: DeleteBookConfirmationModalProps) {
  const { canPerformAction } = useUser();
  const bookContext = book ? buildBookPermissionContext(book) : undefined;
  const canDelete = book && canPerformAction("books", "delete", bookContext);

  const displayTitle = bookTitle || "this book";
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      ariaLabel="Confirm book deletion"
      title="Delete Book"
      message={`Are you sure you want to delete ${displayTitle}? This action cannot be undone.`}
      confirmLabel="Delete"
      confirmLoadingLabel="Deleting..."
      confirmVariant="danger"
      confirmDisabled={!canDelete || isDeleting}
      confirmLoading={isDeleting}
      error={error}
      footerLeading={
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
      }
    >
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
    </ConfirmationModal>
  );
}
