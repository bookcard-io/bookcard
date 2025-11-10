"use client";

import { Button } from "@/components/forms/Button";
import type { Book } from "@/types/book";
import { formatFileSize } from "@/utils/format";
import styles from "./BookEditModal.module.scss";

export interface BookFormatsSectionProps {
  /** Book data containing formats. */
  book: Book;
}

/**
 * Book formats section component.
 *
 * Displays book file formats and format actions.
 * Follows SRP by focusing solely on formats presentation.
 *
 * Parameters
 * ----------
 * props : BookFormatsSectionProps
 *     Component props including book data.
 */
export function BookFormatsSection({ book }: BookFormatsSectionProps) {
  return (
    <div className={styles.formatsSection}>
      <h3 className={styles.formatsTitle}>Formats</h3>
      {book.formats && book.formats.length > 0 ? (
        <div className={styles.formatsList}>
          {book.formats.map((file) => (
            <div
              key={`${file.format}-${file.size}`}
              className={styles.formatItem}
            >
              <div className={styles.formatIcon}>
                {file.format.toUpperCase()}
              </div>
              <div className={styles.formatInfo}>
                <span className={styles.formatName}>
                  {file.format.toUpperCase()}
                </span>
                <span className={styles.formatSize}>
                  {formatFileSize(file.size)}
                </span>
              </div>
              <div className={styles.formatActions}>
                <button
                  type="button"
                  className={styles.formatActionButton}
                  aria-label={`Info for ${file.format.toUpperCase()}`}
                  title={`Info for ${file.format.toUpperCase()}`}
                >
                  <span className="pi pi-info-circle" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className={styles.formatActionButton}
                  aria-label={`Copy ${file.format.toUpperCase()}`}
                  title={`Copy ${file.format.toUpperCase()}`}
                >
                  <span className="pi pi-copy" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className={styles.formatActionButton}
                  aria-label={`Delete ${file.format.toUpperCase()}`}
                  title={`Delete ${file.format.toUpperCase()}`}
                >
                  <span className="pi pi-trash" aria-hidden="true" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className={styles.noFormats}>No formats available</div>
      )}
      <div className={styles.formatButtons}>
        <Button
          type="button"
          variant="ghost"
          size="small"
          className={styles.formatAction}
        >
          <span className="pi pi-plus" aria-hidden="true" />
          Add new format
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="small"
          className={styles.formatAction}
        >
          <span className="pi pi-arrow-right-arrow-left" aria-hidden="true" />
          Convert
        </Button>
      </div>
    </div>
  );
}
