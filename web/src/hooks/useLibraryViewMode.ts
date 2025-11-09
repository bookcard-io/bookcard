import { useCallback, useState } from "react";
import type { ViewMode } from "@/components/library/widgets/ViewModeButtons";

export interface UseLibraryViewModeOptions {
  /** Callback for sort toggle (when mode is "sort"). */
  onSortToggle?: () => void;
}

export interface UseLibraryViewModeResult {
  /** Current view mode. */
  viewMode: ViewMode;
  /** Handler for view mode change. */
  handleViewModeChange: (mode: ViewMode) => void;
}

/**
 * Custom hook for managing library view mode state.
 *
 * Manages the current view mode (grid, list, etc.).
 * Follows SRP by managing only view mode state.
 * Follows IOC by accepting optional callbacks for coordination.
 *
 * Parameters
 * ----------
 * options : UseLibraryViewModeOptions
 *     Optional callbacks for coordination with other concerns.
 *
 * Returns
 * -------
 * UseLibraryViewModeResult
 *     View mode state and change handler.
 */
export function useLibraryViewMode(
  options: UseLibraryViewModeOptions = {},
): UseLibraryViewModeResult {
  const { onSortToggle } = options;
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const handleViewModeChange = useCallback(
    (mode: ViewMode) => {
      // The "sort" button is handled by useLibrarySorting
      if (mode === "sort") {
        onSortToggle?.();
      } else {
        setViewMode(mode);
      }
    },
    [onSortToggle],
  );

  return {
    viewMode,
    handleViewModeChange,
  };
}
