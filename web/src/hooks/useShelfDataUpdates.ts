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
import type { Shelf } from "@/types/shelf";

export interface UseShelfDataUpdatesOptions {
  /** Ref to expose update method externally. */
  updateRef?: React.RefObject<{
    updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
    updateCover: (shelfId: number) => void;
  }>;
}

export interface UseShelfDataUpdatesResult {
  /** Map of shelf ID to updated shelf data. */
  shelfDataOverrides: Map<number, Partial<Shelf>>;
  /** Function to update shelf data for a specific shelf. */
  updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
  /** Function to update cover URL with cache-busting for a specific shelf. */
  updateCover: (shelfId: number) => void;
  /** Function to clear all shelf data overrides. */
  clearOverrides: () => void;
}

/**
 * Custom hook for managing shelf data updates in shelf lists.
 *
 * Tracks shelf data overrides by shelf ID and provides methods to update them.
 * Follows SRP by focusing solely on shelf data override state management.
 * Follows IOC by accepting ref for external access.
 * Follows DRY by centralizing shelf data update logic.
 *
 * Parameters
 * ----------
 * options : UseShelfDataUpdatesOptions
 *     Configuration including optional ref for external access.
 *
 * Returns
 * -------
 * UseShelfDataUpdatesResult
 *     Shelf data overrides map and control functions.
 */
export function useShelfDataUpdates(
  options: UseShelfDataUpdatesOptions = {},
): UseShelfDataUpdatesResult {
  const { updateRef } = options;
  const [shelfDataOverrides, setShelfDataOverrides] = useState<
    Map<number, Partial<Shelf>>
  >(new Map());

  const updateShelf = useCallback(
    (shelfId: number, shelfData: Partial<Shelf>) => {
      setShelfDataOverrides((prev) => {
        const next = new Map(prev);
        // Merge with existing override if present
        const existing = next.get(shelfId);
        next.set(shelfId, { ...existing, ...shelfData });
        return next;
      });
    },
    [],
  );

  const updateCover = useCallback((shelfId: number) => {
    // Force refresh by updating cover_picture with cache-busting timestamp
    // This triggers a re-render and the cache-busting URL will force image reload
    // We use a timestamp to ensure the override is different each time
    const timestamp = Date.now();
    setShelfDataOverrides((prev) => {
      const next = new Map(prev);
      const existing = next.get(shelfId);
      // Toggle or update cover_picture to force refresh
      // If it was truthy, keep it truthy but with new timestamp
      // If it was falsy, keep it falsy
      const currentCover = existing?.cover_picture ?? undefined;
      next.set(shelfId, {
        ...existing,
        cover_picture:
          currentCover !== null && currentCover !== undefined
            ? `refresh-${timestamp}`
            : null,
      });
      return next;
    });
  }, []);

  const clearOverrides = useCallback(() => {
    setShelfDataOverrides(new Map());
  }, []);

  // Expose updateShelf and updateCover methods via ref
  useEffect(() => {
    if (updateRef) {
      updateRef.current = { updateShelf, updateCover };
    }
  }, [updateRef, updateShelf, updateCover]);

  return {
    shelfDataOverrides,
    updateShelf,
    updateCover,
    clearOverrides,
  };
}
