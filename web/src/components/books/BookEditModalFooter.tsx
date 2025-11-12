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
import styles from "./BookEditModal.module.scss";

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
    <div className={styles.footer}>
      <div className={styles.statusMessages}>
        {updateError && (
          <div className={styles.errorBanner} role="alert">
            {updateError}
          </div>
        )}

        {showSuccess && (
          <div className={styles.successBanner}>
            Book metadata updated successfully!
          </div>
        )}
      </div>
      <div className={styles.footerActions}>
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
