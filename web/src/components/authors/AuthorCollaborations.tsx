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

import { BooksGrid } from "@/components/library/BooksGrid";
import type { AuthorWithMetadata } from "@/types/author";
import type { Book } from "@/types/book";

export interface AuthorCollaborationsProps {
  /** Author data. */
  author: AuthorWithMetadata;
  /** List of collaboration books (books with multiple authors including this one). */
  collaborationBooks?: Array<{
    id: number;
    title: string;
    authors: string[];
    thumbnail_url?: string | null;
  }>;
  /** Callback when a book is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback when a book edit button is clicked. */
  onBookEdit?: (bookId: number) => void;
}

/**
 * Author collaborations section component.
 *
 * Displays books where the author collaborated with other authors.
 * Optional section - only shows if collaboration books exist.
 * Follows SRP by focusing solely on collaboration books presentation.
 *
 * Parameters
 * ----------
 * props : AuthorCollaborationsProps
 *     Component props including author data and collaboration books.
 */
export function AuthorCollaborations({
  author,
  collaborationBooks,
  onBookClick,
  onBookEdit,
}: AuthorCollaborationsProps) {
  // Don't render if no collaboration books
  if (!collaborationBooks || collaborationBooks.length === 0) {
    return null;
  }

  const handleBooksDataChange = () => {
    // No-op for now
  };

  // For now, use search query to find collaboration books
  // In the future, this could use a specific API endpoint
  // that finds books with multiple authors including this one
  return (
    <div className="flex flex-col gap-4">
      <h2 className="m-0 font-bold text-[var(--color-text-a0)] text-xl">
        Collaborations
      </h2>
      <div className="-mx-8">
        <BooksGrid
          searchQuery={author.name}
          onBookClick={onBookClick}
          onBookEdit={onBookEdit}
          onBooksDataChange={handleBooksDataChange}
          sortBy="title"
          sortOrder="asc"
          hideStatusHeader={true}
          hideLoadMoreMessage={true}
        />
      </div>
    </div>
  );
}
