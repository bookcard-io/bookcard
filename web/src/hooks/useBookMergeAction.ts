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

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import {
  type BookMergeRecommendation,
  mergeBooks,
} from "@/services/bookService";

type BookDetail = BookMergeRecommendation["books"][0];

export function useBookMergeAction() {
  const queryClient = useQueryClient();
  const { showSuccess, showDanger } = useGlobalMessages();
  const [isMerging, setIsMerging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeMerge = async (
    bookIds: number[],
    keepId: number,
    books: BookDetail[],
  ) => {
    setIsMerging(true);
    setError(null);

    try {
      await mergeBooks(bookIds, keepId);
      const keepBook = books.find((b) => b.id === keepId);
      const bookTitle = keepBook?.title || "books";
      showSuccess(`Successfully merged books into "${bookTitle}"`);

      await queryClient.invalidateQueries({ queryKey: ["books"] });
      await queryClient.invalidateQueries({ queryKey: ["books-infinite"] });

      return true;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to merge books";
      setError(errorMessage);
      showDanger(errorMessage);
      return false;
    } finally {
      setIsMerging(false);
    }
  };

  return { executeMerge, isMerging, error };
}
