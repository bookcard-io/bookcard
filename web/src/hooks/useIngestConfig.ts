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
  getIngestConfig,
  type IngestConfig,
  type IngestConfigUpdate,
  updateIngestConfig,
} from "@/services/ingestConfigService";

export interface UseIngestConfigReturn {
  /** Current configuration. */
  config: IngestConfig | null;
  /** Whether configuration is loading. */
  isLoading: boolean;
  /** Whether configuration is saving. */
  isSaving: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Update a configuration field. */
  updateField: <K extends keyof IngestConfigUpdate>(
    field: K,
    value: IngestConfigUpdate[K],
  ) => void;
  /** Refresh configuration from server. */
  refresh: () => Promise<void>;
}

/**
 * Custom hook for managing ingest configuration.
 *
 * Handles loading, updating, and auto-saving configuration with debouncing.
 * Follows SRP by handling only configuration state management.
 * Follows DRY by centralizing configuration logic.
 * Follows IOC by using service layer for persistence.
 *
 * Returns
 * -------
 * UseIngestConfigReturn
 *     Configuration state and update functions.
 */
export function useIngestConfig(): UseIngestConfigReturn {
  const [config, setConfig] = useState<IngestConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingUpdatesRef = useRef<Partial<IngestConfigUpdate>>({});

  const loadConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const loaded = await getIngestConfig();
      setConfig(loaded);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load configuration";
      setError(message);
      console.error("Failed to load ingest config:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const savePendingUpdates = useCallback(async () => {
    const updates = pendingUpdatesRef.current;
    if (Object.keys(updates).length === 0) {
      return;
    }

    const updatesToSave = { ...updates };
    pendingUpdatesRef.current = {};
    setIsSaving(true);
    setError(null);

    try {
      const updated = await updateIngestConfig(updatesToSave);
      setConfig(updated);
    } catch (err) {
      // Re-queue on failure
      pendingUpdatesRef.current = {
        ...pendingUpdatesRef.current,
        ...updatesToSave,
      };
      const message =
        err instanceof Error ? err.message : "Failed to save configuration";
      setError(message);
      console.error("Failed to save ingest config:", err);
    } finally {
      setIsSaving(false);
    }
  }, []);

  const scheduleSave = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      void savePendingUpdates();
    }, 300);
  }, [savePendingUpdates]);

  const updateField = useCallback(
    <K extends keyof IngestConfigUpdate>(
      field: K,
      value: IngestConfigUpdate[K],
    ) => {
      // Optimistically update local state
      setConfig((prev) => {
        if (!prev) return prev;
        return { ...prev, [field]: value };
      });

      // Queue persistence
      pendingUpdatesRef.current[field] = value;
      scheduleSave();
    },
    [scheduleSave],
  );

  return {
    config,
    isLoading,
    isSaving,
    error,
    updateField,
    refresh: loadConfig,
  };
}
