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

"use client";

import { useCallback, useState } from "react";
import { FullscreenImageModal } from "@/components/common/FullscreenImageModal";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import type { Book } from "@/types/book";
import styles from "./BookEditModal.module.scss";

export interface BookCoverDisplayProps {
  /** Book data. */
  book: Book;
  /** Cover URL to display (staged or original). */
  coverUrl: string | null;
  /** Optional loading state (e.g., when backend is processing cover URL). */
  isLoading?: boolean;
}

/**
 * Book cover display component.
 *
 * Displays book cover image with overlay actions.
 * Follows SRP by focusing solely on cover display.
 *
 * Parameters
 * ----------
 * props : BookCoverDisplayProps
 *     Component props including book and cover URL.
 */
export function BookCoverDisplay({
  book,
  coverUrl,
  isLoading,
}: BookCoverDisplayProps) {
  const [isCoverOpen, setIsCoverOpen] = useState(false);
  const openCover = useCallback(() => setIsCoverOpen(true), []);
  const closeCover = useCallback(() => setIsCoverOpen(false), []);

  return (
    <>
      {coverUrl ? (
        <div className={styles.coverWrapper}>
          <ImageWithLoading
            src={coverUrl}
            alt={`Cover for ${book.title}`}
            width={200}
            height={300}
            className={styles.cover}
            isLoading={isLoading}
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
        src={coverUrl || ""}
        alt={`Cover for ${book.title}`}
        isOpen={isCoverOpen}
        onClose={closeCover}
      />
    </>
  );
}
