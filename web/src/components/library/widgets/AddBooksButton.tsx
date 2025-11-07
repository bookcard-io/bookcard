"use client";

import { Plus } from "@/icons/Plus";
import styles from "./AddBooksButton.module.scss";

export interface AddBooksButtonProps {
  /**
   * Callback fired when the button is clicked.
   */
  onClick?: () => void;
}

/**
 * Button component for adding books to the library.
 *
 * Displays a prominent button with a plus icon for adding new books.
 */
export function AddBooksButton({ onClick }: AddBooksButtonProps) {
  const handleClick = () => {
    onClick?.();
  };

  return (
    <button
      type="button"
      className={styles.addBooksButton}
      onClick={handleClick}
      aria-label="Add books"
    >
      <Plus className={styles.plusIcon} aria-hidden="true" />
      <span className={styles.buttonText}>Add Books</span>
    </button>
  );
}
