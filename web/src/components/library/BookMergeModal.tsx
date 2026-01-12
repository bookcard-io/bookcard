// Copyright (C) 2026 knguyen and others
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
import { useEffect, useRef, useState } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { cn } from "@/libs/utils";
import {
  type BookMergeRecommendation,
  mergeBooks,
  recommendMergeBooks,
} from "@/services/bookService";

export interface BookMergeModalProps {
  /** List of book IDs to merge. */
  bookIds: number[];
  /** Callback when modal should be closed. */
  onClose: () => void;
}

type BookDetail = BookMergeRecommendation["books"][0];

/**
 * Modal component for merging books.
 *
 * Displays all books to merge and allows user to select which one to keep.
 * Automatically recommends the best book based on metadata and file quality.
 */
export function BookMergeModal({ bookIds, onClose }: BookMergeModalProps) {
  const queryClient = useQueryClient();
  const { showSuccess, showDanger } = useGlobalMessages();
  // Store bookIds in state to preserve them even if prop changes
  const [preservedBookIds] = useState<number[]>(bookIds);
  const [books, setBooks] = useState<BookDetail[]>([]);
  const [recommendedKeepId, setRecommendedKeepId] = useState<number | null>(
    null,
  );
  const [selectedKeepId, setSelectedKeepId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMerging, setIsMerging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDryRun, setShowDryRun] = useState(false);
  const dryRunRef = useRef<HTMLDivElement>(null);

  // Fetch recommendation on mount
  useEffect(() => {
    const fetchRecommendation = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await recommendMergeBooks(preservedBookIds);
        setBooks(result.books);
        setRecommendedKeepId(result.recommended_keep_id);
        setSelectedKeepId(result.recommended_keep_id);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load book details",
        );
      } finally {
        setIsLoading(false);
      }
    };

    if (preservedBookIds.length >= 2) {
      void fetchRecommendation();
    }
  }, [preservedBookIds]);

  const handleDryRun = () => {
    setShowDryRun(true);
  };

  // Scroll to dry run section when it becomes visible
  useEffect(() => {
    if (showDryRun && dryRunRef.current) {
      // Use setTimeout to ensure DOM has updated
      setTimeout(() => {
        dryRunRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }, 100);
    }
  }, [showDryRun]);

  const handleMerge = async () => {
    if (!selectedKeepId) {
      return;
    }

    setIsMerging(true);
    setError(null);

    try {
      await mergeBooks(preservedBookIds, selectedKeepId);
      const keepBook = books.find((b) => b.id === selectedKeepId);
      const bookTitle = keepBook?.title || "books";
      showSuccess(`Successfully merged books into "${bookTitle}"`);

      // Invalidate books queries to refresh the grid
      await queryClient.invalidateQueries({ queryKey: ["books"] });
      await queryClient.invalidateQueries({ queryKey: ["books-infinite"] });

      onClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to merge books";
      setError(errorMessage);
      showDanger(errorMessage);
    } finally {
      setIsMerging(false);
    }
  };

  // Calculate dry run steps
  const getDryRunSteps = () => {
    if (!selectedKeepId) {
      return [];
    }

    const keepBook = books.find((b) => b.id === selectedKeepId);
    const mergeBooks = books.filter((b) => b.id !== selectedKeepId);

    if (!keepBook) {
      return [];
    }

    const steps: Array<{ type: string; description: string }> = [];

    // Step 1: Identify keep book
    steps.push({
      type: "keep",
      description: `Keep "${keepBook.title}" (ID: ${keepBook.id})`,
    });

    // Step 2: Analyze merges
    mergeBooks.forEach((mergeBook) => {
      // Metadata
      steps.push({
        type: "metadata",
        description: `Merge metadata from "${mergeBook.title}" into "${keepBook.title}" (filling empty fields)`,
      });

      // Cover
      if (mergeBook.has_cover) {
        if (!keepBook.has_cover) {
          steps.push({
            type: "cover",
            description: `Copy cover from "${mergeBook.title}" to "${keepBook.title}"`,
          });
        } else {
          // Heuristic check (frontend guess, backend does actual logic)
          steps.push({
            type: "cover",
            description: `Compare covers: if "${mergeBook.title}" has better quality, replace "${keepBook.title}" cover`,
          });
        }
      }

      // Files
      if (mergeBook.formats && mergeBook.formats.length > 0) {
        mergeBook.formats.forEach((fmt) => {
          const keepFormat = keepBook.formats?.find(
            (f) => f.format === fmt.format,
          );
          if (keepFormat) {
            steps.push({
              type: "file_conflict",
              description: `File conflict for ${fmt.format}: If merged file is larger, replace keep file (backing up original as .bak). Otherwise backup merged file as .bak.`,
            });
          } else {
            steps.push({
              type: "file_move",
              description: `Move ${fmt.format} file from "${mergeBook.title}" to "${keepBook.title}"`,
            });
          }
        });
      }

      // Delete
      steps.push({
        type: "delete",
        description: `Delete "${mergeBook.title}" (ID: ${mergeBook.id}) after merge`,
      });
    });

    // Final result
    steps.push({
      type: "result",
      description: `Final result: "${keepBook.title}" will contain merged files and metadata`,
    });

    return steps;
  };

  const dryRunSteps = getDryRunSteps();

  if (isLoading) {
    return (
      <div
        className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70"
        role="dialog"
        aria-modal
        aria-labelledby="merge-modal-title"
      >
        <div className="modal-container modal-container-shadow-default flex h-[75vh] min-h-[75vh] w-full max-w-3xl flex-col overflow-hidden">
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
            Loading book details...
          </div>
        </div>
      </div>
    );
  }

  if (error && books.length === 0) {
    return (
      <div
        className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70"
        role="dialog"
        aria-modal
        aria-labelledby="merge-modal-title"
      >
        <div className="modal-container modal-container-shadow-default flex h-[75vh] min-h-[75vh] w-full max-w-3xl flex-col overflow-hidden">
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
            <p className="text-red-500">{error}</p>
            <Button onClick={onClose}>Close</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70"
      role="dialog"
      aria-modal
      aria-labelledby="merge-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          onClose();
        }
      }}
    >
      <div className="modal-container modal-container-shadow-default flex h-[75vh] min-h-[75vh] w-full max-w-3xl flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-surface-a20 border-b p-6">
          <h2
            id="merge-modal-title"
            className="m-0 font-semibold text-[var(--color-text-a0)] text-xl"
          >
            Merge Books
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-md text-text-a30 transition-colors hover:bg-surface-a10 hover:text-text-a0 focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2"
            aria-label="Close"
          >
            <i className="pi pi-times" aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <p className="mb-4 text-sm text-text-a30">
            Select which book to keep. All other books will be merged into the
            selected one.
          </p>

          {error && (
            <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-red-500 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-3">
            {books.map((book) => {
              const isRecommended = book.id === recommendedKeepId;
              const isSelected = book.id === selectedKeepId;

              return (
                <button
                  key={book.id}
                  type="button"
                  className={cn(
                    "flex w-full cursor-pointer items-center gap-4 rounded-md border-2 p-4 text-left transition-colors",
                    isSelected
                      ? "border-primary-a0 bg-primary-a0/10"
                      : "border-surface-a20 hover:border-surface-a30 hover:bg-surface-a10",
                  )}
                  onClick={() => {
                    setSelectedKeepId(book.id);
                    setShowDryRun(false);
                  }}
                >
                  <input
                    type="radio"
                    checked={isSelected}
                    onChange={() => {
                      setSelectedKeepId(book.id);
                      setShowDryRun(false);
                    }}
                    className="h-4 w-4 flex-shrink-0 cursor-pointer"
                    readOnly
                    tabIndex={-1}
                    aria-hidden="true"
                  />
                  {/* Book Cover */}
                  <div className="relative h-24 w-16 flex-shrink-0 overflow-hidden rounded-md shadow-sm">
                    {book.has_cover ? (
                      <ImageWithLoading
                        src={`/api/books/${book.id}/cover`}
                        alt={`Cover of ${book.title}`}
                        width={64}
                        height={96}
                        className="h-full w-full object-cover"
                        containerClassName="h-full w-full"
                        unoptimized
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-surface-a20 text-center text-[10px]">
                        No Cover
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="m-0 font-medium text-[var(--color-text-a0)] text-base">
                        {book.title}
                      </h3>
                      {isRecommended && (
                        <span className="rounded-full bg-primary-a0/20 px-2 py-0.5 text-primary-a0 text-xs">
                          Recommended
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-col gap-1 text-sm text-text-a30">
                      <span>{book.author || "Unknown Author"}</span>
                      <div className="flex flex-wrap gap-3 text-xs">
                        {book.year && <span>{book.year}</span>}
                        {book.publisher && <span>{book.publisher}</span>}
                      </div>
                      <div className="flex flex-wrap gap-2 pt-1">
                        {book.formats.map((f) => (
                          <span
                            key={f.format}
                            className="rounded bg-surface-a20 px-1.5 py-0.5 font-medium text-text-a60 text-xs"
                          >
                            {f.format} ({(f.size / 1024 / 1024).toFixed(2)} MB)
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Dry Run Steps */}
          {showDryRun && selectedKeepId && dryRunSteps.length > 0 && (
            <div
              ref={dryRunRef}
              className="mt-6 rounded-md border border-primary-a0/30 bg-primary-a0/5 p-4"
            >
              <h3 className="mb-3 font-semibold text-[var(--color-text-a0)] text-sm">
                Dry Run - Merge Steps
              </h3>
              <ol className="space-y-2 text-sm">
                {dryRunSteps.map((step, index) => {
                  let icon = "pi-circle";
                  let textColor = "text-text-a30";

                  if (step.type === "keep") {
                    icon = "pi-check-circle";
                    textColor = "text-green-500";
                  } else if (
                    step.type === "metadata" ||
                    step.type === "file_move"
                  ) {
                    icon = "pi-arrow-right";
                    textColor = "text-primary-a0";
                  } else if (step.type === "cover") {
                    icon = "pi-image";
                    textColor = "text-primary-a0";
                  } else if (step.type === "file_conflict") {
                    icon = "pi-exclamation-circle";
                    textColor = "text-orange-500";
                  } else if (step.type === "delete") {
                    icon = "pi-trash";
                    textColor = "text-orange-500";
                  } else if (step.type === "result") {
                    icon = "pi-check";
                    textColor = "text-primary-a0 font-semibold";
                  }

                  return (
                    <li
                      key={`${step.type}-${step.description}-${index}`}
                      className={cn("flex items-start gap-2", textColor)}
                    >
                      <i className={cn("pi mt-0.5", icon)} aria-hidden="true" />
                      <span>{step.description}</span>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-surface-a20 border-t p-6">
          <Button variant="secondary" onClick={onClose} disabled={isMerging}>
            Cancel
          </Button>
          <Button
            variant="secondary"
            onClick={handleDryRun}
            disabled={!selectedKeepId || isMerging}
          >
            Dry run
          </Button>
          <Button onClick={handleMerge} disabled={!selectedKeepId || isMerging}>
            {isMerging && (
              <i className="pi pi-spin pi-spinner" aria-hidden="true" />
            )}
            {isMerging ? "Merging..." : "Merge books"}
          </Button>
        </div>
      </div>
    </div>
  );
}
