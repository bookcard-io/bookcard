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
import { useEffect, useRef, useState } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useAuthorSelection } from "@/hooks/useAuthorSelection";
import { cn } from "@/libs/utils";
import { mergeAuthors, recommendMergeAuthor } from "@/services/authorService";

export interface AuthorMergeModalProps {
  /** List of author IDs to merge. */
  authorIds: string[];
  /** Callback when modal should be closed. */
  onClose: () => void;
}

interface AuthorDetail {
  id: string | null;
  key: string | null;
  name: string;
  book_count: number;
  is_verified: boolean;
  metadata_score: number;
  photo_url: string | null;
  relationship_counts?: {
    alternate_names: number;
    remote_ids: number;
    photos: number;
    links: number;
    works: number;
    work_subjects: number;
    similarities: number;
    user_metadata: number;
    user_photos: number;
  };
}

/**
 * Modal component for merging authors.
 *
 * Displays all authors to merge and allows user to select which one to keep.
 * Automatically recommends the best author based on metadata and book count.
 */
export function AuthorMergeModal({
  authorIds,
  onClose,
}: AuthorMergeModalProps) {
  const queryClient = useQueryClient();
  const { clearSelection } = useAuthorSelection();
  const { showSuccess, showDanger } = useGlobalMessages();
  // Store authorIds in state to preserve them even if prop changes
  const [preservedAuthorIds] = useState<string[]>(authorIds);
  const [authors, setAuthors] = useState<AuthorDetail[]>([]);
  const [recommendedKeepId, setRecommendedKeepId] = useState<string | null>(
    null,
  );
  const [selectedKeepId, setSelectedKeepId] = useState<string | null>(null);
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
        const result = await recommendMergeAuthor(preservedAuthorIds);
        setAuthors(result.authors as AuthorDetail[]);
        setRecommendedKeepId(result.recommended_keep_id as string | null);
        setSelectedKeepId(result.recommended_keep_id as string | null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load author details",
        );
      } finally {
        setIsLoading(false);
      }
    };

    if (preservedAuthorIds.length >= 2) {
      void fetchRecommendation();
    }
  }, [preservedAuthorIds]);

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
      await mergeAuthors(preservedAuthorIds, selectedKeepId);
      const keepAuthor = authors.find((a) => a.id === selectedKeepId);
      const authorName = keepAuthor?.name || "authors";
      showSuccess(`Successfully merged authors into "${authorName}"`);
      clearSelection();

      // Invalidate authors queries to refresh the grid
      await queryClient.invalidateQueries({ queryKey: ["authors"] });
      await queryClient.invalidateQueries({ queryKey: ["authors-infinite"] });

      onClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to merge authors";
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

    const keepAuthor = authors.find((a) => a.id === selectedKeepId);
    const mergeAuthors = authors.filter((a) => a.id !== selectedKeepId);

    if (!keepAuthor) {
      return [];
    }

    const steps: Array<{ type: string; description: string }> = [];
    let totalBooks = keepAuthor.book_count;

    // Step 1: Identify keep author
    steps.push({
      type: "keep",
      description: `Keep "${keepAuthor.name}" (${keepAuthor.book_count} book${keepAuthor.book_count !== 1 ? "s" : ""})`,
    });

    // Steps for each author to merge
    mergeAuthors.forEach((mergeAuthor) => {
      const counts = mergeAuthor.relationship_counts;
      const relationshipDetails: Array<{ label: string; count: number }> = [];

      // Collect all relationship types with their counts
      if (counts) {
        if (counts.alternate_names > 0) {
          relationshipDetails.push({
            label: "alternate name",
            count: counts.alternate_names,
          });
        }
        if (counts.remote_ids > 0) {
          relationshipDetails.push({
            label: "remote ID",
            count: counts.remote_ids,
          });
        }
        if (counts.photos > 0) {
          relationshipDetails.push({
            label: "photo",
            count: counts.photos,
          });
        }
        if (counts.links > 0) {
          relationshipDetails.push({
            label: "link",
            count: counts.links,
          });
        }
        if (counts.works > 0) {
          relationshipDetails.push({
            label: "work",
            count: counts.works,
          });
        }
        if (counts.work_subjects > 0) {
          relationshipDetails.push({
            label: "work subject",
            count: counts.work_subjects,
          });
        }
        if (counts.similarities > 0) {
          relationshipDetails.push({
            label: "similarity",
            count: counts.similarities,
          });
        }
        if (counts.user_metadata > 0) {
          relationshipDetails.push({
            label: "user metadata",
            count: counts.user_metadata,
          });
        }
        if (counts.user_photos > 0) {
          relationshipDetails.push({
            label: "user photo",
            count: counts.user_photos,
          });
        }
      }

      if (mergeAuthor.book_count === 0) {
        // Author with zero books
        // Add relationship deletion steps first (they're deleted via cascade when author is deleted)
        if (relationshipDetails.length > 0) {
          relationshipDetails.forEach((rel) => {
            steps.push({
              type: "delete_relationship",
              description: `Delete ${rel.count} ${rel.label}${rel.count !== 1 ? "s" : ""} from "${mergeAuthor.name}" (via cascade)`,
            });
          });
        }
        steps.push({
          type: "delete_zero",
          description: `Delete "${mergeAuthor.name}" (0 books) - relationships deleted via cascade`,
        });
      } else {
        // Author with books - reassign books first
        totalBooks += mergeAuthor.book_count;
        steps.push({
          type: "reassign",
          description: `Reassign ${mergeAuthor.book_count} book${mergeAuthor.book_count !== 1 ? "s" : ""} from "${mergeAuthor.name}" to "${keepAuthor.name}"`,
        });
        // Add relationship deletion steps before author deletion (they're deleted via cascade)
        if (relationshipDetails.length > 0) {
          relationshipDetails.forEach((rel) => {
            steps.push({
              type: "delete_relationship",
              description: `Delete ${rel.count} ${rel.label}${rel.count !== 1 ? "s" : ""} from "${mergeAuthor.name}" (via cascade)`,
            });
          });
        }
        steps.push({
          type: "delete",
          description: `Delete "${mergeAuthor.name}" - relationships deleted via cascade`,
        });
      }
    });

    // Final result
    steps.push({
      type: "result",
      description: `Final result: "${keepAuthor.name}" will have ${totalBooks} book${totalBooks !== 1 ? "s" : ""}`,
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
            Loading author details...
          </div>
        </div>
      </div>
    );
  }

  if (error && authors.length === 0) {
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
            Merge Authors
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
            Select which author to keep. All other authors will be merged into
            the selected one.
          </p>

          {error && (
            <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-3 text-red-500 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-3">
            {authors.map((author) => {
              const isRecommended = author.id === recommendedKeepId;
              const isSelected = author.id === selectedKeepId;

              return (
                <button
                  key={author.id}
                  type="button"
                  className={cn(
                    "flex w-full cursor-pointer items-center gap-4 rounded-md border-2 p-4 text-left transition-colors",
                    isSelected
                      ? "border-primary-a0 bg-primary-a0/10"
                      : "border-surface-a20 hover:border-surface-a30 hover:bg-surface-a10",
                  )}
                  onClick={() => {
                    setSelectedKeepId(author.id);
                    setShowDryRun(false);
                  }}
                >
                  <input
                    type="radio"
                    checked={isSelected}
                    onChange={() => {
                      setSelectedKeepId(author.id);
                      setShowDryRun(false);
                    }}
                    className="h-4 w-4 flex-shrink-0 cursor-pointer"
                    readOnly
                    tabIndex={-1}
                    aria-hidden="true"
                  />
                  {/* Author Photo */}
                  <div className="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-md">
                    {author.photo_url ? (
                      <ImageWithLoading
                        src={author.photo_url}
                        alt={`Photo of ${author.name}`}
                        width={64}
                        height={64}
                        className="h-full w-full object-cover"
                        containerClassName="h-full w-full"
                        unoptimized
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-surface-a20">
                        <i
                          className="pi pi-user text-2xl text-text-a40"
                          aria-hidden="true"
                        />
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="m-0 font-medium text-[var(--color-text-a0)] text-base">
                        {author.name}
                      </h3>
                      {isRecommended && (
                        <span className="rounded-full bg-primary-a0/20 px-2 py-0.5 text-primary-a0 text-xs">
                          Recommended
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-4 text-sm text-text-a30">
                      <span>{author.book_count} books</span>
                      {author.is_verified && (
                        <span className="text-green-500">Verified</span>
                      )}
                      <span>Metadata score: {author.metadata_score}</span>
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
                  } else if (step.type === "reassign") {
                    icon = "pi-arrow-right";
                    textColor = "text-primary-a0";
                  } else if (
                    step.type === "delete" ||
                    step.type === "delete_zero"
                  ) {
                    icon = "pi-trash";
                    textColor = "text-orange-500";
                  } else if (step.type === "delete_relationship") {
                    icon = "pi-minus-circle";
                    textColor = "text-orange-400";
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
            {isMerging ? "Merging..." : "Merge authors"}
          </Button>
        </div>
      </div>
    </div>
  );
}
