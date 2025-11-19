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

import { useEffect } from "react";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useOpenLibrarySettings } from "@/hooks/useOpenLibrarySettings";
import { useTasks } from "@/hooks/useTasks";
import { TaskStatus, TaskType } from "@/types/tasks";

/**
 * OpenLibrary data dump settings component.
 *
 * Manages OpenLibrary data dump configuration for authors and works dumps.
 * Allows users to configure URLs for each dump type (client-side only, no persistence).
 *
 * Follows SOLID principles:
 * - SRP: Delegates business logic to useOpenLibrarySettings hook and field rendering
 * - IOC: Uses dependency injection via hook callbacks and component props
 * - SOC: Separates concerns into hook layer and UI layer
 * - DRY: Reuses form components and centralizes state management
 *
 * Features:
 * - URL input fields for authors and works dumps
 * - Change tracking and form validation
 * - Submit, cancel, and reset to defaults functionality
 */
export function OpenLibrarySettings() {
  const { showSuccess, showDanger } = useGlobalMessages();

  // Check for active download tasks - only poll when there's an active task
  const { tasks: activeDownloadTasks, refresh: refreshTasks } = useTasks({
    taskType: TaskType.OPENLIBRARY_DUMP_DOWNLOAD,
    status: null, // Get all statuses, we'll filter for PENDING/RUNNING
    page: 1,
    pageSize: 100,
    autoRefresh: false, // Disable continuous polling
    enabled: true,
  });

  const hasActiveDownloadTask = activeDownloadTasks.some(
    (task) =>
      task.task_type === TaskType.OPENLIBRARY_DUMP_DOWNLOAD &&
      (task.status === TaskStatus.PENDING ||
        task.status === TaskStatus.RUNNING),
  );

  // Only poll when there's an active task
  useEffect(() => {
    if (!hasActiveDownloadTask) {
      return;
    }

    const interval = setInterval(() => {
      void refreshTasks();
    }, 2000);

    return () => {
      clearInterval(interval);
    };
  }, [hasActiveDownloadTask, refreshTasks]);

  const {
    formData,
    isDownloading,
    error,
    handleFieldChange,
    handleDownload,
    handleResetToDefaults,
  } = useOpenLibrarySettings({
    onDownloadSuccess: () => {
      showSuccess("Download task created. Check Scheduled Tasks for progress.");
      // Refresh task list to catch the newly created task
      void refreshTasks();
    },
    onError: (errorMessage) => {
      showDanger(`Failed to create download task: ${errorMessage}`);
    },
  });

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Authors Dump Configuration */}
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label
                htmlFor="authors_url"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Authors Dump URL
              </label>
              <input
                type="url"
                id="authors_url"
                value={formData.authors_url || ""}
                onChange={(e) =>
                  handleFieldChange("authors_url", e.target.value)
                }
                placeholder="https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              />
              <p className="text-text-a30 text-xs">
                URL for the OpenLibrary authors metadata dump. Leave empty to
                use the default OpenLibrary URL.
              </p>
            </div>
          </div>

          {/* Works Dump Configuration */}
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label
                htmlFor="works_url"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Works Dump URL
              </label>
              <input
                type="url"
                id="works_url"
                value={formData.works_url || ""}
                onChange={(e) => handleFieldChange("works_url", e.target.value)}
                placeholder="https://openlibrary.org/data/ol_dump_works_latest.txt.gz"
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              />
              <p className="text-text-a30 text-xs">
                URL for the OpenLibrary works metadata dump. Leave empty to use
                the default OpenLibrary URL.
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between gap-3 border-surface-a20 border-t pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={handleResetToDefaults}
          >
            Reset to Defaults
          </Button>
          <Button
            type="button"
            variant="success"
            onClick={handleDownload}
            disabled={hasActiveDownloadTask || isDownloading}
            loading={isDownloading}
          >
            {hasActiveDownloadTask ? (
              <>
                <i className="pi pi-spinner animate-spin" aria-hidden="true" />
                <span>Downloading...</span>
              </>
            ) : (
              "Download Files"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
