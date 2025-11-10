"use client";

import { useBookCoverFromUrl } from "@/hooks/useBookCoverFromUrl";
import type { Book } from "@/types/book";
import { BookCoverActions } from "./BookCoverActions";
import { BookCoverDisplay } from "./BookCoverDisplay";
import styles from "./BookEditModal.module.scss";
import { BookFormatsSection } from "./BookFormatsSection";
import { CoverUrlInput } from "./CoverUrlInput";

export interface BookEditCoverSectionProps {
  /** Current book being edited. */
  book: Book;
  /** Staged cover URL (if set from URL input). */
  stagedCoverUrl?: string | null;
  /** Callback when cover URL is set. */
  onCoverUrlSet?: (url: string) => void;
  /** Callback when URL input visibility changes. */
  onUrlInputVisibilityChange?: (isVisible: boolean) => void;
}

/**
 * Cover and formats section component for book edit modal.
 *
 * Displays book cover, cover actions, and file formats.
 * Follows SRP by delegating to specialized components.
 * Uses IOC via hooks and components.
 *
 * Parameters
 * ----------
 * props : BookEditCoverSectionProps
 *     Component props including book and callbacks.
 */
export function BookEditCoverSection({
  book,
  stagedCoverUrl,
  onCoverUrlSet,
  onUrlInputVisibilityChange,
}: BookEditCoverSectionProps) {
  const { isLoading, error, urlInput, handleUrlChange, handleSetFromUrlClick } =
    useBookCoverFromUrl({
      bookId: book.id,
      onCoverUrlSet,
      onUrlInputVisibilityChange,
    });

  // Use staged cover URL if available, otherwise use book's thumbnail_url
  const displayCoverUrl = stagedCoverUrl || book.thumbnail_url;

  return (
    <div className={styles.leftSidebar}>
      <div className={styles.coverContainer}>
        <BookCoverDisplay
          book={book}
          coverUrl={displayCoverUrl}
          isLoading={isLoading}
        />
        <BookCoverActions
          isUrlInputVisible={urlInput.isVisible}
          onSetFromUrlClick={handleSetFromUrlClick}
          urlInput={
            urlInput.isVisible ? (
              <CoverUrlInput
                value={urlInput.value}
                disabled={isLoading}
                error={error}
                inputRef={urlInput.inputRef}
                onChange={handleUrlChange}
                onKeyDown={urlInput.handleKeyDown}
              />
            ) : undefined
          }
        />
      </div>
      <BookFormatsSection book={book} />
    </div>
  );
}
