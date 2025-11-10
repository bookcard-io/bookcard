"use client";

import { useCallback, useState } from "react";
import { FullscreenImageModal } from "@/components/common/FullscreenImageModal";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { RatingDisplay } from "@/components/forms/RatingDisplay";
import type { Book } from "@/types/book";
import styles from "./BookViewHeader.module.scss";

export interface BookViewHeaderProps {
  /** Book data to display. */
  book: Book;
  /** Whether to show description. */
  showDescription?: boolean;
  /** Callback when edit icon is clicked. */
  onEdit?: () => void;
}

/**
 * Book view header component.
 *
 * Displays book cover, title, authors, series, and optionally description.
 * Follows SRP by focusing solely on header presentation.
 */
export function BookViewHeader({
  book,
  showDescription = false,
  onEdit,
}: BookViewHeaderProps) {
  const [isCoverOpen, setIsCoverOpen] = useState(false);
  const openCover = useCallback(() => setIsCoverOpen(true), []);
  const closeCover = useCallback(() => setIsCoverOpen(false), []);

  return (
    <div className={styles.header}>
      {book.thumbnail_url && (
        <div className={styles.coverContainer}>
          <div className={styles.coverClickable}>
            <ImageWithLoading
              src={book.thumbnail_url}
              alt={`Cover for ${book.title}`}
              width={200}
              height={300}
              className={styles.cover}
              containerClassName={styles.coverWrapper}
              unoptimized
            />
            <button
              type="button"
              className={styles.coverCurtain}
              aria-label="View cover full screen"
              title="View cover"
              onClick={openCover}
            >
              <i
                className="pi pi-arrow-up-right-and-arrow-down-left-from-center"
                aria-hidden="true"
              />
            </button>
          </div>
          <div className={styles.iconActions}>
            <button
              type="button"
              className={styles.iconButton}
              aria-label="Read book"
              title="Read book"
            >
              <i className="pi pi-book" aria-hidden="true" />
            </button>
            <button
              type="button"
              className={styles.iconButton}
              aria-label="Send book"
              title="Send book"
            >
              <i className="pi pi-send" aria-hidden="true" />
            </button>
            <button
              type="button"
              className={styles.iconButton}
              aria-label="Convert format"
              title="Convert format"
            >
              <i className="pi pi-arrow-right-arrow-left" aria-hidden="true" />
            </button>
            {onEdit && (
              <button
                type="button"
                onClick={onEdit}
                className={styles.iconButton}
                aria-label="Edit metadata"
                title="Edit metadata"
              >
                <i className="pi pi-pencil" aria-hidden="true" />
              </button>
            )}
          </div>
          <FullscreenImageModal
            src={book.thumbnail_url}
            alt={`Cover for ${book.title}`}
            isOpen={isCoverOpen}
            onClose={closeCover}
          />
        </div>
      )}
      <div className={styles.headerInfo}>
        <h1 className={styles.title}>{book.title}</h1>
        {book.authors && book.authors.length > 0 && (
          <div className={styles.authors}>
            <span className={styles.label}>By</span>
            <span className={styles.value}>{book.authors.join(", ")}</span>
          </div>
        )}
        {book.series && (
          <div className={styles.series}>
            <span className={styles.label}>Series:</span>
            <span className={styles.value}>
              {book.series}
              {book.series_index !== null &&
                book.series_index !== undefined && (
                  <span className={styles.seriesIndex}>
                    {" "}
                    #{book.series_index}
                  </span>
                )}
            </span>
          </div>
        )}
        {book.rating !== null && book.rating !== undefined && (
          <div className={styles.ratingSection}>
            <RatingDisplay value={book.rating} showText size="medium" />
          </div>
        )}
        {showDescription && book.description && (
          <div className={styles.descriptionSection}>
            <h2 className={styles.descriptionTitle}>Description</h2>
            <div
              className={styles.description}
              // biome-ignore lint/security/noDangerouslySetInnerHtml: Book descriptions from Calibre are trusted HTML content
              dangerouslySetInnerHTML={{ __html: book.description }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
