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

import { useCallback, useMemo, useState } from "react";
import type { SearchResultRead } from "@/types/pvrSearch";

export type SortDirection = "asc" | "desc";

export function useTableSort(results: SearchResultRead[]) {
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: SortDirection;
  } | null>(null);

  const handleSort = useCallback((key: string) => {
    setSortConfig((prev) => {
      let direction: SortDirection = "asc";
      if (prev && prev.key === key && prev.direction === "asc") {
        direction = "desc";
      }
      return { key, direction };
    });
  }, []);

  const sortedResults = useMemo(() => {
    const data = [...results];
    if (!sortConfig) return data;

    return data.sort((a, b) => {
      let aValue: string | number;
      let bValue: string | number;

      switch (sortConfig.key) {
        case "age":
          aValue = a.release.publish_date
            ? new Date(a.release.publish_date).getTime()
            : 0;
          bValue = b.release.publish_date
            ? new Date(b.release.publish_date).getTime()
            : 0;
          break;
        case "title":
          aValue = a.release.title;
          bValue = b.release.title;
          break;
        case "indexer":
          aValue = a.indexer_name ?? "";
          bValue = b.indexer_name ?? "";
          break;
        case "size":
          aValue = a.release.size_bytes ?? 0;
          bValue = b.release.size_bytes ?? 0;
          break;
        case "peers":
          aValue = a.release.seeders ?? 0;
          bValue = b.release.seeders ?? 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) {
        return sortConfig.direction === "asc" ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === "asc" ? 1 : -1;
      }
      return 0;
    });
  }, [results, sortConfig]);

  return { sortedResults, sortConfig, handleSort };
}
