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

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
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
  onRefetch,
}: AuthorDetailViewProps) {
  const router = useRouter();
  const [showFullBio, setShowFullBio] = useState(false);

  const handleToggleBio = useCallback(() => {
    setShowFullBio((prev) => !prev);
  }, []);

  const handleBookClick = useCallback(
    (book: Book) => {
      router.push(`/books/${book.id}/view`);
    },
    [router],
  );

  const handleBookEdit = useCallback(
    (bookId: number) => {
      router.push(`/books/${bookId}/edit`);
    },
    [router],
  );

  return (
    <div className="flex min-h-full flex-col overflow-y-auto">
      <div className="flex-1 px-8 pt-6 pb-8">
        <AuthorHeader
          author={author}
          showFullBio={showFullBio}
          onToggleBio={handleToggleBio}
          onBack={onBack}
          onMetadataFetched={onRefetch}
        />

        {/* Library Books Section */}
        <div className="mt-8">
          <AuthorLibraryBooks
            author={author}
            onBookClick={handleBookClick}
            onBookEdit={handleBookEdit}
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
    </div>
  );
}
