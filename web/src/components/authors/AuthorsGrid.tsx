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

import { useVirtualizer } from "@tanstack/react-virtual";
import { useRouter } from "next/navigation";
import { useMemo, useRef, useState } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { BookCardEditButton } from "@/components/library/BookCardEditButton";
import { useAuthorsViewData } from "@/hooks/useAuthorsViewData";
import { useInfiniteScrollVirtualizer } from "@/hooks/useInfiniteScrollVirtualizer";
import { useResponsiveGridLayout } from "@/hooks/useResponsiveGridLayout";
import { cn } from "@/libs/utils";
import type { AuthorWithMetadata } from "@/types/author";
import { createEnterSpaceHandler } from "@/utils/keyboard";

/**
 * Author card overlay component.
 *
 * Provides overlay background and visibility states for overlay buttons.
 * Same style as BookCardOverlay but without selection state.
 */
function AuthorCardOverlay({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "absolute inset-0 z-10 transition-[opacity,background-color] duration-200 ease-in-out",
        // Default state: hidden
        "pointer-events-none bg-black/50 opacity-0",
        // On hover: show overlay and all buttons (using parent button's group)
        "group-hover:bg-black/50 group-hover:opacity-100",
        "group-hover:[&_.edit-button]:pointer-events-auto group-hover:[&_.edit-button]:opacity-100",
        "group-hover:[&_.menu-button]:pointer-events-auto group-hover:[&_.menu-button]:opacity-100",
        "group-hover:[&_.checkbox]:pointer-events-auto",
      )}
    >
      {children}
    </div>
  );
}

/**
 * Author card checkbox component.
 *
 * No-op checkbox for author selection (wired to no-op for now).
 */
function AuthorCardCheckbox() {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    // No-op for now
  };

  const handleKeyDown = createEnterSpaceHandler(() => {
    handleClick({} as React.MouseEvent<HTMLButtonElement>);
  });

  return (
    <button
      type="button"
      className={cn(
        "checkbox pointer-events-auto flex cursor-default items-center justify-center",
        "transition-[background-color,border-color] duration-200 ease-in-out",
        "focus:shadow-focus-ring focus:outline-none",
        "absolute top-3 left-3 h-6 w-6 rounded border-2 bg-transparent p-0",
        "border-[var(--color-white)] text-[var(--color-white)] hover:bg-[rgba(144,170,249,0.2)]",
        "[&_i]:block [&_i]:text-sm",
      )}
      onClick={handleClick}
      aria-label="Select author"
      onKeyDown={handleKeyDown}
    >
      {/* No check icon for now since it's no-op */}
    </button>
  );
}

/**
 * Author card menu button component.
 *
 * No-op menu button for author card (wired to no-op for now).
 */
function AuthorCardMenuButton() {
  const [isMenuOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  const handleToggle = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    // No-op for now
  };

  const handleKeyDown = createEnterSpaceHandler(() => {
    handleToggle({} as React.MouseEvent<HTMLButtonElement>);
  });

  return (
    <div className="absolute right-3 bottom-3 z-20">
      <button
        ref={buttonRef}
        type="button"
        className={cn(
          "menu-button pointer-events-auto flex cursor-default items-center justify-center",
          "transition-[background-color,transform,opacity] duration-200 ease-in-out",
          "focus:shadow-focus-ring focus:outline-none",
          "active:scale-95",
          "h-10 w-10 rounded-full text-[var(--color-white)]",
          "border-none bg-white/20 backdrop-blur-sm",
          "hover:scale-110 hover:bg-white/30 [&_i]:block [&_i]:text-lg",
        )}
        onClick={handleToggle}
        aria-label="Menu"
        aria-haspopup="true"
        aria-expanded={isMenuOpen}
        onKeyDown={handleKeyDown}
      >
        <i className="pi pi-ellipsis-v" aria-hidden="true" />
      </button>
    </div>
  );
}

/**
 * Authors grid component for displaying a paginated grid of authors.
 *
 * Manages data fetching via useAuthorsViewData hook and renders author cards.
 * Uses virtualization for efficient rendering of large grids.
 * Follows SOC by separating data fetching (hook) from presentation (component).
 */
export function AuthorsGrid() {
  const router = useRouter();
  const { authors, isLoading, error, loadMore, hasMore } = useAuthorsViewData({
    pageSize: 20,
  });

  // Container ref for responsive layout calculations (not the scroll container)
  const parentRef = useRef<HTMLDivElement | null>(null);

  // Responsive grid layout shared between CSS and virtualizer math
  const { columnCount, cardWidth, gap } = useResponsiveGridLayout(parentRef);

  // Compute number of virtualized rows based on responsive column count
  const rowCount = useMemo(
    () => Math.max(1, Math.ceil(authors.length / Math.max(columnCount, 1))),
    [authors.length, columnCount],
  );

  // Estimate row height from card width and aspect ratio; refined via measureElement.
  const estimatedRowHeight = useMemo(() => {
    const coverAspectRatio = 1; // square aspect ratio for author photos
    const metadataHeight = 60; // name + location + spacing
    const padding = 16; // p-4 = 1rem = 16px
    const cardHeight = cardWidth * coverAspectRatio + metadataHeight + padding;
    return cardHeight + gap;
  }, [cardWidth, gap]);

  // Virtualizer for efficient rendering of large grids (virtualizing rows).
  const rowVirtualizer = useVirtualizer({
    count: hasMore ? rowCount + 1 : rowCount,
    // Use the main page scroll container defined in PageLayout so that
    // virtual rows respond to the actual scrollable area, not window scroll.
    getScrollElement: () =>
      typeof document !== "undefined"
        ? (document.querySelector(
            '[data-page-scroll-container="true"]',
          ) as HTMLElement | null)
        : null,
    estimateSize: () => estimatedRowHeight,
    overscan: 3,
    // Always measure actual DOM height so row offsets stay accurate
    measureElement: (element) => element?.getBoundingClientRect().height,
  });

  // Infinite scroll: load more when we scroll close to the last row (SRP: scroll concerns separated)
  useInfiniteScrollVirtualizer({
    virtualizer: rowVirtualizer,
    itemCount: rowCount,
    hasMore: hasMore ?? false,
    isLoading,
    loadMore,
    threshold: 2, // within 2 rows of the end
  });

  const handleAuthorClick = (author: AuthorWithMetadata) => {
    // Use the key if available, otherwise use the name as fallback
    const authorId = author.key
      ? author.key.replace("/authors/", "")
      : encodeURIComponent(author.name);
    router.push(`/authors/${authorId}`);
  };

  // Error state (SRP: error display separated)
  if (error) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
        {error}
      </div>
    );
  }

  // Loading state (SRP: loading display separated)
  if (isLoading && authors.length === 0) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
        Loading authors...
      </div>
    );
  }

  // Empty state (SRP: empty display separated)
  if (authors.length === 0) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
        No authors found
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="px-8">
        <div ref={parentRef} className="relative w-full">
          <div
            className="relative w-full"
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const isLoaderRow = hasMore && virtualRow.index >= rowCount;

              if (isLoaderRow) {
                return (
                  <div
                    key={`loader-${virtualRow.index}`}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      maxWidth: "100%",
                      paddingBottom: `${gap}px`,
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    <div className="p-4 text-center text-sm text-text-a40">
                      {isLoading
                        ? "Loading more authors..."
                        : "No more authors to load"}
                    </div>
                  </div>
                );
              }

              const startIndex = virtualRow.index * columnCount;
              const endIndex = Math.min(
                startIndex + columnCount,
                authors.length,
              );
              const rowAuthors = authors.slice(startIndex, endIndex);

              if (!rowAuthors.length) {
                return null;
              }

              return (
                <div
                  key={virtualRow.index}
                  data-index={virtualRow.index}
                  ref={rowVirtualizer.measureElement}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    maxWidth: "100%",
                    paddingBottom: `${gap}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  <div
                    className="flex"
                    style={{
                      gap: `${gap}px`,
                      width: "100%",
                      maxWidth: "100%",
                    }}
                  >
                    {rowAuthors.map((author) => (
                      <div
                        key={author.key || author.name}
                        className="flex"
                        style={{
                          flex: `0 0 ${cardWidth}px`,
                          width: `${cardWidth}px`,
                        }}
                      >
                        {/* biome-ignore lint/a11y/useSemanticElements: Cannot use <button> here due to nested buttons (checkbox, menu) inside. Using div with proper ARIA for accessibility. */}
                        <div
                          role="button"
                          tabIndex={0}
                          onClick={() => handleAuthorClick(author)}
                          onKeyDown={createEnterSpaceHandler(() =>
                            handleAuthorClick(author),
                          )}
                          className={cn(
                            "group cursor-pointer overflow-hidden rounded",
                            "w-full border-2 border-transparent bg-gradient-to-b from-surface-a0 to-surface-a10 p-4 text-left",
                            "transition-[transform,box-shadow,border-color] duration-200 ease-out",
                            "hover:-translate-y-0.5 hover:shadow-card-hover",
                            "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
                            "focus:not-focus-visible:outline-none focus:outline-none",
                          )}
                          aria-label={`View ${author.name}`}
                        >
                          {/* Author Photo */}
                          <div className="relative aspect-square w-full overflow-hidden rounded-md">
                            {author.photo_url ? (
                              <ImageWithLoading
                                src={author.photo_url}
                                alt={`Photo of ${author.name}`}
                                width={200}
                                height={200}
                                className="h-full w-full object-cover"
                                containerClassName="h-full w-full"
                                unoptimized
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center bg-surface-a20">
                                <i
                                  className="pi pi-user text-4xl text-text-a40"
                                  aria-hidden="true"
                                />
                              </div>
                            )}
                            {/* Desktop overlay (hidden on mobile) */}
                            <div className="hidden md:block">
                              <AuthorCardOverlay>
                                <AuthorCardCheckbox />
                                <BookCardEditButton
                                  bookTitle={author.name}
                                  onEdit={() => {
                                    // No-op for now
                                  }}
                                />
                                <AuthorCardMenuButton />
                              </AuthorCardOverlay>
                            </div>
                          </div>

                          {/* Author Name */}
                          <div className="flex min-w-0 flex-col gap-1">
                            <h3 className="m-0 truncate font-medium text-[var(--color-text-a0)] text-sm group-hover:text-[var(--color-primary-a0)]">
                              {author.name}
                            </h3>
                            {author.location && (
                              <p className="m-0 truncate text-[var(--color-text-a30)] text-xs">
                                {author.location}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      {!hasMore && !isLoading && authors.length > 0 && (
        <div className="p-4 px-8 text-center text-sm text-text-a40">
          No more authors to load
        </div>
      )}
    </div>
  );
}
