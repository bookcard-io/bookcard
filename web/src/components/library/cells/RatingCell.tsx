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

import { RatingStars } from "@/components/forms/RatingStars";
import type { Book } from "@/types/book";

export interface RatingCellProps {
  /** Book data. */
  book: Book;
  /** Callback when rating changes (optional, enables interactive mode). */
  onRatingChange?: (bookId: number, rating: number | null) => void;
}

/**
 * Rating cell component for displaying book rating.
 *
 * Renders interactive or read-only rating stars based on props.
 * Follows SRP by handling only rating display logic.
 * Follows IOC by accepting callback via props.
 *
 * Parameters
 * ----------
 * props : RatingCellProps
 *     Component props including book and optional rating change callback.
 */
export function RatingCell({ book, onRatingChange }: RatingCellProps) {
  if (onRatingChange) {
    // Interactive rating stars
    return (
      <RatingStars
        value={book.rating ?? null}
        interactive
        onStarClick={(rating) => {
          // Toggle: clicking the same rating clears it
          const newRating = book.rating === rating ? null : rating;
          onRatingChange(book.id, newRating);
        }}
        size="small"
      />
    );
  }

  // Non-interactive display (fallback)
  if (book.rating === null || book.rating === undefined) {
    return <span className="text-text-a40">—</span>;
  }

  const rating = book.rating;
  return (
    <div className="flex items-center gap-1">
      <div className="flex">
        {Array.from({ length: 5 }, (_, i) => i).map((starIndex) => (
          <i
            key={`star-${starIndex}`}
            className={`pi ${
              starIndex < rating ? "pi-star-fill" : "pi-star"
            } text-warning-a0 text-xs`}
            aria-hidden="true"
          />
        ))}
      </div>
    </div>
  );
}
