"use client";

import Image from "next/image";
import { useCallback, useState } from "react";
import { FullscreenImageModal } from "@/components/common/FullscreenImageModal";
import { Button } from "@/components/forms/Button";
import type { Book } from "@/types/book";
import { formatFileSize } from "@/utils/format";
import styles from "./BookEditModal.module.scss";

export interface BookEditCoverSectionProps {
  /** Current book being edited. */
  book: Book;
}

/**
 * Cover and formats section component for book edit modal.
 *
 * Displays book cover, cover actions, and file formats.
 * Follows SRP by focusing solely on cover and formats presentation.
 */
export function BookEditCoverSection({ book }: BookEditCoverSectionProps) {
  const [isCoverOpen, setIsCoverOpen] = useState(false);
  const openCover = useCallback(() => setIsCoverOpen(true), []);
  const closeCover = useCallback(() => setIsCoverOpen(false), []);

  return (
    <div className={styles.leftSidebar}>
      <div className={styles.coverContainer}>
        {book.thumbnail_url ? (
          <div className={styles.coverWrapper}>
            <Image
              src={book.thumbnail_url}
              alt={`Cover for ${book.title}`}
              width={200}
              height={300}
              className={styles.cover}
              unoptimized
            />
            <div className={styles.coverOverlay}>
              <button
                type="button"
                className={styles.coverActionButton}
                aria-label="View cover"
                title="View cover"
                onClick={openCover}
              >
                <span
                  className="pi pi-arrow-up-right-and-arrow-down-left-from-center"
                  aria-hidden="true"
                />
              </button>
              <button
                type="button"
                className={styles.coverActionButton}
                aria-label="Delete cover"
                title="Delete cover"
              >
                <span className="pi pi-trash" aria-hidden="true" />
              </button>
            </div>
          </div>
        ) : (
          <div className={styles.coverPlaceholder}>
            <span>No Cover</span>
          </div>
        )}
        <FullscreenImageModal
          src={book.thumbnail_url || ""}
          alt={`Cover for ${book.title}`}
          isOpen={isCoverOpen}
          onClose={closeCover}
        />
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
      </div>

      {/* Formats Section */}
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
    </div>
  );
}
