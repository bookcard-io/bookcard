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

import { useEffect, useState } from "react";
import { useBookCoverFromUrl } from "@/hooks/useBookCoverFromUrl";
import { uploadBookCover } from "@/services/bookService";
import type { Book } from "@/types/book";
import { getCoverUrlWithCacheBuster } from "@/utils/books";
import { BookCoverActions } from "./BookCoverActions";
import { BookCoverDisplay } from "./BookCoverDisplay";
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
  /** Callback when cover is saved (for notifying parent). */
  onCoverSaved?: () => void;
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
  onCoverSaved,
}: BookEditCoverSectionProps) {
  // Local state to track cover URL with cache-busting
  const [coverUrl, setCoverUrl] = useState<string | null>(book.thumbnail_url);
  const [isUploading, setIsUploading] = useState(false);

  // Update cover URL when book changes
  useEffect(() => {
    setCoverUrl(book.thumbnail_url);
  }, [book.thumbnail_url]);

  const {
    isLoading: isUrlLoading,
    error,
    urlInput,
    handleUrlChange,
    handleSetFromUrlClick,
  } = useBookCoverFromUrl({
    bookId: book.id,
    onCoverUrlSet,
    onUrlInputVisibilityChange,
    onCoverSaved: () => {
      // Update cover URL with cache-busting parameter to force image refresh
      // without refetching the entire book data (DRY: using utility)
      setCoverUrl(getCoverUrlWithCacheBuster(book.id));
      // Notify parent component
      onCoverSaved?.();
    },
  });

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);
    try {
      await uploadBookCover(book.id, file);
      setCoverUrl(getCoverUrlWithCacheBuster(book.id));
      onCoverSaved?.();
    } catch (err) {
      console.error("Failed to upload cover:", err);
      // TODO: Handle error state (maybe reuse error from hook or add new one)
    } finally {
      setIsUploading(false);
    }
  };

  const isLoading = isUrlLoading || isUploading;

  // Use staged cover URL if available, otherwise use local cover URL
  const displayCoverUrl = stagedCoverUrl || coverUrl;

  return (
    <div className="flex flex-col">
      <div className="flex flex-col gap-4">
        <BookCoverDisplay
          book={book}
          coverUrl={displayCoverUrl}
          isLoading={isLoading}
        />
        <BookCoverActions
          book={book}
          isUrlInputVisible={urlInput.isVisible}
          onSetFromUrlClick={handleSetFromUrlClick}
          onFileSelect={handleFileSelect}
          isLoading={isLoading}
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
