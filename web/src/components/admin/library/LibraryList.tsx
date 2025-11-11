/**
 * Library list component.
 *
 * Displays a list of libraries with their statistics and actions.
 * Follows SRP by focusing solely on list composition and empty states.
 * Follows IOC by delegating data fetching to hooks and rendering to sub-components.
 */

"use client";

import { useLibraryStats } from "./hooks/useLibraryStats";
import { LibraryListItem } from "./LibraryListItem";
import type { Library } from "./types";

export type { Library };

export interface LibraryListProps {
  /** List of libraries to display. */
  libraries: Library[];
  /** Callback when library active state is toggled. */
  onToggle: (library: Library) => void;
  /** Callback when library is deleted. */
  onDelete: (id: number) => void;
  /** ID of library currently being deleted. */
  deletingLibraryId: number | null;
}

/**
 * Library list component.
 *
 * Renders a list of libraries with their statistics and management actions.
 * Handles empty states and composition of library items.
 *
 * Parameters
 * ----------
 * props : LibraryListProps
 *     Component props including libraries and callbacks.
 */
export function LibraryList({
  libraries,
  onToggle,
  onDelete,
  deletingLibraryId,
}: LibraryListProps) {
  const { stats, loadingStats } = useLibraryStats(libraries);

  return (
    <div className="flex flex-col gap-2">
      {libraries.map((lib) => (
        <LibraryListItem
          key={lib.id}
          library={lib}
          stats={stats[lib.id]}
          isLoadingStats={loadingStats[lib.id]}
          onToggle={onToggle}
          onDelete={onDelete}
          deletingLibraryId={deletingLibraryId}
        />
      ))}
      {libraries.length === 0 && (
        <div className="p-6 text-center text-[var(--color-text-a30)] text-sm italic">
          No libraries configured yet.
        </div>
      )}
      {libraries.length > 0 && !libraries.some((lib) => lib.is_active) && (
        <div className="p-6 text-center text-[var(--color-text-a30)] text-sm italic">
          Please activate a library to begin using the app.
        </div>
      )}
    </div>
  );
}
