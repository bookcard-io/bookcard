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

import { useCallback, useEffect, useRef, useState } from "react";
import {
  downloadOpenLibraryDumps,
  getDefaultDumpUrls,
  ingestOpenLibraryDumps,
} from "@/services/openLibrarySettingsService";

export interface OpenLibrarySettingsFormData {
  authors_url: string | null;
  works_url: string | null;
  editions_url: string | null;
  process_authors: boolean;
  process_works: boolean;
  process_editions: boolean;
}

export interface UseOpenLibrarySettingsOptions {
  /** Callback when download is successful. */
  onDownloadSuccess?: () => void;
  /** Callback when ingest is successful. */
  onIngestSuccess?: () => void;
  /** Callback when an error occurs. */
  onError?: (error: string) => void;
  /** Initial URLs from backend config. */
  initialUrls?: {
    authors_url: string | null;
    works_url: string | null;
    editions_url: string | null;
  };
  /** Initial process flags from backend config. */
  initialProcessFlags?: {
    process_authors: boolean;
    process_works: boolean;
    process_editions: boolean;
  };
}

export interface UseOpenLibrarySettingsReturn {
  /** Form data state. */
  formData: OpenLibrarySettingsFormData;
  /** Whether download is in progress. */
  isDownloading: boolean;
  /** Whether ingest is in progress. */
  isIngesting: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Handler for field changes. */
  handleFieldChange: <K extends keyof OpenLibrarySettingsFormData>(
    field: K,
    value: OpenLibrarySettingsFormData[K],
  ) => void;
  /** Handler to trigger download. */
  handleDownload: () => Promise<void>;
  /** Handler to trigger ingest. */
  handleIngest: () => Promise<void>;
  /** Handler to reset to defaults. */
  handleResetToDefaults: () => void;
}

/**
 * Custom hook for managing OpenLibrary settings.
 *
 * Handles form state management for OpenLibrary dump settings (client-side only).
 * Follows SRP by separating settings logic from UI components.
 * Follows IOC by accepting callbacks as dependencies.
 * Follows DRY by centralizing form state and change tracking.
 *
 * Parameters
 * ----------
 * options : UseOpenLibrarySettingsOptions
 *     Configuration options including callbacks.
 *
 * Returns
 * -------
 * UseOpenLibrarySettingsReturn
 *     Object with settings state and handlers.
 */
export function useOpenLibrarySettings(
  options: UseOpenLibrarySettingsOptions = {},
): UseOpenLibrarySettingsReturn {
  const {
    onDownloadSuccess,
    onIngestSuccess,
    onError,
    initialUrls,
    initialProcessFlags,
  } = options;

  const defaults = getDefaultDumpUrls();
  const [formData, setFormData] = useState<OpenLibrarySettingsFormData>({
    authors_url: initialUrls?.authors_url ?? defaults.authors_url,
    works_url: initialUrls?.works_url ?? defaults.works_url,
    editions_url: initialUrls?.editions_url ?? defaults.editions_url,
    process_authors: initialProcessFlags?.process_authors ?? true,
    process_works: initialProcessFlags?.process_works ?? true,
    process_editions: initialProcessFlags?.process_editions ?? false,
  });
  const [isDownloading, setIsDownloading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync formData when initial values are first provided (only once)
  const hasInitializedRef = useRef(false);
  useEffect(() => {
    // Only sync once when initial values are first provided
    if (!hasInitializedRef.current && (initialUrls || initialProcessFlags)) {
      hasInitializedRef.current = true;
      setFormData((prev) => ({
        ...prev,
        ...(initialUrls && {
          authors_url: initialUrls.authors_url ?? prev.authors_url,
          works_url: initialUrls.works_url ?? prev.works_url,
          editions_url: initialUrls.editions_url ?? prev.editions_url,
        }),
        ...(initialProcessFlags && {
          process_authors:
            initialProcessFlags.process_authors ?? prev.process_authors,
          process_works:
            initialProcessFlags.process_works ?? prev.process_works,
          process_editions:
            initialProcessFlags.process_editions ?? prev.process_editions,
        }),
      }));
    }
  }, [initialUrls, initialProcessFlags]);

  const handleFieldChange = useCallback(
    <K extends keyof OpenLibrarySettingsFormData>(
      field: K,
      value: OpenLibrarySettingsFormData[K],
    ) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      setError(null);
    },
    [],
  );

  const handleResetToDefaults = useCallback(() => {
    const defaults = getDefaultDumpUrls();
    setFormData({
      authors_url: defaults.authors_url,
      works_url: defaults.works_url,
      editions_url: defaults.editions_url,
      process_authors: true,
      process_works: true,
      process_editions: false,
    });
    setError(null);
  }, []);

  const handleDownload = useCallback(async () => {
    try {
      setIsDownloading(true);
      setError(null);

      // Collect non-empty URLs
      const urls: string[] = [];
      if (formData.authors_url) {
        urls.push(formData.authors_url);
      }
      if (formData.works_url) {
        urls.push(formData.works_url);
      }
      if (formData.editions_url) {
        urls.push(formData.editions_url);
      }

      if (urls.length === 0) {
        throw new Error("Please provide at least one URL to download");
      }

      await downloadOpenLibraryDumps(urls);

      // Task created successfully - it will be visible in the task list
      // The task will handle the actual download and report progress
      if (onDownloadSuccess) {
        onDownloadSuccess();
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to download files";
      setError(message);
      if (onError) {
        onError(message);
      }
    } finally {
      setIsDownloading(false);
    }
  }, [formData, onDownloadSuccess, onError]);

  const handleIngest = useCallback(async () => {
    try {
      setIsIngesting(true);
      setError(null);

      // Check if at least one file type is enabled
      if (
        !formData.process_authors &&
        !formData.process_works &&
        !formData.process_editions
      ) {
        throw new Error("Please select at least one file type to process");
      }

      await ingestOpenLibraryDumps({
        process_authors: formData.process_authors,
        process_works: formData.process_works,
        process_editions: formData.process_editions,
      });

      // Task created successfully - it will be visible in the task list
      // The task will handle the actual ingest and report progress
      if (onIngestSuccess) {
        onIngestSuccess();
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to ingest files";
      setError(message);
      if (onError) {
        onError(message);
      }
    } finally {
      setIsIngesting(false);
    }
  }, [formData, onIngestSuccess, onError]);

  return {
    formData,
    isDownloading,
    isIngesting,
    error,
    handleFieldChange,
    handleDownload,
    handleIngest,
    handleResetToDefaults,
  };
}
