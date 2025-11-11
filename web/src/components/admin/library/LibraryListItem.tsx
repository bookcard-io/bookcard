/**
 * Library list item component.
 *
 * Renders a single library item with checkbox, info, stats, and actions.
 * Follows SRP by focusing solely on individual library item rendering.
 */

import { cn } from "@/libs/utils";
import type { LibraryStats } from "@/services/libraryStatsService";
import { LibraryStatsPills } from "./LibraryStatsPills";
import type { Library } from "./types";

export interface LibraryListItemProps {
  /** Library data. */
  library: Library;
  /** Library statistics (optional). */
  stats: LibraryStats | null | undefined;
  /** Whether stats are loading. */
  isLoadingStats: boolean | undefined;
  /** Callback when library active state is toggled. */
  onToggle: (library: Library) => void;
  /** Callback when library is deleted. */
  onDelete: (id: number) => void;
  /** ID of library currently being deleted. */
  deletingLibraryId: number | null;
}

/**
 * Library list item component.
 *
 * Renders a single library with its information, stats, and actions.
 *
 * Parameters
 * ----------
 * props : LibraryListItemProps
 *     Component props including library data and callbacks.
 */
export function LibraryListItem({
  library,
  stats,
  isLoadingStats,
  onToggle,
  onDelete,
  deletingLibraryId,
}: LibraryListItemProps) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a10)] p-3">
      <div className="flex flex-1 items-center gap-3">
        <input
          type="checkbox"
          checked={library.is_active}
          onChange={() => onToggle(library)}
          className="h-[18px] w-[18px] cursor-pointer accent-[var(--color-primary-a0)]"
        />
        <div className="flex flex-1 flex-col gap-1">
          <div
            className={cn(
              "font-medium text-sm",
              library.is_active
                ? "text-[var(--color-primary-a0)]"
                : "text-[var(--color-text-a0)]",
            )}
          >
            {library.name}
          </div>
          <div className="break-all text-[var(--color-text-a30)] text-xs">
            {library.calibre_db_path}
          </div>
          {library.updated_at && (
            <div className="text-[11px] text-[var(--color-text-a40)]">
              Last updated: {new Date(library.updated_at).toLocaleString()}
            </div>
          )}
        </div>
      </div>
      {stats && <LibraryStatsPills stats={stats} />}
      {isLoadingStats === true && (
        <div className="text-[var(--color-text-a30)] text-xs">
          Loading stats...
        </div>
      )}
      <button
        type="button"
        onClick={() => onDelete(library.id)}
        disabled={deletingLibraryId === library.id}
        className={cn(
          "cursor-pointer rounded-md border border-[var(--color-danger-a20)] bg-transparent px-3 py-1.5 font-medium text-[var(--color-danger-a0)] text-xs transition-colors duration-150",
          deletingLibraryId === library.id
            ? "cursor-not-allowed border-[var(--color-danger-a30)] text-[var(--color-danger-a30)] opacity-60"
            : "hover:bg-[var(--color-danger-a20)] hover:text-[var(--color-danger-a0)]",
        )}
      >
        Remove
      </button>
    </div>
  );
}
