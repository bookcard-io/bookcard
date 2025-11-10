"use client";

import { Button } from "@/components/forms/Button";
import styles from "./BookEditModal.module.scss";

export interface BookCoverActionsProps {
  /** Whether URL input is visible. */
  isUrlInputVisible: boolean;
  /** Handler for "Set cover from URL" button click. */
  onSetFromUrlClick: () => void;
  /** URL input component to render when visible. */
  urlInput?: React.ReactNode;
}

/**
 * Book cover actions component.
 *
 * Displays action buttons for cover operations.
 * Follows SRP by focusing solely on cover action buttons.
 *
 * Parameters
 * ----------
 * props : BookCoverActionsProps
 *     Component props including handlers and URL input.
 */
export function BookCoverActions({
  isUrlInputVisible,
  onSetFromUrlClick,
  urlInput,
}: BookCoverActionsProps) {
  return (
    <div className={styles.coverActions}>
      <Button
        type="button"
        variant="ghost"
        size="small"
        className={styles.coverAction}
      >
        <span className="pi pi-image" aria-hidden="true" />
        Select cover
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="small"
        className={styles.coverAction}
        onClick={onSetFromUrlClick}
      >
        <span className="pi pi-link" aria-hidden="true" />
        Set cover from URL
      </Button>
      {isUrlInputVisible && urlInput}
      <Button
        type="button"
        variant="ghost"
        size="small"
        className={styles.coverAction}
      >
        <span className="pi pi-download" aria-hidden="true" />
        Download cover
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="small"
        className={styles.coverAction}
      >
        <span className="pi pi-sparkles" aria-hidden="true" />
        Generate cover
      </Button>
    </div>
  );
}
