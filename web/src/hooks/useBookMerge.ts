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

import { useEffect, useState } from "react";
import {
  type BookMergeRecommendation,
  recommendMergeBooks,
} from "@/services/bookService";

export type BookDetail = BookMergeRecommendation["books"][0];

export function useBookMerge(bookIds: number[]) {
  const [books, setBooks] = useState<BookDetail[]>([]);
  const [recommendedKeepId, setRecommendedKeepId] = useState<number | null>(
    null,
  );
  const [selectedKeepId, setSelectedKeepId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendation = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await recommendMergeBooks(bookIds);
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

    if (bookIds.length >= 2) {
      void fetchRecommendation();
    }
  }, [bookIds]);

  return {
    books,
    recommendedKeepId,
    selectedKeepId,
    setSelectedKeepId,
    isLoading,
    error,
  };
}
