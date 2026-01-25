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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  ScheduledJob,
  ScheduledJobUpdate,
} from "@/services/scheduledJobsService";
import {
  listScheduledJobs,
  updateScheduledJob,
} from "@/services/scheduledJobsService";

export interface UseScheduledJobsReturn {
  /** Loaded scheduled jobs. */
  jobs: ScheduledJob[];
  /** Whether jobs are loading. */
  isLoading: boolean;
  /** Whether any job update is being saved. */
  isSaving: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Optimistically update a job field and persist (debounced). */
  updateJob: (jobName: string, update: ScheduledJobUpdate) => void;
  /** Refresh jobs from server. */
  refresh: () => Promise<void>;
}

/**
 * Hook for scheduled job management.
 *
 * Returns
 * -------
 * UseScheduledJobsReturn
 *     Scheduled jobs state and update helpers.
 */
export function useScheduledJobs(): UseScheduledJobsReturn {
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debounceTimersRef = useRef<Record<string, NodeJS.Timeout | null>>({});
  const pendingUpdatesRef = useRef<Record<string, ScheduledJobUpdate>>({});

  const load = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const loaded = await listScheduledJobs();
      setJobs(loaded);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load jobs";
      setError(message);
      console.error("Failed to load scheduled jobs:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const jobIndexByName = useMemo(() => {
    const map = new Map<string, number>();
    jobs.forEach((j, idx) => {
      map.set(j.job_name, idx);
    });
    return map;
  }, [jobs]);

  const flushJobUpdate = useCallback(async (jobName: string) => {
    const pending = pendingUpdatesRef.current[jobName];
    if (!pending || Object.keys(pending).length === 0) {
      return;
    }
    const toSave = { ...pending };
    pendingUpdatesRef.current[jobName] = {};

    setIsSaving(true);
    setError(null);
    try {
      const updated = await updateScheduledJob(jobName, toSave);
      setJobs((prev) => {
        const idx = prev.findIndex((j) => j.job_name === jobName);
        if (idx === -1) return prev;
        const next = [...prev];
        next[idx] = updated;
        return next;
      });
    } catch (err) {
      // Re-queue on failure
      pendingUpdatesRef.current[jobName] = {
        ...pendingUpdatesRef.current[jobName],
        ...toSave,
      };
      const message =
        err instanceof Error ? err.message : "Failed to save scheduled job";
      setError(message);
      console.error("Failed to update scheduled job:", err);
    } finally {
      setIsSaving(false);
    }
  }, []);

  const scheduleFlush = useCallback(
    (jobName: string) => {
      const existing = debounceTimersRef.current[jobName];
      if (existing) {
        clearTimeout(existing);
      }
      debounceTimersRef.current[jobName] = setTimeout(() => {
        void flushJobUpdate(jobName);
      }, 300);
    },
    [flushJobUpdate],
  );

  const updateJob = useCallback(
    (jobName: string, update: ScheduledJobUpdate) => {
      // Optimistic update
      const idx = jobIndexByName.get(jobName);
      if (idx !== undefined) {
        setJobs((prev) => {
          const next = [...prev];
          const existing = next[idx];
          if (!existing) {
            return prev;
          }
          next[idx] = { ...existing, ...update };
          return next;
        });
      }

      pendingUpdatesRef.current[jobName] = {
        ...pendingUpdatesRef.current[jobName],
        ...update,
      };
      scheduleFlush(jobName);
    },
    [jobIndexByName, scheduleFlush],
  );

  return {
    jobs,
    isLoading,
    isSaving,
    error,
    updateJob,
    refresh: load,
  };
}
