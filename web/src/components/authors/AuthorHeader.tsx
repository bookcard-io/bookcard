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
import { cn } from "@/libs/utils";
import { fetchAuthorMetadata } from "@/services/authorService";
import type { AuthorWithMetadata } from "@/types/author";
import {
  categorizeGenresAndStyles,
  getPrimaryGenre,
} from "@/utils/genreCategorizer";

export interface AuthorHeaderProps {
  /** Author data to display. */
  author: AuthorWithMetadata;
  /** Whether to show full biography. */
  showFullBio?: boolean;
  /** Callback when bio toggle is clicked. */
  onToggleBio?: () => void;
  /** Callback when back button is clicked. */
  onBack?: () => void;
  /** Callback when metadata is successfully fetched. */
  onMetadataFetched?: () => void;
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
  onMetadataFetched,
}: AuthorHeaderProps) {
  const [isPhotoOpen, setIsPhotoOpen] = useState(false);
  const [isFetchingMetadata, setIsFetchingMetadata] = useState(false);
  const [showAllStyles, setShowAllStyles] = useState(false);
  const openPhoto = useCallback(() => setIsPhotoOpen(true), []);
  const closePhoto = useCallback(() => setIsPhotoOpen(false), []);

  const handleFetchMetadata = useCallback(async () => {
    if (isFetchingMetadata) {
      return;
    }

    // Get author ID - use OpenLibrary key
    const authorId = author.key || "";
    if (!authorId) {
      return;
    }

    setIsFetchingMetadata(true);
    try {
      const result = await fetchAuthorMetadata(authorId);
      // Task is now running in background - refetch author data after a delay
      // to allow task to complete (or user can check task status separately)
      setTimeout(() => {
        onMetadataFetched?.();
      }, 2000); // Give task a moment to start
      // TODO: Show success toast with task ID or poll task status
      console.log("Metadata fetch task created:", result.task_id);
    } catch (error) {
      // TODO: Show error toast/notification
      console.error("Failed to fetch metadata:", error);
    } finally {
      setIsFetchingMetadata(false);
    }
  }, [author.key, isFetchingMetadata, onMetadataFetched]);

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
        {author.photo_url && (
          <div className="flex-shrink-0">
            <div className="group relative inline-block leading-none">
              <ImageWithLoading
                src={author.photo_url}
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
              src={author.photo_url}
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
            <button
              type="button"
              onClick={handleFetchMetadata}
              disabled={isFetchingMetadata}
              className="flex items-center gap-2 rounded-md bg-[var(--color-primary-a0)] px-4 py-2 font-medium text-[var(--color-text-primary-a0)] text-sm transition-colors hover:bg-[var(--color-primary-a10)] focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 active:bg-[var(--color-primary-a20)] disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Match author"
            >
              <i
                className={cn(
                  "pi",
                  isFetchingMetadata ? "pi-spin pi-spinner" : "pi-id-card",
                )}
                aria-hidden="true"
              />
              <span>{isFetchingMetadata ? "Matching..." : "Match author"}</span>
            </button>
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
    </>
  );
}
