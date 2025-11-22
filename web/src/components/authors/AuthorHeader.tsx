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

import { useCallback, useEffect, useRef, useState } from "react";
import { AuthorEditModal } from "@/components/authors/AuthorEditModal";
import { FullscreenImageModal } from "@/components/common/FullscreenImageModal";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { cn } from "@/libs/utils";
import type { AuthorWithMetadata } from "@/types/author";
import {
  categorizeGenresAndStyles,
  getPrimaryGenre,
} from "@/utils/genreCategorizer";

/**
 * Normalize an OpenLibrary author key to a bare OLID.
 *
 * Examples
 * --------
 * - "/authors/OL52940A" -> "OL52940A"
 * - "authors/OL52940A" -> "OL52940A"
 * - "OL52940A" -> "OL52940A"
 */
const normalizeAuthorKey = (key?: string | null): string =>
  key?.replace(/^\/?authors\//, "").replace(/^\//, "") ?? "";

/**
 * Build the author identifier used for rematch requests.
 *
 * The backend prefers a Calibre-based identifier so it can always
 * resolve or create the appropriate mapping, regardless of whether
 * the author is already matched:
 *
 * - If `calibre_id` is present, use `calibre-{calibre_id}`.
 * - Otherwise, fall back to an existing `calibre-` style key.
 * - As a last resort, use a normalized OpenLibrary key.
 */
const buildRematchAuthorId = (author: AuthorWithMetadata): string | null => {
  if (author.calibre_id != null) {
    return `calibre-${author.calibre_id}`;
  }

  if (author.key?.startsWith("calibre-")) {
    return author.key;
  }

  const normalizedKey = normalizeAuthorKey(author.key);
  return normalizedKey || null;
};

export interface AuthorHeaderProps {
  /** Author data to display. */
  author: AuthorWithMetadata;
  /** Whether to show full biography. */
  showFullBio?: boolean;
  /** Callback when bio toggle is clicked. */
  onToggleBio?: () => void;
  /** Callback when back button is clicked. */
  onBack?: () => void;
  /** Callback to update author object in place. */
  onAuthorUpdate?: (updatedAuthor: AuthorWithMetadata) => void;
}

/**
 * Author header component.
 *
 * Displays author image, name, location, genres, rating, action buttons,
 * and biography. Similar to Plex artist header layout.
 * Follows SRP by focusing solely on header presentation.
 *
 * Parameters
 * ----------
 * props : AuthorHeaderProps
 *     Component props including author data and callbacks.
 */
export function AuthorHeader({
  author,
  showFullBio = false,
  onToggleBio,
  onBack,
  onAuthorUpdate,
}: AuthorHeaderProps) {
  const [isPhotoOpen, setIsPhotoOpen] = useState(false);
  const [showAllStyles, setShowAllStyles] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isRematching, setIsRematching] = useState(false);
  const [showOlidInput, setShowOlidInput] = useState(false);
  const [olidInput, setOlidInput] = useState("");
  const olidInputRef = useRef<HTMLInputElement>(null);
  // Track photo URL separately to avoid remounting on updates
  const [photoUrl, setPhotoUrl] = useState<string | null | undefined>(
    author.photo_url,
  );
  const authorKeyRef = useRef<string | undefined>(author.key);

  // Update photo URL when author changes
  useEffect(() => {
    if (author.key !== authorKeyRef.current) {
      // Different author - reset photo URL
      authorKeyRef.current = author.key;
    }
    // Always update photo URL when author.photo_url changes (idempotent)
    setPhotoUrl(author.photo_url);
  }, [author.key, author.photo_url]);

  const openPhoto = useCallback(() => setIsPhotoOpen(true), []);
  const closePhoto = useCallback(() => setIsPhotoOpen(false), []);
  const openEditModal = useCallback(() => setIsEditModalOpen(true), []);
  const closeEditModal = useCallback(() => setIsEditModalOpen(false), []);

  const handleShowOlidInput = useCallback(() => {
    setShowOlidInput(true);
    const normalizedKey = normalizeAuthorKey(author.key);
    // For already-matched authors, prefill with existing OLID.
    // For unmatched authors, leave blank so user must provide an OLID.
    const initialOlid =
      author.is_unmatched || author.key?.startsWith("calibre-")
        ? ""
        : normalizedKey;
    setOlidInput(initialOlid);
    // Focus the input after it's rendered
    setTimeout(() => {
      olidInputRef.current?.focus();
    }, 0);
  }, [author.is_unmatched, author.key]);

  const handleCancelOlidInput = useCallback(() => {
    setShowOlidInput(false);
    setOlidInput("");
  }, []);

  const handleRematch = useCallback(
    async (olid?: string) => {
      const authorIdForRematch = buildRematchAuthorId(author);
      if (isRematching || !authorIdForRematch) {
        return;
      }

      setIsRematching(true);
      try {
        const response = await fetch(
          `/api/authors/${authorIdForRematch}/rematch`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(olid ? { openlibrary_key: olid } : {}),
          },
        );

        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(errorData.detail || "Failed to rematch author");
        }

        const result = (await response.json()) as { message: string };
        console.log("Author rematch job enqueued:", result.message);
        // TODO: Show success toast/notification
        setShowOlidInput(false);
        setOlidInput("");
      } catch (error) {
        console.error("Failed to rematch author:", error);
        // TODO: Show error toast/notification
      } finally {
        setIsRematching(false);
      }
    },
    [author, isRematching],
  );

  const handleSubmitOlid = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmedOlid = olidInput.trim();
      if (trimmedOlid) {
        handleRematch(trimmedOlid);
      }
    },
    [olidInput, handleRematch],
  );

  // Extract bio text
  const bioText = author.bio?.value || "";
  const shouldTruncate = bioText.length > 300 && !showFullBio;
  const displayBio = shouldTruncate
    ? `${bioText.substring(0, 300)}...`
    : bioText;

  // Categorize genres and styles
  const subjects = author.genres || [];
  const { styles: allStyles } = categorizeGenresAndStyles(subjects);
  // Limit to 1 primary genre
  const primaryGenre = getPrimaryGenre(subjects);
  // Show 3 styles initially, expand to 10 on "and more" click
  const maxStyles = showAllStyles ? 10 : 3;
  const displayedStyles = allStyles.slice(0, maxStyles);
  const hasMoreStyles = allStyles.length > 3;

  return (
    <>
      {/* Back button */}
      {onBack && (
        <button
          type="button"
          onClick={onBack}
          className="mb-4 flex items-center gap-2 text-sm text-text-a30 transition-colors hover:text-text-a0 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
          aria-label="Back to authors"
        >
          <i className="pi pi-arrow-left" aria-hidden="true" />
          <span>Back to Authors</span>
        </button>
      )}

      <div className="flex flex-col gap-6 md:flex-row md:gap-8">
        {/* Author Photo */}
        {photoUrl && (
          <div className="flex-shrink-0">
            <div className="group relative inline-block leading-none">
              <ImageWithLoading
                key={author.key} // Stable key based on author key, not photo URL
                src={photoUrl}
                alt={`Photo of ${author.name}`}
                width={250}
                height={250}
                className="rounded-md object-cover shadow-[0_4px_12px_rgba(0,0,0,0.3)]"
                containerClassName="inline-block"
                unoptimized
              />
              <button
                type="button"
                className="pointer-events-none absolute inset-0 flex cursor-default items-center justify-center rounded-md bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.25)_0%,rgba(0,0,0,0.35)_60%,rgba(0,0,0,0.45)_100%)] opacity-0 transition-opacity duration-200 ease-linear hover:bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.3)_0%,rgba(0,0,0,0.45)_60%,rgba(0,0,0,0.55)_100%)] focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 group-hover:pointer-events-auto group-hover:opacity-100"
                aria-label="View photo full screen"
                title="View photo"
                onClick={openPhoto}
              >
                <i
                  className="pi pi-arrow-up-right-and-arrow-down-left-from-center text-[1.5rem] text-[var(--color-text-a0)] opacity-95 transition-transform duration-100 ease-linear hover:scale-110"
                  aria-hidden="true"
                />
              </button>
            </div>
            <FullscreenImageModal
              src={photoUrl}
              alt={`Photo of ${author.name}`}
              isOpen={isPhotoOpen}
              onClose={closePhoto}
            />
          </div>
        )}

        {/* Author Details */}
        <div className="flex min-w-0 flex-1 flex-col gap-4">
          {/* Name */}
          <h1 className="m-0 font-bold text-3xl text-[var(--color-text-a0)] leading-tight md:text-4xl">
            {author.name}
          </h1>

          {/* Location */}
          {author.location && (
            <div className="text-[var(--color-text-a30)] text-base">
              {author.location}
            </div>
          )}

          {/* Genre */}
          {primaryGenre && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[var(--color-text-a0)] text-sm">
                {primaryGenre}
              </span>
            </div>
          )}

          {/* Rating (placeholder - 0 stars for now) */}
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <i
                key={star}
                className="pi pi-star text-[var(--color-text-a40)] text-base"
                aria-hidden="true"
              />
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3">
            {showOlidInput ? (
              <form
                onSubmit={handleSubmitOlid}
                className="flex items-center gap-2"
              >
                <input
                  ref={olidInputRef}
                  type="text"
                  value={olidInput}
                  onChange={(e) => setOlidInput(e.target.value)}
                  placeholder="Enter OLID (e.g., OL676009W)"
                  disabled={isRematching}
                  className="rounded-md border border-surface-a20 bg-surface-tonal-a10 px-3 py-2 text-[var(--color-text-a0)] text-sm placeholder:text-[var(--color-text-a40)] focus:border-[var(--color-primary-a0)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={isRematching || !olidInput.trim()}
                  className="flex items-center gap-2 rounded-md bg-[var(--color-primary-a0)] px-4 py-2 font-medium text-[var(--color-text-primary-a0)] text-sm transition-colors hover:bg-[var(--color-primary-a10)] focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 active:bg-[var(--color-primary-a20)] disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="Submit OLID"
                >
                  <i
                    className={cn(
                      "pi",
                      isRematching ? "pi-spin pi-spinner" : "pi-check",
                    )}
                    aria-hidden="true"
                  />
                  <span>{isRematching ? "Matching..." : "Match"}</span>
                </button>
                <button
                  type="button"
                  onClick={handleCancelOlidInput}
                  disabled={isRematching}
                  className="flex h-9 w-9 items-center justify-center rounded-md border border-surface-a20 bg-surface-tonal-a10 text-text-a30 transition-[background-color,border-color] duration-200 hover:border-surface-a30 hover:bg-surface-tonal-a20 hover:text-text-a0 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="Cancel"
                  title="Cancel"
                >
                  <i className="pi pi-times" aria-hidden="true" />
                </button>
              </form>
            ) : (
              <button
                type="button"
                onClick={handleShowOlidInput}
                disabled={!author.key}
                className="flex items-center gap-2 rounded-md bg-[var(--color-primary-a0)] px-4 py-2 font-medium text-[var(--color-text-primary-a0)] text-sm transition-colors hover:bg-[var(--color-primary-a10)] focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 active:bg-[var(--color-primary-a20)] disabled:cursor-not-allowed disabled:opacity-50"
                aria-label="Match author"
              >
                <i className="pi pi-id-card" aria-hidden="true" />
                <span>Match author</span>
              </button>
            )}
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-md border border-surface-a20 bg-surface-tonal-a10 text-text-a30 transition-[background-color,border-color] duration-200 hover:border-surface-a30 hover:bg-surface-tonal-a20 hover:text-text-a0 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
              aria-label="Align justify"
              title="Align justify"
            >
              <i className="pi pi-align-justify" aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={openEditModal}
              className="flex h-9 w-9 items-center justify-center rounded-md border border-surface-a20 bg-surface-tonal-a10 text-text-a30 transition-[background-color,border-color] duration-200 hover:border-surface-a30 hover:bg-surface-tonal-a20 hover:text-text-a0 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
              aria-label="Edit"
              title="Edit"
            >
              <i className="pi pi-pencil" aria-hidden="true" />
            </button>
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-md border border-surface-a20 bg-surface-tonal-a10 text-text-a30 transition-[background-color,border-color] duration-200 hover:border-surface-a30 hover:bg-surface-tonal-a20 hover:text-text-a0 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
              aria-label="More options"
              title="More options"
            >
              <i className="pi pi-ellipsis-h" aria-hidden="true" />
            </button>
          </div>

          {/* Biography */}
          {bioText && (
            <div className="mt-2 flex flex-col gap-2">
              <div
                className={cn(
                  "max-w-[700px] text-[var(--color-text-a20)] text-sm leading-relaxed",
                  shouldTruncate && "line-clamp-3",
                )}
              >
                {displayBio}
              </div>
              {bioText.length > 300 && (
                <button
                  type="button"
                  onClick={onToggleBio}
                  className="flex w-fit items-center gap-1 text-[var(--color-primary-a0)] text-sm transition-colors hover:text-[var(--color-primary-a10)] focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
                  aria-label={showFullBio ? "Show less" : "Show more"}
                >
                  <span>{showFullBio ? "Show less" : "More"}</span>
                  <i
                    className={cn(
                      "pi text-xs transition-transform",
                      showFullBio ? "pi-chevron-up" : "pi-chevron-down",
                    )}
                    aria-hidden="true"
                  />
                </button>
              )}
            </div>
          )}

          {/* Styles Section */}
          {displayedStyles.length > 0 && (
            <div className="mt-4 flex flex-col items-start gap-1 sm:flex-row sm:items-center sm:gap-2 md:gap-10">
              <span className="font-medium text-[var(--color-text-a30)] text-sm">
                Style
              </span>
              <div className="flex flex-wrap items-center gap-1 text-[var(--color-text-a20)] text-sm">
                {displayedStyles.map((style, index) => (
                  <span key={style}>
                    {style}
                    {index < displayedStyles.length - 1 && ","}
                  </span>
                ))}
                {hasMoreStyles && !showAllStyles && (
                  <button
                    type="button"
                    onClick={() => setShowAllStyles(true)}
                    className="cursor-pointer text-[var(--color-text-a30)] transition-colors hover:text-[var(--color-text-a0)] focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
                    aria-label="Show more styles"
                  >
                    and more
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Author Edit Modal */}
      {isEditModalOpen && author.key && (
        <AuthorEditModal
          authorId={author.key}
          onClose={closeEditModal}
          onAuthorSaved={(updatedAuthor) => {
            // Update photo URL immediately from the updated author
            if (updatedAuthor.photo_url !== photoUrl) {
              setPhotoUrl(updatedAuthor.photo_url);
            }
            // Update parent author object in place to avoid remount
            onAuthorUpdate?.(updatedAuthor);
            closeEditModal();
            // Only refetch if other metadata might have changed (not just photo)
            // onMetadataFetched?.();
          }}
        />
      )}
    </>
  );
}
