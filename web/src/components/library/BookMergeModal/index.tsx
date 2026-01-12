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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BookCard } from "@/components/library/BookMergeModal/BookCard";
import { DryRunDisplay } from "@/components/library/BookMergeModal/DryRunDisplay";
import { ErrorBanner } from "@/components/library/BookMergeModal/ErrorBanner";
import { ErrorState } from "@/components/library/BookMergeModal/ErrorState";
import { LoadingState } from "@/components/library/BookMergeModal/LoadingState";
import { ModalContainer } from "@/components/library/BookMergeModal/ModalContainer";
import { ModalFooter } from "@/components/library/BookMergeModal/ModalFooter";
import { ModalHeader } from "@/components/library/BookMergeModal/ModalHeader";
import { useBookMerge } from "@/hooks/useBookMerge";
import { useBookMergeAction } from "@/hooks/useBookMergeAction";
import { DryRunCalculator } from "@/utils/dryRunCalculator";

export interface BookMergeModalProps {
  /** List of book IDs to merge. */
  bookIds: number[];
  /** Callback when modal should be closed. */
  onClose: () => void;
}

export function BookMergeModal({ bookIds, onClose }: BookMergeModalProps) {
  const [preservedBookIds] = useState<number[]>(bookIds);
  const [showDryRun, setShowDryRun] = useState(false);
  const dryRunRef = useRef<HTMLDivElement>(null);

  const {
    books,
    recommendedKeepId,
    selectedKeepId,
    setSelectedKeepId,
    isLoading,
    error: fetchError,
  } = useBookMerge(preservedBookIds);

  const { executeMerge, isMerging, error: mergeError } = useBookMergeAction();

  const error = fetchError || mergeError;

  const dryRunSteps = useMemo(() => {
    if (!selectedKeepId) return [];
    return new DryRunCalculator(books, selectedKeepId).calculate();
  }, [books, selectedKeepId]);

  // Scroll to dry run section when it becomes visible
  useEffect(() => {
    if (showDryRun && dryRunRef.current) {
      setTimeout(() => {
        dryRunRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }, 100);
    }
  }, [showDryRun]);

  const handleSelect = useCallback(
    (id: number) => {
      setSelectedKeepId(id);
      setShowDryRun(false);
    },
    [setSelectedKeepId],
  );

  const handleDryRun = useCallback(() => {
    setShowDryRun(true);
  }, []);

  const handleMerge = useCallback(async () => {
    if (!selectedKeepId) return;

    const success = await executeMerge(preservedBookIds, selectedKeepId, books);
    if (success) onClose();
  }, [selectedKeepId, preservedBookIds, books, executeMerge, onClose]);

  if (isLoading) {
    return (
      <ModalContainer onClose={onClose}>
        <LoadingState />
      </ModalContainer>
    );
  }

  if (error && books.length === 0) {
    return (
      <ModalContainer onClose={onClose}>
        <ErrorState error={error} onClose={onClose} />
      </ModalContainer>
    );
  }

  return (
    <ModalContainer onClose={onClose}>
      <ModalHeader onClose={onClose} />

      <div className="flex-1 overflow-y-auto p-6">
        <p className="mb-4 text-sm text-text-a30">
          Select which book to keep. All other books will be merged into the
          selected one.
        </p>

        {error && <ErrorBanner error={error} />}

        <div className="space-y-3">
          {books.map((book) => (
            <BookCard
              key={book.id}
              book={book}
              isRecommended={book.id === recommendedKeepId}
              isSelected={book.id === selectedKeepId}
              onSelect={handleSelect}
            />
          ))}
        </div>

        {showDryRun && dryRunSteps.length > 0 && (
          <DryRunDisplay steps={dryRunSteps} scrollRef={dryRunRef} />
        )}
      </div>

      <ModalFooter
        onCancel={onClose}
        onDryRun={handleDryRun}
        onMerge={handleMerge}
        disabled={!selectedKeepId}
        isMerging={isMerging}
      />
    </ModalContainer>
  );
}
