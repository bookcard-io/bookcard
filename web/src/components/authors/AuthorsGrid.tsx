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

import { useQueryClient } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useRouter } from "next/navigation";
import { useMemo, useRef, useState } from "react";
import { AuthorEditModal } from "@/components/authors/AuthorEditModal";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { BookCardEditButton } from "@/components/library/BookCardEditButton";
import { getAuthorId, useAuthorSelection } from "@/hooks/useAuthorSelection";
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
 * Same style as BookCardOverlay with selection state support.
 */
interface AuthorCardOverlayProps {
  children: React.ReactNode;
  selected: boolean;
}

function AuthorCardOverlay({ children, selected }: AuthorCardOverlayProps) {
  return (
    <div
      className={cn(
        "absolute inset-0 z-10 transition-[opacity,background-color] duration-200 ease-in-out",
        // Default state: hidden
        "pointer-events-none bg-black/50 opacity-0",
        // When selected: visible but transparent, hide edit/menu buttons
        selected && "bg-transparent opacity-100",
        selected &&
          "[&_.edit-button]:pointer-events-none [&_.edit-button]:opacity-0",
        selected &&
          "[&_.menu-button]:pointer-events-none [&_.menu-button]:opacity-0",
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
 * Handles author selection/deselection via checkbox interaction.
 */
interface AuthorCardCheckboxProps {
  author: AuthorWithMetadata;
  allAuthors: AuthorWithMetadata[];
  selected: boolean;
}

function AuthorCardCheckbox({
  author,
  allAuthors,
  selected,
}: AuthorCardCheckboxProps) {
  const { handleAuthorClick } = useAuthorSelection();

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    // Create a synthetic event with ctrlKey set to toggle behavior
    const syntheticEvent = {
      ...e,
      ctrlKey: true,
      metaKey: false,
      shiftKey: false,
    } as React.MouseEvent;
    handleAuthorClick(author, allAuthors, syntheticEvent);
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
        selected
          ? "border-primary-a0 bg-primary-a0"
          : "border-[var(--color-white)] text-[var(--color-white)] hover:bg-[rgba(144,170,249,0.2)]",
        "[&_i]:block [&_i]:text-sm",
      )}
      onClick={handleClick}
      aria-label={selected ? "Deselect author" : "Select author"}
      onKeyDown={handleKeyDown}
    >
      {selected && <i className="pi pi-check" aria-hidden="true" />}
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

export interface AuthorsGridProps {
  /** Filter type: "all" shows all authors, "unmatched" shows only unmatched authors. */
  filterType?: "all" | "unmatched";
}

/**
 * Authors grid component for displaying a paginated grid of authors.
 *
 * Manages data fetching via useAuthorsViewData hook and renders author cards.
 * Uses virtualization for efficient rendering of large grids.
 * Follows SOC by separating data fetching (hook) from presentation (component).
 */
export function AuthorsGrid({ filterType = "all" }: AuthorsGridProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { authors, isLoading, error, loadMore, hasMore } = useAuthorsViewData({
    pageSize: 20,
    filterType,
  });
  const { isSelected, handleAuthorClick: handleAuthorSelection } =
    useAuthorSelection();
  const [editingAuthorId, setEditingAuthorId] = useState<string | null>(null);

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

  const handleAuthorClick = (
    author: AuthorWithMetadata,
    authors: AuthorWithMetadata[],
    event: React.MouseEvent,
  ) => {
    // Handle selection if modifier keys are pressed
    if (event.ctrlKey || event.metaKey || event.shiftKey) {
      handleAuthorSelection(author, authors, event);
      return;
    }

    // Save scroll position before navigation
    const scrollContainer = document.querySelector(
      '[data-page-scroll-container="true"]',
    ) as HTMLElement | null;
    if (scrollContainer) {
      try {
        sessionStorage.setItem(
          "authors-scroll-position",
          String(scrollContainer.scrollTop),
        );
      } catch {
        // Ignore storage errors
      }
    }

    // Regular click: navigate to author page
    // Use the key if available, otherwise use the name as fallback
    const authorId = author.key
      ? author.key.replace("/authors/", "")
      : encodeURIComponent(author.name);
    router.push(`/authors/${authorId}`);
  };

  const handleAuthorKeyDown = (author: AuthorWithMetadata) => {
    // Save scroll position before navigation
    const scrollContainer = document.querySelector(
      '[data-page-scroll-container="true"]',
    ) as HTMLElement | null;
    if (scrollContainer) {
      try {
        sessionStorage.setItem(
          "authors-scroll-position",
          String(scrollContainer.scrollTop),
        );
      } catch {
        // Ignore storage errors
      }
    }

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
    <div className="w-full px-8">
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
            const endIndex = Math.min(startIndex + columnCount, authors.length);
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
                        onClick={(e) => handleAuthorClick(author, authors, e)}
                        onKeyDown={createEnterSpaceHandler(() =>
                          handleAuthorKeyDown(author),
                        )}
                        data-author-card
                        className={cn(
                          "group cursor-pointer overflow-hidden rounded",
                          "w-full border-2 bg-gradient-to-b p-4 text-left",
                          author.is_unmatched
                            ? "border-primary-a0/30 from-surface-a0 to-surface-a10 hover:border-primary-a0 hover:shadow-[0_0_15px_rgba(144,170,249,0.15)]"
                            : "border-transparent from-surface-a0 to-surface-a10 hover:shadow-card-hover",
                          "transition-[transform,box-shadow,border-color] duration-200 ease-out",
                          "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
                          "focus:not-focus-visible:outline-none focus:outline-none",
                          // Selected state: show primary border and glow
                          isSelected(getAuthorId(author)) &&
                            "border-primary-a0 shadow-primary-glow outline-none",
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
                            <AuthorCardOverlay
                              selected={isSelected(getAuthorId(author))}
                            >
                              <AuthorCardCheckbox
                                author={author}
                                allAuthors={authors}
                                selected={isSelected(getAuthorId(author))}
                              />
                              <BookCardEditButton
                                bookTitle={author.name}
                                onEdit={() => {
                                  setEditingAuthorId(getAuthorId(author));
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
      {!hasMore && !isLoading && authors.length > 0 && (
        <div className="p-4 text-center text-sm text-text-a40">
          No more authors to load
        </div>
      )}
      {editingAuthorId && (
        <AuthorEditModal
          authorId={editingAuthorId}
          onClose={() => {
            setEditingAuthorId(null);
          }}
          onAuthorSaved={(updatedAuthor) => {
            // Update author data in grid when author is saved (O(1) operation)
            // Update all infinite query caches that might contain this author
            queryClient.setQueriesData<{
              pages: Array<{ items: AuthorWithMetadata[] }>;
              pageParams: unknown[];
            }>({ queryKey: ["authors-infinite"] }, (oldData) => {
              if (!oldData) return oldData;
              return {
                ...oldData,
                pages: oldData.pages.map((page) => ({
                  ...page,
                  items: page.items.map((author) => {
                    // Match by key or name (same logic as useAuthors deduplication)
                    const authorId = author.key || author.name;
                    const updatedId = updatedAuthor.key || updatedAuthor.name;
                    if (authorId === updatedId) {
                      return updatedAuthor;
                    }
                    return author;
                  }),
                })),
              };
            });
            // Also update list query cache if it exists
            queryClient.setQueriesData<{ items: AuthorWithMetadata[] }>(
              { queryKey: ["authors"] },
              (oldData) => {
                if (!oldData) return oldData;
                return {
                  ...oldData,
                  items: oldData.items.map((author) => {
                    const authorId = author.key || author.name;
                    const updatedId = updatedAuthor.key || updatedAuthor.name;
                    if (authorId === updatedId) {
                      return updatedAuthor;
                    }
                    return author;
                  }),
                };
              },
            );
          }}
        />
      )}
    </div>
  );
}
