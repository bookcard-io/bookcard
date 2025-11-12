// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import type { Book } from "@/types/book";
import { formatDate, formatYear } from "@/utils/format";
import styles from "./BookViewMetadata.module.scss";

export interface BookViewMetadataProps {
  /** Book data to display. */
  book: Book;
}

/**
 * Book view metadata component.
 *
 * Displays publication, classification, and identifier information.
 * Follows SRP by focusing solely on metadata presentation.
 */
export function BookViewMetadata({ book }: BookViewMetadataProps) {
  return (
    <div className={styles.metadataGrid}>
      {/* Publication Info */}
      <section className={styles.metadataSection}>
        <h3 className={styles.metadataTitle}>Publication</h3>
        <div className={styles.metadataItem}>
          <span className={styles.metadataLabel}>Published:</span>
          <span className={styles.metadataValue}>
            {formatDate(book.pubdate)}
          </span>
        </div>
        {book.pubdate && (
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Year:</span>
            <span className={styles.metadataValue}>
              {formatYear(book.pubdate)}
            </span>
          </div>
        )}
        {book.publisher && (
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Publisher:</span>
            <span className={styles.metadataValue}>{book.publisher}</span>
          </div>
        )}
        {book.languages && book.languages.length > 0 && (
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Languages:</span>
            <span className={styles.metadataValue}>
              {book.languages.map((lang) => lang.toUpperCase()).join(", ")}
            </span>
          </div>
        )}
      </section>

      {/* Classification */}
      <section className={styles.metadataSection}>
        <h3 className={styles.metadataTitle}>Classification</h3>
        {book.tags && book.tags.length > 0 && (
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Tags:</span>
            <div className={styles.tags}>
              {book.tags.map((tag) => (
                <span key={tag} className={styles.tag}>
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Identifiers */}
      {book.identifiers && book.identifiers.length > 0 && (
        <section className={styles.metadataSection}>
          <h3 className={styles.metadataTitle}>Identifiers</h3>
          {book.identifiers.map((ident) => (
            <div
              key={`${ident.type}-${ident.val}`}
              className={styles.metadataItem}
            >
              <span className={styles.metadataLabel}>
                {ident.type.toUpperCase()}:
              </span>
              <span className={styles.metadataValue}>{ident.val}</span>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
