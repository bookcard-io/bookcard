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
