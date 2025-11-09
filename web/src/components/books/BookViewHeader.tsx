import Image from "next/image";
import type { Book } from "@/types/book";
import styles from "./BookViewHeader.module.scss";

export interface BookViewHeaderProps {
  /** Book data to display. */
  book: Book;
  /** Whether to show description. */
  showDescription?: boolean;
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
}: BookViewHeaderProps) {
  return (
    <div className={styles.header}>
      {book.thumbnail_url && (
        <div className={styles.coverContainer}>
          <Image
            src={book.thumbnail_url}
            alt={`Cover for ${book.title}`}
            width={200}
            height={300}
            className={styles.cover}
            unoptimized
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
