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

import { useCallback } from "react";
import type { UseMetadataSearchStreamResult } from "./useMetadataSearchStream";

export interface UseMetadataSearchActionsOptions {
  /** Search stream hook result. */
  searchStream: UseMetadataSearchStreamResult;
  /** Callback to update search query. */
  setSearchQuery: (query: string) => void;
  /** Callback when modal should be closed. */
  onClose: () => void;
}

export interface UseMetadataSearchActionsResult {
  /** Handler for search action. */
  handleSearch: (query: string) => void;
  /** Handler for cancel action. */
  handleCancel: () => void;
  /** Handler for close action. */
  handleClose: () => void;
}

/**
 * Custom hook for metadata search actions.
 *
 * Provides handlers for search operations.
 * Follows SRP by focusing solely on search action logic.
 * Uses IOC via callback dependencies.
 *
 * Parameters
 * ----------
 * options : UseMetadataSearchActionsOptions
 *     Options for search actions.
 *
 * Returns
 * -------
 * UseMetadataSearchActionsResult
 *     Object containing action handlers.
 */
export function useMetadataSearchActions(
  options: UseMetadataSearchActionsOptions,
): UseMetadataSearchActionsResult {
  const { searchStream, setSearchQuery, onClose } = options;
  const { startSearch, cancelSearch, reset } = searchStream;

  const handleSearch = useCallback(
    (query: string) => {
      const trimmedQuery = query.trim();
      if (trimmedQuery) {
        setSearchQuery(trimmedQuery);
        reset();
        // Start search with the new query immediately
        startSearch(trimmedQuery);
      }
    },
    [reset, startSearch, setSearchQuery],
  );

  const handleCancel = useCallback(() => {
    cancelSearch();
  }, [cancelSearch]);

  const handleClose = useCallback(() => {
    cancelSearch();
    onClose();
  }, [cancelSearch, onClose]);

  return {
    handleSearch,
    handleCancel,
    handleClose,
  };
}
