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

import { useCallback, useEffect, useState } from "react";
import { pvrSearchService } from "@/services/pvrSearchService";
import type { SearchResultRead } from "@/types/pvrSearch";

export function useSearchResults(trackedBookId: number, isOpen: boolean) {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResultRead[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(
    async (initiate = false) => {
      setIsLoading(true);
      setError(null);
      try {
        if (initiate) {
          await pvrSearchService.search({ tracked_book_id: trackedBookId });
          // Wait a bit for results to populate
          await new Promise((resolve) => setTimeout(resolve, 2000));
        }

        const response = await pvrSearchService.getResults(trackedBookId);
        setResults(response.results);
      } catch (err: unknown) {
        // If we didn't initiate and got 404, it might mean no previous search.
        // If we did initiate and failed, that's an error.
        const errorMessage = err instanceof Error ? err.message : String(err);
        if (!initiate && errorMessage.includes("No results")) {
          // Do nothing or maybe show empty
        } else {
          setError(errorMessage || "Failed to load results");
        }
      } finally {
        setIsLoading(false);
      }
    },
    [trackedBookId],
  );

  useEffect(() => {
    if (isOpen) {
      fetchResults(true);
    }
  }, [isOpen, fetchResults]);

  return { results, isLoading, error, refetch: fetchResults };
}
