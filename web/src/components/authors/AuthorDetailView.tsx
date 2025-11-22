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

import { useCallback, useRef, useState } from "react";
import { BookEditModal } from "@/components/books/BookEditModal";
import { BookViewModal } from "@/components/books/BookViewModal";
import { useBookEditModal } from "@/hooks/useBookEditModal";
import { useBookViewModal } from "@/hooks/useBookViewModal";
import type { AuthorWithMetadata } from "@/types/author";
import type { Book } from "@/types/book";
import { AuthorCollaborations } from "./AuthorCollaborations";
import { AuthorHeader } from "./AuthorHeader";
import { AuthorLibraryBooks } from "./AuthorLibraryBooks";
import { AuthorSimilarAuthors } from "./AuthorSimilarAuthors";

export interface AuthorDetailViewProps {
  /** Author data to display. */
  author: AuthorWithMetadata;
  /** Callback when back button is clicked. */
  onBack?: () => void;
  /** Callback to refetch author data. */
  onRefetch?: () => void;
  /** Callback to update author object in place. */
  onAuthorUpdate?: (updatedAuthor: AuthorWithMetadata) => void;
}

/**
 * Author detail view component.
 *
 * Displays comprehensive author information in a full-page layout.
 * Similar to Plex artist page with header section, library books,
 * collaborations, and similar authors.
 * Follows SRP by delegating to specialized components.
 *
 * Parameters
 * ----------
 * props : AuthorDetailViewProps
 *     Component props including author data and callbacks.
 */
export function AuthorDetailView({
  author,
  onBack,
  onAuthorUpdate,
}: AuthorDetailViewProps) {
  const [showFullBio, setShowFullBio] = useState(false);

  // Book data update ref for updating grid when books are edited
  const bookDataUpdateRef = useRef<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
    addBook?: (bookId: number) => Promise<void>;
  } | null>(null);

  // Store book navigation data from BooksGrid (for modal navigation)
  const [booksNavigationData, setBooksNavigationData] = useState<{
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  }>({
    bookIds: [],
    isLoading: false,
  });

  // Book view modal state with book IDs for navigation
  const bookModal = useBookViewModal({
    bookIds: booksNavigationData.bookIds,
    loadMore: booksNavigationData.loadMore,
    hasMore: booksNavigationData.hasMore,
    isLoading: booksNavigationData.isLoading,
  });

  // Book edit modal state
  const bookEditModal = useBookEditModal();

  const handleToggleBio = useCallback(() => {
    setShowFullBio((prev) => !prev);
  }, []);

  const handleBookClick = useCallback(
    (book: Book) => {
      bookModal.handleBookClick(book);
    },
    [bookModal],
  );

  const handleBookEdit = useCallback(
    (bookId: number) => {
      bookEditModal.handleEditBook(bookId);
    },
    [bookEditModal],
  );

  return (
    <div className="flex min-h-full flex-col overflow-y-auto">
      <div className="flex-1 px-8 pt-6 pb-8">
        <AuthorHeader
          author={author}
          showFullBio={showFullBio}
          onToggleBio={handleToggleBio}
          onBack={onBack}
          onAuthorUpdate={onAuthorUpdate}
        />

        {/* Library Books Section */}
        <div className="mt-8">
          <AuthorLibraryBooks
            author={author}
            onBookClick={handleBookClick}
            onBookEdit={handleBookEdit}
            bookDataUpdateRef={bookDataUpdateRef}
            onBooksDataChange={setBooksNavigationData}
          />
        </div>

        {/* Collaborations Section (optional) */}
        {author.collaborations && author.collaborations.length > 0 && (
          <div className="mt-8">
            <AuthorCollaborations
              author={author}
              collaborationBooks={author.collaborations}
              onBookClick={handleBookClick}
              onBookEdit={handleBookEdit}
              bookDataUpdateRef={bookDataUpdateRef}
            />
          </div>
        )}

        {/* Similar Authors Section */}
        <div className="mt-8">
          <AuthorSimilarAuthors
            author={author}
            similarAuthors={author.similar_authors}
          />
        </div>
      </div>

      {/* Book View Modal */}
      <BookViewModal
        bookId={bookModal.viewingBookId}
        onClose={bookModal.handleCloseModal}
        onNavigatePrevious={bookModal.handleNavigatePrevious}
        onNavigateNext={bookModal.handleNavigateNext}
        onEdit={bookEditModal.handleEditBook}
        onBookDeleted={(bookId) => {
          bookDataUpdateRef.current?.removeBook?.(bookId);
        }}
      />

      {/* Book Edit Modal */}
      {bookEditModal.editingBookId !== null && (
        <BookEditModal
          bookId={bookEditModal.editingBookId}
          onClose={bookEditModal.handleCloseModal}
          onCoverSaved={(bookId) => {
            bookDataUpdateRef.current?.updateCover(bookId);
          }}
          onBookSaved={(book) => {
            bookDataUpdateRef.current?.updateBook(book.id, {
              title: book.title,
              authors: book.authors,
              thumbnail_url: book.thumbnail_url,
            });
          }}
        />
      )}
    </div>
  );
}
