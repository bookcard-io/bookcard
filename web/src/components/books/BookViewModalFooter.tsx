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

export interface BookViewModalFooterProps {
  /** Callback when delete button is clicked. */
  onDelete?: () => void;
}

/**
 * Footer component for book view modal.
 *
 * Displays action buttons.
 * Follows SRP by focusing solely on footer presentation.
 */
export function BookViewModalFooter({ onDelete }: BookViewModalFooterProps) {
  const handleDelete = () => {
    if (onDelete) {
      onDelete();
    }
  };

  return (
    <div className="flex items-center justify-between gap-4 border-surface-a20 border-t bg-surface-tonal-a10 px-6 pt-4 pb-6">
      <div className="flex-1" />
      <div className="flex flex-shrink-0 justify-end gap-3">
        <Button
          type="button"
          variant="danger"
          size="medium"
          onClick={handleDelete}
          className="bg-[var(--color-danger-a-1)] text-[var(--color-white)] hover:bg-[var(--color-danger-a0)]"
        >
          Delete
        </Button>
      </div>
    </div>
  );
}
