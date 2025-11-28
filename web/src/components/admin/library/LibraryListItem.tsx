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
 * Library list item component.
 *
 * Renders a single library item with checkbox, info, stats, and actions.
 * Follows SRP by focusing solely on individual library item rendering.
 */

import { Button } from "@/components/forms/Button";
import { EditableTextField } from "@/components/profile/EditableNameField";
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
  /** Callback when library scan is initiated. */
  onScan: (libraryId: number) => void;
  /** ID of library currently being scanned. */
  scanningLibraryId: number | null;
  /** Callback when library is updated. */
  onUpdate: (libraryId: number, updates: { name?: string }) => Promise<void>;
  /** Whether there is an active scan task for this library. */
  hasActiveScan: boolean;
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
  onScan,
  scanningLibraryId,
  onUpdate,
  hasActiveScan,
}: LibraryListItemProps) {
  const isScanning = scanningLibraryId === library.id || hasActiveScan;

  const handleNameSave = async (name: string) => {
    await onUpdate(library.id, { name: name.trim() || library.name });
  };

  return (
    <div className="flex items-center gap-3 rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a10)] p-3">
      <div className="flex min-w-[250px] flex-1 items-center gap-3">
        <input
          type="checkbox"
          checked={library.is_active}
          onChange={() => onToggle(library)}
          className="h-[18px] w-[18px] cursor-pointer accent-[var(--color-primary-a0)]"
        />
        <div className="flex flex-1 flex-col gap-1">
          <div className="font-medium text-sm">
            <EditableTextField
              currentValue={library.name}
              onSave={handleNameSave}
              placeholder="Enter library name"
              editLabel="Edit library name"
              allowEmpty={false}
            />
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
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="success"
          size="small"
          onClick={() => onScan(library.id)}
          disabled={isScanning || deletingLibraryId === library.id}
          loading={isScanning}
        >
          {hasActiveScan ? (
            <i className="pi pi-spinner animate-spin" aria-hidden="true" />
          ) : (
            <i className="pi pi-sync" aria-hidden="true" />
          )}
          Scan
        </Button>
        <Button
          type="button"
          variant="danger"
          size="small"
          onClick={() => onDelete(library.id)}
          disabled={deletingLibraryId === library.id || isScanning}
          className="bg-[var(--color-danger-a-1)] text-[var(--color-white)] hover:bg-[var(--color-danger-a0)]"
        >
          <i className="pi pi-trash" aria-hidden="true" />
          Remove
        </Button>
      </div>
    </div>
  );
}
