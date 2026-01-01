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

import { useEffect, useState } from "react";
import { trackedBookService } from "@/services/trackedBookService";
import type { TrackedBook } from "@/types/trackedBook";

export function useTrackedBook(bookId: string) {
  const [book, setBook] = useState<TrackedBook | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchBook() {
      if (!bookId) return;

      try {
        setIsLoading(true);
        const data = await trackedBookService.get(bookId);
        if (isMounted) setBook(data);
      } catch (err) {
        if (isMounted) setError("Failed to load book details");
        console.error(err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    void fetchBook();

    return () => {
      isMounted = false;
    };
  }, [bookId]);

  return { book, isLoading, error };
}
