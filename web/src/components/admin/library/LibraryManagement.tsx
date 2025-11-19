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

import { useCallback, useState } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useLibraryManagement } from "./hooks/useLibraryManagement";
import { LibraryList } from "./LibraryList";
import { PathInputWithSuggestions } from "./PathInputWithSuggestions";

/**
 * Library management component.
 *
 * Provides UI for managing libraries (add, toggle, delete).
 * Follows SRP by delegating business logic to hooks.
 * Uses IOC by accepting context dependencies.
 */
export function LibraryManagement() {
  const { refresh: refreshActiveLibrary } = useActiveLibrary();
  const [newPath, setNewPath] = useState("");
  const [newName, setNewName] = useState("");

  const {
    libraries,
    isLoading,
    isBusy,
    error,
    deletingLibraryId,
    scanningLibraryId,
    addLibrary,
    toggleLibrary,
    deleteLibrary,
    scanLibrary,
    clearError,
  } = useLibraryManagement({
    onRefresh: refreshActiveLibrary,
  });

  const handleAdd = useCallback(async () => {
    try {
      await addLibrary(newPath, newName);
      setNewPath("");
      setNewName("");
    } catch {
      // Error is handled by the hook
    }
  }, [newPath, newName, addLibrary]);

  const handlePathChange = useCallback(
    (value: string) => {
      setNewPath(value);
      clearError();
    },
    [clearError],
  );

  const handleNameChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setNewName(e.target.value);
      clearError();
    },
    [clearError],
  );

  if (isLoading) {
    return (
      <div className="py-6 text-center text-sm text-text-a30">
        Loading libraries...
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newName}
            onChange={handleNameChange}
            placeholder="Library name (optional)"
            className="flex-[0_0_250px] rounded-md border border-[var(--color-surface-a20)] bg-surface-a10 px-3 py-2.5 text-sm text-text-a0 transition-colors duration-200 focus:border-[var(--color-primary-a0)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-70"
            disabled={isBusy}
          />
          <PathInputWithSuggestions
            value={newPath}
            onChange={handlePathChange}
            onSubmit={handleAdd}
            busy={isBusy}
          />
          <button
            type="button"
            onClick={handleAdd}
            disabled={!newPath.trim() || isBusy}
            className="flex-[0_0_auto] cursor-pointer rounded-md border-none bg-primary-a0 px-5 py-2.5 font-medium text-sm text-text-a0 transition-colors duration-200 hover:bg-primary-a10 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Add
          </button>
        </div>
      </div>

      <LibraryList
        libraries={libraries}
        onToggle={toggleLibrary}
        onDelete={deleteLibrary}
        deletingLibraryId={deletingLibraryId}
        onScan={scanLibrary}
        scanningLibraryId={scanningLibraryId}
      />
    </div>
  );
}
