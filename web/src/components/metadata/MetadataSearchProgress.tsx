"use client";

import { useEffect, useState } from "react";
import type { SearchState } from "@/hooks/useMetadataSearchStream";

export interface MetadataSearchProgressProps {
  /** Current search state. */
  state: SearchState;
}

/**
 * Component for displaying overall metadata search progress.
 *
 * Follows SRP by focusing solely on aggregate progress visualization.
 */
export function MetadataSearchProgress({ state }: MetadataSearchProgressProps) {
  const { totalProviders, providersCompleted, providersFailed, totalResults } =
    state;
  const isSearching = state.isSearching;

  // Default to expanded when searching, collapsed when complete
  const [isExpanded, setIsExpanded] = useState(isSearching);

  // Update expanded state based on search status
  useEffect(() => {
    if (isSearching) {
      setIsExpanded(true);
    } else {
      // Collapse when search completes
      const allComplete =
        state.totalProviders > 0 &&
        state.providersCompleted + state.providersFailed ===
          state.totalProviders;
      if (allComplete) {
        setIsExpanded(false);
      }
    }
  }, [
    isSearching,
    state.totalProviders,
    state.providersCompleted,
    state.providersFailed,
  ]);

  if (totalProviders === 0) {
    return null;
  }

  const providersInProgress =
    totalProviders - providersCompleted - providersFailed;
  const progressPercentage =
    totalProviders > 0
      ? ((providersCompleted + providersFailed) / totalProviders) * 100
      : 0;

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-surface-a20 bg-surface-tonal-a0 p-3">
      <button
        type="button"
        className="flex cursor-pointer items-center justify-between gap-2 border-0 bg-transparent p-0 transition-opacity duration-200 hover:opacity-80 focus:rounded focus:outline-none focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls="search-progress-content"
      >
        <div className="flex items-center gap-2">
          <h3 className="m-0 font-semibold text-[0.9rem] text-text-a0">
            Search Progress
          </h3>
          <div className="text-[0.7rem] text-text-a30">
            {providersCompleted + providersFailed} / {totalProviders} providers
          </div>
        </div>
        <span
          className={`pi flex-shrink-0 text-sm text-text-a30 transition-transform duration-200 ${isExpanded ? "pi-chevron-up" : "pi-chevron-down"}`}
          aria-hidden="true"
        />
      </button>

      {isExpanded && (
        <div id="search-progress-content" className="flex flex-col gap-2">
          <div className="h-2 w-full overflow-hidden rounded bg-surface-a20">
            <div
              className="h-full rounded bg-primary-a0 transition-[width] duration-300 ease-in-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>

          <div className="flex flex-wrap gap-3 text-[0.72rem]">
            <div className="flex items-center gap-2">
              <span className="text-text-a30">Completed:</span>
              <span className="font-semibold text-text-a0">
                {providersCompleted}
              </span>
            </div>
            {providersInProgress > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-text-a30">In Progress:</span>
                <span className="font-semibold text-text-a0">
                  {providersInProgress}
                </span>
              </div>
            )}
            {providersFailed > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-text-a30">Failed:</span>
                <span className="font-semibold text-danger-a10">
                  {providersFailed}
                </span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <span className="text-text-a30">Total Results:</span>
              <span className="font-semibold text-text-a0">{totalResults}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
