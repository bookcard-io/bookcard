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
  /** Callback when library is deleted. */
  onDelete: (id: number) => void;
  /** ID of library currently being deleted. */
  deletingLibraryId: number | null;
  /** Callback when library scan is initiated. */
  onScan: (libraryId: number) => void;
  /** ID of library currently being scanned. */
  scanningLibraryId: number | null;
  /** ID of library currently being updated. */
  updatingLibraryId: number | null;
  /** Callback when library is updated. */
  onUpdate: (
    libraryId: number,
    updates: {
      name?: string;
      auto_convert_on_ingest?: boolean;
      auto_convert_target_format?: string | null;
      auto_convert_ignored_formats?: string | null;
      auto_convert_backup_originals?: boolean;
    },
  ) => Promise<void>;
  /** Map of library_id to whether it has an active scan task. */
  libraryScanStatusMap: Map<number, boolean>;
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
  onDelete,
  deletingLibraryId,
  onScan,
  scanningLibraryId,
  updatingLibraryId,
  onUpdate,
  libraryScanStatusMap,
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
          onDelete={onDelete}
          deletingLibraryId={deletingLibraryId}
          onScan={onScan}
          scanningLibraryId={scanningLibraryId}
          updatingLibraryId={updatingLibraryId}
          onUpdate={onUpdate}
          hasActiveScan={libraryScanStatusMap.get(lib.id) ?? false}
        />
      ))}
      {libraries.length === 0 && (
        <div className="p-6 text-center text-[var(--color-text-a30)] text-sm italic">
          No libraries configured yet.
        </div>
      )}
    </div>
  );
}
