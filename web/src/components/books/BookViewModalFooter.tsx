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
export function BookViewModalFooter({
  onDelete,
}: BookViewModalFooterProps) {
  const handleDelete = () => {
    // TODO: Implement delete functionality
    if (onDelete) {
      onDelete();
    }
  };

  return (
    <div className="flex justify-between items-center gap-4 px-6 pb-6 pt-4 border-t border-surface-a20 bg-surface-tonal-a10">
      <div className="flex-1" />
      <div className="flex justify-end gap-3 flex-shrink-0">
        <Button
          type="button"
          variant="danger"
          size="medium"
          onClick={handleDelete}
          className="bg-[var(--color-danger-a-1)] hover:bg-[var(--color-danger-a0)]"
        >
          Delete
        </Button>
      </div>
    </div>
  );
}
