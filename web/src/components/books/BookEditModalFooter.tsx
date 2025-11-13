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

export interface BookEditModalFooterProps {
  /** Error message from update attempt. */
  updateError: string | null;
  /** Whether to show success message. */
  showSuccess: boolean;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Callback when cancel is clicked. */
  onCancel: () => void;
}

/**
 * Footer component for book edit modal.
 *
 * Displays status messages and action buttons.
 * Follows SRP by focusing solely on footer presentation.
 */
export function BookEditModalFooter({
  updateError,
  showSuccess,
  isUpdating,
  hasChanges,
  onCancel,
}: BookEditModalFooterProps) {
  return (
    <div className="flex flex-col gap-4 p-4 bg-surface-tonal-a10 border-t border-surface-a20 md:flex-row md:items-center md:justify-between md:gap-4 md:pt-4 md:pb-6 md:px-6">
      <div className="flex flex-1 flex-col gap-2 w-full">
        {updateError && (
          <div
            className="rounded-md bg-danger-a20 px-4 py-3 text-sm text-danger-a0"
            role="alert"
          >
            {updateError}
          </div>
        )}

        {showSuccess && (
          <div className="rounded-md bg-success-a20 px-4 py-3 text-sm text-success-a0 animate-[slideIn_0.3s_ease-out]">
            Book metadata updated successfully!
          </div>
        )}
      </div>
      <div className="flex flex-shrink-0 justify-end gap-3 w-full md:w-auto md:flex-row flex-col-reverse">
        <Button
          type="button"
          variant="ghost"
          size="medium"
          onClick={onCancel}
          disabled={isUpdating}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          size="medium"
          loading={isUpdating}
          disabled={!hasChanges}
        >
          Save info
        </Button>
      </div>
    </div>
  );
}
