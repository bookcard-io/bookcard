"use client";

import { Button } from "@/components/forms/Button";
import type { Book } from "@/types/book";
import styles from "./BookEditModal.module.scss";

export interface BookEditModalHeaderProps {
  /** Current book being edited. */
  book: Book;
  /** Current form title value. */
  formTitle?: string | null;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Callback to open metadata fetch modal. */
  onFetchMetadata: () => void;
}

/**
 * Header component for book edit modal.
 *
 * Displays the title and fetch metadata button.
 * Follows SRP by focusing solely on header presentation.
 */
export function BookEditModalHeader({
  book,
  formTitle,
  isUpdating,
  onFetchMetadata,
}: BookEditModalHeaderProps) {
  return (
    <div className={styles.header}>
      <h2 className={styles.title}>
        Editing {formTitle || book.title || "Untitled"}
      </h2>
      <Button
        type="button"
        variant="success"
        size="medium"
        onClick={onFetchMetadata}
        disabled={isUpdating}
      >
        Fetch metadata
      </Button>
    </div>
  );
}
