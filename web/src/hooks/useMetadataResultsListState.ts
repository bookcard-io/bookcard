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

import { useCallback, useState } from "react";

export interface UseMetadataResultsListStateResult {
  /** Currently expanded item key, or null if none. */
  expandedKey: string | null;
  /** Set of keys for items that have been collapsed. */
  collapsedKeys: Set<string>;
  /** Handle expand/collapse toggle for an item. */
  handleExpand: (key: string) => void;
  /** Check if an item is expanded. */
  isExpanded: (key: string) => boolean;
  /** Check if an item should be dimmed. */
  isDimmed: (key: string) => boolean;
}

/**
 * Hook for managing metadata results list state.
 *
 * Handles expanded state, collapsed tracking, and dimming logic.
 * Follows SRP by focusing solely on list state management.
 * Follows IOC by providing callbacks for state changes.
 *
 * Returns
 * -------
 * UseMetadataResultsListStateResult
 *     List state and manipulation functions.
 */
export function useMetadataResultsListState(): UseMetadataResultsListStateResult {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [collapsedKeys, setCollapsedKeys] = useState<Set<string>>(new Set());

  const handleExpand = useCallback((key: string) => {
    setExpandedKey((prev) => {
      // If collapsing (prev was a key and now setting to null), mark this item as collapsed
      if (prev !== null && prev === key) {
        setCollapsedKeys((prevCollapsed) => new Set(prevCollapsed).add(key));
        return null;
      }
      // If expanding, remove from collapsed list
      if (prev !== key) {
        setCollapsedKeys((prevCollapsed) => {
          const newSet = new Set(prevCollapsed);
          newSet.delete(key);
          return newSet;
        });
      }
      return prev === key ? null : key;
    });
  }, []);

  const isExpanded = useCallback(
    (key: string) => expandedKey === key,
    [expandedKey],
  );

  const isDimmed = useCallback(
    (key: string) => collapsedKeys.has(key),
    [collapsedKeys],
  );

  return {
    expandedKey,
    collapsedKeys,
    handleExpand,
    isExpanded,
    isDimmed,
  };
}
