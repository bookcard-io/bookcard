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
          className="bg-[var(--color-danger-a-1)] hover:bg-[var(--color-danger-a0)]"
        >
          Delete
        </Button>
      </div>
    </div>
  );
}
