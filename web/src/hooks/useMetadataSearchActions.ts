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
