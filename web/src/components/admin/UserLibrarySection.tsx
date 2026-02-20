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

"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useUserLibraryManagement } from "@/hooks/useUserLibraryManagement";
import { cn } from "@/libs/utils";

export interface UserLibrarySectionProps {
  /** ID of the user whose library assignments are being managed. */
  userId: number;
}

/**
 * Library access management section for the admin user-edit modal.
 *
 * Displays the user's assigned libraries with controls to toggle
 * visibility, set the active (ingest) library, assign new libraries,
 * and unassign existing ones. Changes are applied immediately via the
 * admin API — no form-level "Save" is required.
 *
 * Parameters
 * ----------
 * props : UserLibrarySectionProps
 *     Component props containing the target user ID.
 */
export function UserLibrarySection({ userId }: UserLibrarySectionProps) {
  const {
    assignments,
    allLibraries,
    isLoading,
    isBusy,
    error,
    assignLibrary,
    unassignLibrary,
    setActiveLibrary,
    toggleVisibility,
    clearError,
  } = useUserLibraryManagement(userId);

  const [selectedLibraryId, setSelectedLibraryId] = useState<string>("");

  const unassignedLibraries = useMemo(() => {
    const assignedIds = new Set(assignments.map((a) => a.library_id));
    return allLibraries.filter((lib) => !assignedIds.has(lib.id));
  }, [allLibraries, assignments]);

  const handleAssign = async () => {
    const libId = Number(selectedLibraryId);
    if (!Number.isFinite(libId)) return;
    await assignLibrary(libId);
    setSelectedLibraryId("");
  };

  if (isLoading) {
    return (
      <div className="text-sm text-text-a30">Loading library access...</div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <h3 className="font-semibold text-sm text-text-a0">Library access</h3>

      {error && (
        <div className="flex items-center justify-between rounded-md bg-[var(--color-danger-a20)] px-3 py-2 text-[var(--color-danger-a0)] text-sm">
          <span>{error}</span>
          <button
            type="button"
            onClick={clearError}
            className="ml-2 text-[var(--color-danger-a0)] hover:opacity-70"
            aria-label="Dismiss error"
          >
            <i className="pi pi-times text-xs" aria-hidden="true" />
          </button>
        </div>
      )}

      {assignments.length === 0 ? (
        <p className="text-sm text-text-a40 italic">
          No libraries assigned to this user.
        </p>
      ) : (
        <div className="flex flex-col overflow-hidden rounded-md border border-surface-a20">
          {/* Header */}
          <div className="grid grid-cols-[2fr_80px_80px_48px] gap-2 bg-surface-a10 px-3 py-2 font-semibold text-text-a40 text-xs">
            <div>Library</div>
            <div className="text-center">Visible</div>
            <div className="text-center">Active</div>
            <div />
          </div>

          {/* Rows */}
          {assignments.map((assignment, idx) => (
            <div
              key={assignment.id}
              className={cn(
                "grid grid-cols-[2fr_80px_80px_48px] items-center gap-2 border-surface-a20 border-t px-3 py-2 text-sm",
                idx % 2 === 0 ? "bg-surface-a20" : "bg-surface-tonal-a20",
              )}
            >
              <div className="truncate text-text-a0">
                {assignment.library_name ?? `Library ${assignment.library_id}`}
              </div>

              {/* Visible toggle */}
              <div className="flex justify-center">
                <button
                  type="button"
                  role="switch"
                  aria-checked={assignment.is_visible}
                  aria-label={`Toggle visibility for ${assignment.library_name}`}
                  disabled={isBusy}
                  onClick={() =>
                    toggleVisibility(
                      assignment.library_id,
                      !assignment.is_visible,
                    )
                  }
                  className={cn(
                    "relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-a0 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50",
                    assignment.is_visible ? "bg-primary-a0" : "bg-surface-a40",
                  )}
                >
                  <span
                    className={cn(
                      "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200",
                      assignment.is_visible ? "translate-x-4" : "translate-x-0",
                    )}
                  />
                </button>
              </div>

              {/* Active radio */}
              <div className="flex justify-center">
                <input
                  type="radio"
                  name={`active-library-${userId}`}
                  checked={assignment.is_active}
                  disabled={isBusy || assignment.is_active}
                  onChange={() => setActiveLibrary(assignment.library_id)}
                  className="h-4 w-4 cursor-pointer accent-[var(--color-primary-a0)] disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label={`Set ${assignment.library_name} as active`}
                />
              </div>

              {/* Remove button */}
              <div className="flex justify-center">
                <Button
                  type="button"
                  variant="danger"
                  size="xsmall"
                  disabled={isBusy}
                  onClick={() => unassignLibrary(assignment.library_id)}
                  aria-label={`Unassign ${assignment.library_name}`}
                  title="Remove library access"
                >
                  <i className="pi pi-times text-xs" aria-hidden="true" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Assign new library */}
      {unassignedLibraries.length > 0 && (
        <div className="flex items-center gap-2">
          <select
            value={selectedLibraryId}
            onChange={(e) => setSelectedLibraryId(e.target.value)}
            disabled={isBusy}
            className="h-8 flex-1 rounded-md border border-surface-a20 bg-surface-a10 px-2 text-sm text-text-a0 focus:border-primary-a0 focus:outline-none focus:ring-1 focus:ring-primary-a0 disabled:opacity-50"
          >
            <option value="">Select a library to assign...</option>
            {unassignedLibraries.map((lib) => (
              <option key={lib.id} value={lib.id}>
                {lib.name}
              </option>
            ))}
          </select>
          <Button
            type="button"
            variant="secondary"
            size="xsmall"
            disabled={isBusy || !selectedLibraryId}
            onClick={handleAssign}
          >
            <i className="pi pi-plus text-xs" aria-hidden="true" />
            Assign
          </Button>
        </div>
      )}
    </div>
  );
}
