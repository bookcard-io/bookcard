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
import { useUser } from "@/contexts/UserContext";
import type { Book } from "@/types/book";
import { buildBookPermissionContext } from "@/utils/permissions";

export interface BookViewModalFooterProps {
  /** Callback when delete button is clicked. */
  onDelete?: () => void;
  /** Book data for permission checking. */
  book?: Book | null;
}

/**
 * Footer component for book view modal.
 *
 * Displays action buttons.
 * Follows SRP by focusing solely on footer presentation.
 */
export function BookViewModalFooter({
  onDelete,
  book,
}: BookViewModalFooterProps) {
  const { canPerformAction } = useUser();

  const handleDelete = () => {
    if (onDelete) {
      onDelete();
    }
  };

  // Check permission
  const canDelete =
    book &&
    canPerformAction("books", "delete", buildBookPermissionContext(book));

  return (
    <div className="modal-footer-between">
      <div className="flex-1" />
      <div className="flex flex-shrink-0 justify-end gap-3">
        <Button
          type="button"
          variant="danger"
          size="medium"
          onClick={handleDelete}
          disabled={!canDelete}
          className="bg-[var(--color-danger-a-1)] text-[var(--color-white)] hover:bg-[var(--color-danger-a0)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          Delete
        </Button>
      </div>
    </div>
  );
}
