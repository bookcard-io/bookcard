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

import { useCallback, useState } from "react";
import {
  downloadOpenLibraryDumps,
  getDefaultDumpUrls,
} from "@/services/openLibrarySettingsService";

export interface OpenLibrarySettingsFormData {
  authors_url: string | null;
  works_url: string | null;
}

export interface UseOpenLibrarySettingsOptions {
  /** Callback when download is successful. */
  onDownloadSuccess?: () => void;
  /** Callback when an error occurs. */
  onError?: (error: string) => void;
}

export interface UseOpenLibrarySettingsReturn {
  /** Form data state. */
  formData: OpenLibrarySettingsFormData;
  /** Whether download is in progress. */
  isDownloading: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Handler for field changes. */
  handleFieldChange: <K extends keyof OpenLibrarySettingsFormData>(
    field: K,
    value: OpenLibrarySettingsFormData[K],
  ) => void;
  /** Handler to trigger download. */
  handleDownload: () => Promise<void>;
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
  const { onDownloadSuccess, onError } = options;

  const defaults = getDefaultDumpUrls();
  const [formData, setFormData] = useState<OpenLibrarySettingsFormData>({
    authors_url: defaults.authors_url,
    works_url: defaults.works_url,
  });
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return {
    formData,
    isDownloading,
    error,
    handleFieldChange,
    handleDownload,
    handleResetToDefaults,
  };
}
