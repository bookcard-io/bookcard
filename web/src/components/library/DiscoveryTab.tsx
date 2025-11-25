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
import { BookEditModal } from "@/components/books/BookEditModal";
import { BookViewModal } from "@/components/books/BookViewModal";
import { DiscoverSection } from "@/components/library/discovery/DiscoverSection";
import { MoreByAuthorSection } from "@/components/library/discovery/MoreByAuthorSection";
import { MoreInGenreSection } from "@/components/library/discovery/MoreInGenreSection";
import { OnThisDaySection } from "@/components/library/discovery/OnThisDaySection";
import { RecentlyAddedSection } from "@/components/library/discovery/RecentlyAddedSection";
import { RecentlyReadSection } from "@/components/library/discovery/RecentlyReadSection";
import { RecentShelvesSection } from "@/components/library/discovery/RecentShelvesSection";
import type { Book } from "@/types/book";

export interface DiscoveryTabProps {
  /** Callback when book is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback when book edit is requested. */
  onBookEdit?: (bookId: number) => void;
  /** Callback when book is deleted. */
  onBookDeleted?: (bookId: number) => void;
}

/**
 * Discovery tab component.
 *
 * Displays personalized book recommendations and library insights.
 * Follows SRP by delegating to specialized section components.
 * Uses IOC via component composition.
 */
export function DiscoveryTab({
  onBookClick,
  onBookEdit,
  onBookDeleted,
}: DiscoveryTabProps) {
  const [viewingBookId, setViewingBookId] = useState<number | null>(null);
  const [editingBookId, setEditingBookId] = useState<number | null>(null);
  const [bookNavigationData, setBookNavigationData] = useState<{
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  } | null>(null);

  const handleBookClick = useCallback(
    (book: Book) => {
      setViewingBookId(book.id);
      onBookClick?.(book);
    },
    [onBookClick],
  );

  const handleBookEdit = useCallback(
    (bookId: number) => {
      setEditingBookId(bookId);
      setViewingBookId(null);
      onBookEdit?.(bookId);
    },
    [onBookEdit],
  );

  const handleCloseModal = useCallback(() => {
    setViewingBookId(null);
  }, []);

  const handleCloseEditModal = useCallback(() => {
    setEditingBookId(null);
  }, []);

  const handleNavigatePrevious = useCallback(() => {
    if (
      !bookNavigationData?.bookIds ||
      bookNavigationData.bookIds.length === 0 ||
      !viewingBookId
    ) {
      return;
    }
    const currentIndex = bookNavigationData.bookIds.indexOf(viewingBookId);
    if (currentIndex > 0) {
      const prevId = bookNavigationData.bookIds[currentIndex - 1];
      if (prevId !== undefined) {
        setViewingBookId(prevId);
      }
    }
  }, [viewingBookId, bookNavigationData]);

  const handleNavigateNext = useCallback(() => {
    if (
      !bookNavigationData?.bookIds ||
      bookNavigationData.bookIds.length === 0 ||
      !viewingBookId
    ) {
      return;
    }
    const currentIndex = bookNavigationData.bookIds.indexOf(viewingBookId);
    if (currentIndex < bookNavigationData.bookIds.length - 1) {
      const nextId = bookNavigationData.bookIds[currentIndex + 1];
      if (nextId !== undefined) {
        setViewingBookId(nextId);
      }
    } else if (bookNavigationData.hasMore && bookNavigationData.loadMore) {
      bookNavigationData.loadMore();
      // Note: We'll update viewingBookId after loadMore completes
      // This is a simplified version - in production you'd want to track loading state
    }
  }, [viewingBookId, bookNavigationData]);

  return (
    <>
      <div className="flex flex-col gap-8 px-8 pt-2 pb-6">
        <RecentlyReadSection
          onBookClick={handleBookClick}
          onBookEdit={handleBookEdit}
          onBooksDataChange={setBookNavigationData}
        />
        <RecentlyAddedSection
          onBookClick={handleBookClick}
          onBookEdit={handleBookEdit}
          onBooksDataChange={setBookNavigationData}
        />
        <RecentShelvesSection />
        <OnThisDaySection
          onBookClick={handleBookClick}
          onBookEdit={handleBookEdit}
          onBooksDataChange={setBookNavigationData}
        />
        <MoreByAuthorSection
          onBookClick={handleBookClick}
          onBookEdit={handleBookEdit}
          onBooksDataChange={setBookNavigationData}
        />
        <MoreInGenreSection
          onBookClick={handleBookClick}
          onBookEdit={handleBookEdit}
          onBooksDataChange={setBookNavigationData}
        />
        <DiscoverSection
          onBookClick={handleBookClick}
          onBookEdit={handleBookEdit}
          onBooksDataChange={setBookNavigationData}
        />
      </div>
      <BookViewModal
        bookId={viewingBookId}
        onClose={handleCloseModal}
        onNavigatePrevious={handleNavigatePrevious}
        onNavigateNext={handleNavigateNext}
        onEdit={handleBookEdit}
        onBookDeleted={onBookDeleted}
      />
      {editingBookId !== null && (
        <BookEditModal
          bookId={editingBookId}
          onClose={handleCloseEditModal}
          onBookSaved={() => {
            // Book saved, could refresh data if needed
          }}
        />
      )}
    </>
  );
}
