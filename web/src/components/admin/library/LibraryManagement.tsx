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

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useTasks } from "@/hooks/useTasks";
import { TaskStatus, TaskType } from "@/types/tasks";
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
  const [newName, setNewName] = useState("");
  const [newPath, setNewPath] = useState("");
  const [newLibraryName, setNewLibraryName] = useState("");

  const {
    libraries,
    isLoading,
    isBusy,
    error,
    deletingLibraryId,
    scanningLibraryId,
    updatingLibraryId,
    addLibrary,
    createLibrary,
    deleteLibrary,
    scanLibrary: originalScanLibrary,
    updateLibrary,
    clearError,
  } = useLibraryManagement({
    onRefresh: refreshActiveLibrary,
  });

  // Check for active library scan tasks - only poll when there's an active task
  const { tasks: activeScanTasks, refresh: refreshScanTasks } = useTasks({
    taskType: TaskType.LIBRARY_SCAN,
    status: null, // Get all statuses, we'll filter for PENDING/RUNNING
    page: 1,
    pageSize: 100,
    autoRefresh: false, // Disable continuous polling
    enabled: true,
  });

  // Wrap scanLibrary to refresh scan tasks after initiating a scan
  const scanLibrary = useCallback(
    async (libraryId: number) => {
      await originalScanLibrary(libraryId);
      // Refresh task list to catch the newly created task
      void refreshScanTasks();
    },
    [originalScanLibrary, refreshScanTasks],
  );

  const hasActiveScanTask = activeScanTasks.some(
    (task) =>
      task.task_type === TaskType.LIBRARY_SCAN &&
      (task.status === TaskStatus.PENDING ||
        task.status === TaskStatus.RUNNING),
  );

  // Only poll when there's an active scan task
  useEffect(() => {
    if (!hasActiveScanTask) {
      return;
    }

    const interval = setInterval(() => {
      void refreshScanTasks();
    }, 2000);

    return () => {
      clearInterval(interval);
    };
  }, [hasActiveScanTask, refreshScanTasks]);

  // Create a map of library_id -> hasActiveScan
  const libraryScanStatusMap = useMemo(() => {
    const map = new Map<number, boolean>();
    activeScanTasks.forEach((task) => {
      if (
        task.task_type === TaskType.LIBRARY_SCAN &&
        (task.status === TaskStatus.PENDING ||
          task.status === TaskStatus.RUNNING) &&
        task.metadata &&
        typeof task.metadata === "object" &&
        "library_id" in task.metadata &&
        typeof task.metadata.library_id === "number"
      ) {
        map.set(task.metadata.library_id, true);
      }
    });
    return map;
  }, [activeScanTasks]);

  const handleCreateNewLibrary = useCallback(async () => {
    try {
      const name = newLibraryName.trim() || "My Library";
      await createLibrary(name);
      setNewLibraryName("");
    } catch {
      // Error is handled by the hook
    }
  }, [newLibraryName, createLibrary]);

  const handleAddExistingLibrary = useCallback(async () => {
    try {
      const name = newName.trim() || "Existing Library";
      await addLibrary(name, newPath);
      setNewName("");
      setNewPath("");
    } catch {
      // Error is handled by the hook
    }
  }, [newName, newPath, addLibrary]);

  const handleNewLibraryNameChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setNewLibraryName(e.target.value);
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

  const handlePathChange = useCallback(
    (value: string) => {
      setNewPath(value);
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

  const hasLibraries = libraries.length > 0;
  const canCreateNew = !isBusy;
  const canAddExisting = newPath.trim().length > 0 && !isBusy;

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      {!hasLibraries ? (
        // Initial setup: Show both options
        <div className="flex flex-col gap-6">
          {/* Create a library section */}
          <div className="flex flex-col gap-3">
            <h2 className="font-semibold text-lg text-text-a0">
              Create a library
            </h2>
            <p className="text-sm text-text-a30">
              New to Calibre? We'll set up a fresh library for you. Just click
              the button below and we'll handle everything.
            </p>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={newLibraryName}
                onChange={handleNewLibraryNameChange}
                placeholder="Library name (optional)"
                className="flex-1 rounded-md border border-[var(--color-surface-a20)] bg-surface-a0 px-3 py-2 text-sm text-text-a0 transition-colors duration-200 focus:border-[var(--color-primary-a0)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-70"
                disabled={isBusy}
              />
              <Button
                variant="success"
                size="small"
                onClick={handleCreateNewLibrary}
                disabled={!canCreateNew}
                loading={isBusy}
              >
                Create library
              </Button>
            </div>
          </div>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-[var(--color-surface-a20)] border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-surface-a0 px-2 text-text-a30">Or</span>
            </div>
          </div>

          {/* Existing library section */}
          <div className="flex flex-col gap-3">
            <h2 className="font-semibold text-lg text-text-a0">
              Existing library
            </h2>
            <p className="text-sm text-text-a30">
              Already have a Calibre library? Connect it by providing the path
              to your library directory.
            </p>
            <div className="flex flex-col gap-3 md:flex-row md:items-end">
              <input
                type="text"
                value={newName}
                onChange={handleNameChange}
                placeholder="Library name (optional)"
                className="flex-1 rounded-md border border-[var(--color-surface-a20)] bg-surface-a0 px-3 py-2 text-sm text-text-a0 transition-colors duration-200 focus:border-[var(--color-primary-a0)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-70"
                disabled={isBusy}
              />
              <div className="min-w-0 flex-1">
                <PathInputWithSuggestions
                  value={newPath}
                  onChange={handlePathChange}
                  onSubmit={handleAddExistingLibrary}
                  busy={isBusy}
                />
              </div>
              <Button
                variant="primary"
                size="small"
                onClick={handleAddExistingLibrary}
                disabled={!canAddExisting}
                loading={isBusy}
                className="md:flex-[0_0_auto]"
              >
                Add library
              </Button>
            </div>
          </div>
        </div>
      ) : (
        // Libraries exist: Show compact add library form
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-lg text-text-a0">
              Your Libraries
            </h2>
            <div className="flex items-center gap-2">
              <Button
                variant="success"
                size="small"
                onClick={handleCreateNewLibrary}
                disabled={!canCreateNew}
                loading={isBusy}
              >
                Create New
              </Button>
            </div>
          </div>

          {/* Quick add existing library */}
          <div className="flex flex-col gap-2 rounded-md border border-[var(--color-surface-a20)] bg-surface-a10 p-4">
            <h3 className="font-medium text-sm text-text-a0">
              Add existing library
            </h3>
            <div className="flex flex-col gap-2 md:flex-row md:items-end">
              <input
                type="text"
                value={newName}
                onChange={handleNameChange}
                placeholder="Library name (optional)"
                className="flex-1 rounded-md border border-[var(--color-surface-a20)] bg-surface-a0 px-3 py-2 text-sm text-text-a0 transition-colors duration-200 focus:border-[var(--color-primary-a0)] focus:outline-none disabled:cursor-not-allowed disabled:opacity-70"
                disabled={isBusy}
              />
              <div className="min-w-0 flex-1">
                <PathInputWithSuggestions
                  value={newPath}
                  onChange={handlePathChange}
                  onSubmit={handleAddExistingLibrary}
                  busy={isBusy}
                />
              </div>
              <Button
                variant="primary"
                size="small"
                onClick={handleAddExistingLibrary}
                disabled={!canAddExisting}
                loading={isBusy}
                className="md:flex-[0_0_auto]"
              >
                Add Library
              </Button>
            </div>
          </div>
        </div>
      )}

      {hasLibraries && (
        <LibraryList
          libraries={libraries}
          onDelete={deleteLibrary}
          deletingLibraryId={deletingLibraryId}
          onScan={scanLibrary}
          scanningLibraryId={scanningLibraryId}
          updatingLibraryId={updatingLibraryId}
          onUpdate={updateLibrary}
          libraryScanStatusMap={libraryScanStatusMap}
        />
      )}
    </div>
  );
}
