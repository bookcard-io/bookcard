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

import { useEffect, useRef } from "react";
import { Button } from "@/components/forms/Button";
import { useBlurAfterClick } from "@/components/profile/BlurAfterClickContext";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useOpenLibraryDumpConfig } from "@/hooks/useOpenLibraryDumpConfig";
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
  const { onBlurChange } = useBlurAfterClick();
  const {
    config: dumpConfig,
    isLoading: isConfigLoading,
    updateField: updateConfigField,
  } = useOpenLibraryDumpConfig();

  // Check for active download tasks - only poll when there's an active task
  const { tasks: activeDownloadTasks, refresh: refreshDownloadTasks } =
    useTasks({
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

  // Check for active ingest tasks - only poll when there's an active task
  const { tasks: activeIngestTasks, refresh: refreshIngestTasks } = useTasks({
    taskType: TaskType.OPENLIBRARY_DUMP_INGEST,
    status: null, // Get all statuses, we'll filter for PENDING/RUNNING
    page: 1,
    pageSize: 100,
    autoRefresh: false, // Disable continuous polling
    enabled: true,
  });

  const hasActiveIngestTask = activeIngestTasks.some(
    (task) =>
      task.task_type === TaskType.OPENLIBRARY_DUMP_INGEST &&
      (task.status === TaskStatus.PENDING ||
        task.status === TaskStatus.RUNNING),
  );

  // Only poll when there's an active download task
  useEffect(() => {
    if (!hasActiveDownloadTask) {
      return;
    }

    const interval = setInterval(() => {
      void refreshDownloadTasks();
    }, 2000);

    return () => {
      clearInterval(interval);
    };
  }, [hasActiveDownloadTask, refreshDownloadTasks]);

  // Only poll when there's an active ingest task
  useEffect(() => {
    if (!hasActiveIngestTask) {
      return;
    }

    const interval = setInterval(() => {
      void refreshIngestTasks();
    }, 2000);

    return () => {
      clearInterval(interval);
    };
  }, [hasActiveIngestTask, refreshIngestTasks]);

  // Store initial values in ref to prevent remounts on config updates
  // Only initialize once when config first loads (not on every update)
  const initialValuesRef = useRef<{
    urls?: {
      authors_url: string | null;
      works_url: string | null;
      editions_url: string | null;
    };
    flags?: {
      process_authors: boolean;
      process_works: boolean;
      process_editions: boolean;
    };
  }>({});

  // Only set initial values once when config first loads (not on updates)
  if (
    dumpConfig &&
    !isConfigLoading &&
    !initialValuesRef.current.urls &&
    !initialValuesRef.current.flags
  ) {
    initialValuesRef.current = {
      urls: {
        authors_url: dumpConfig.authors_url,
        works_url: dumpConfig.works_url,
        editions_url: dumpConfig.editions_url,
      },
      flags: {
        process_authors: dumpConfig.default_process_authors,
        process_works: dumpConfig.default_process_works,
        process_editions: dumpConfig.default_process_editions,
      },
    };
  }

  const initialUrls = initialValuesRef.current.urls;
  const initialProcessFlags = initialValuesRef.current.flags;

  const {
    formData,
    isDownloading,
    isIngesting,
    error,
    handleFieldChange,
    handleDownload,
    handleIngest,
    handleResetToDefaults,
  } = useOpenLibrarySettings({
    initialUrls,
    initialProcessFlags,
    onDownloadSuccess: () => {
      showSuccess("Download task created. Check Scheduled Tasks for progress.");
      // Refresh task list to catch the newly created task
      void refreshDownloadTasks();
    },
    onIngestSuccess: () => {
      showSuccess("Ingest task created. Check Scheduled Tasks for progress.");
      // Refresh task list to catch the newly created task
      void refreshIngestTasks();
    },
    onError: (errorMessage) => {
      showDanger(`Failed to create task: ${errorMessage}`);
    },
  });

  if (isConfigLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-2 text-text-a30">
          <i className="pi pi-spin pi-spinner" aria-hidden="true" />
          <span>Loading configuration...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-8">
        {/* Configuration Section */}
        {dumpConfig && (
          <div className="flex flex-col gap-4">
            <h3 className="font-semibold text-lg text-text-a0">
              Configuration
            </h3>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              {/* Staleness Threshold */}
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="staleness_threshold_days"
                  className="font-medium text-sm text-text-a10 leading-normal"
                >
                  Staleness Threshold (days)
                </label>
                <input
                  type="number"
                  id="staleness_threshold_days"
                  min="1"
                  value={dumpConfig.staleness_threshold_days}
                  onChange={(e) => {
                    const value = parseInt(e.target.value, 10);
                    if (!Number.isNaN(value) && value >= 1) {
                      updateConfigField("staleness_threshold_days", value);
                    }
                  }}
                  className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
                />
              </div>

              {/* Auto-Download */}
              <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
                <input
                  type="checkbox"
                  checked={dumpConfig.enable_auto_download}
                  onChange={onBlurChange((e) => {
                    updateConfigField("enable_auto_download", e.target.checked);
                  })}
                  className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
                />
                <div className="flex flex-col gap-1">
                  <span className="font-medium text-sm text-text-a10">
                    Enable Auto-Download
                  </span>
                  <span className="text-text-a30 text-xs">
                    Automatically download dumps when they become stale.
                  </span>
                </div>
              </label>

              {/* Auto-Ingest */}
              <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
                <input
                  type="checkbox"
                  checked={dumpConfig.enable_auto_process}
                  onChange={onBlurChange((e) => {
                    updateConfigField("enable_auto_process", e.target.checked);
                  })}
                  className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
                />
                <div className="flex flex-col gap-1">
                  <span className="font-medium text-sm text-text-a10">
                    Enable Auto-Ingest
                  </span>
                  <span className="text-text-a30 text-xs">
                    Automatically ingest dumps after download.
                  </span>
                </div>
              </label>
            </div>
          </div>
        )}

        {/* Download Section */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg text-text-a0">
              Download Dumps
            </h3>
            <span className="text-sm text-text-a30">(Step 1)</span>
          </div>
          <p className="text-sm text-text-a30">
            Configure URLs and download dump files from OpenLibrary. Downloaded
            files are stored locally and can be processed later.
          </p>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Authors Dump URL */}
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
                onChange={(e) => {
                  handleFieldChange("authors_url", e.target.value);
                  if (dumpConfig) {
                    updateConfigField("authors_url", e.target.value || null);
                  }
                }}
                placeholder="https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              />
              <p className="text-text-a30 text-xs">
                URL for the authors metadata dump file.
              </p>
            </div>

            {/* Works Dump URL */}
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
                onChange={(e) => {
                  handleFieldChange("works_url", e.target.value);
                  if (dumpConfig) {
                    updateConfigField("works_url", e.target.value || null);
                  }
                }}
                placeholder="https://openlibrary.org/data/ol_dump_works_latest.txt.gz"
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              />
              <p className="text-text-a30 text-xs">
                URL for the works metadata dump file.
              </p>
            </div>

            {/* Editions Dump URL */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="editions_url"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Editions Dump URL
              </label>
              <input
                type="url"
                id="editions_url"
                value={formData.editions_url || ""}
                onChange={(e) => {
                  handleFieldChange("editions_url", e.target.value);
                  if (dumpConfig) {
                    updateConfigField("editions_url", e.target.value || null);
                  }
                }}
                disabled
                placeholder="https://openlibrary.org/data/ol_dump_editions_latest.txt.gz"
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30 disabled:cursor-not-allowed disabled:bg-surface-a5 disabled:opacity-50"
              />
              <p className="text-text-a30 text-xs">
                URL for the editions metadata dump file (disabled).
              </p>
            </div>
          </div>
          <div className="flex justify-end">
            <Button
              type="button"
              variant="success"
              onClick={handleDownload}
              disabled={hasActiveDownloadTask || hasActiveIngestTask}
              loading={isDownloading || hasActiveDownloadTask}
            >
              {hasActiveDownloadTask ? (
                <>
                  <i
                    className="pi pi-spinner animate-spin"
                    aria-hidden="true"
                  />
                  <span>Downloading...</span>
                </>
              ) : (
                "Download dumps"
              )}
            </Button>
          </div>
        </div>

        {/* Ingest/Process Section */}
        <div className="flex flex-col gap-4 border-surface-a20 border-t pt-6">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg text-text-a0">Ingest Dumps</h3>
            <span className="text-sm text-text-a30">(Step 2)</span>
          </div>
          <p className="text-sm text-text-a30">
            Process downloaded dump files into the database. Select which dump
            types to ingest. Files must be downloaded first.
          </p>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Authors Ingest Checkbox */}
            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                id="process_authors"
                checked={formData.process_authors ?? true}
                onChange={onBlurChange((e) => {
                  handleFieldChange("process_authors", e.target.checked);
                  if (dumpConfig) {
                    updateConfigField(
                      "default_process_authors",
                      e.target.checked,
                    );
                  }
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Process Authors
                </span>
                <span className="text-text-a30 text-xs">
                  Ingest authors metadata from downloaded dump file.
                </span>
              </div>
            </label>

            {/* Works Ingest Checkbox */}
            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                id="process_works"
                checked={formData.process_works ?? true}
                onChange={onBlurChange((e) => {
                  handleFieldChange("process_works", e.target.checked);
                  if (dumpConfig) {
                    updateConfigField(
                      "default_process_works",
                      e.target.checked,
                    );
                  }
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Process Works
                </span>
                <span className="text-text-a30 text-xs">
                  Ingest works metadata from downloaded dump file.
                </span>
              </div>
            </label>

            {/* Editions Ingest Checkbox */}
            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 opacity-50 transition-colors">
              <input
                type="checkbox"
                id="process_editions"
                checked={formData.process_editions ?? false}
                onChange={onBlurChange((e) => {
                  handleFieldChange("process_editions", e.target.checked);
                  if (dumpConfig) {
                    updateConfigField(
                      "default_process_editions",
                      e.target.checked,
                    );
                  }
                })}
                disabled
                className="mt-0.5 h-4 w-4 cursor-not-allowed rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Process Editions
                </span>
                <span className="text-text-a30 text-xs">
                  Ingest editions metadata (currently disabled).
                </span>
              </div>
            </label>
          </div>
          <div className="flex justify-end">
            <Button
              type="button"
              variant="primary"
              onClick={handleIngest}
              disabled={hasActiveDownloadTask || hasActiveIngestTask}
              loading={isIngesting || hasActiveIngestTask}
            >
              {hasActiveIngestTask ? (
                <>
                  <i
                    className="pi pi-spinner animate-spin"
                    aria-hidden="true"
                  />
                  <span>Ingesting...</span>
                </>
              ) : (
                "Ingest dumps"
              )}
            </Button>
          </div>
        </div>

        {/* Reset Button */}
        <div className="flex justify-start border-surface-a20 border-t pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={handleResetToDefaults}
          >
            Reset to defaults
          </Button>
        </div>
      </div>
    </div>
  );
}
