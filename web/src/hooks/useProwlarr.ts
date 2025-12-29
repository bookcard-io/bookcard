import { useCallback, useEffect, useState } from "react";
import type {
  ProwlarrConfig,
  ProwlarrConfigUpdate,
  ProwlarrSyncResult,
} from "@/types/prowlarr";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";

export interface UseProwlarrResult {
  config: ProwlarrConfig | null;
  isLoading: boolean;
  isSyncing: boolean;
  error: string | null;
  updateConfig: (data: ProwlarrConfigUpdate) => Promise<ProwlarrConfig>;
  syncIndexers: () => Promise<ProwlarrSyncResult>;
}

export function useProwlarr(): UseProwlarrResult {
  const [config, setConfig] = useState<ProwlarrConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchConfig = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const url = "/api/prowlarr/config";
        const fetchKey = generateFetchKey(url, { method: "GET" });

        const result = await deduplicateFetch(fetchKey, async () => {
          const response = await fetch(url);
          if (!response.ok) {
            const errorData = (await response.json()) as { detail?: string };
            throw new Error(
              errorData.detail || "Failed to fetch Prowlarr config",
            );
          }
          return (await response.json()) as ProwlarrConfig;
        });

        if (mounted) {
          setConfig(result);
        }
      } catch (err) {
        if (mounted) {
          const message = err instanceof Error ? err.message : "Unknown error";
          setError(message);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    void fetchConfig();

    return () => {
      mounted = false;
    };
  }, []);

  const updateConfig = useCallback(async (data: ProwlarrConfigUpdate) => {
    const response = await fetch("/api/prowlarr/config", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to update Prowlarr config");
    }

    const updatedConfig = (await response.json()) as ProwlarrConfig;
    setConfig(updatedConfig);
    return updatedConfig;
  }, []);

  const syncIndexers = useCallback(async () => {
    setIsSyncing(true);
    try {
      const response = await fetch("/api/prowlarr/sync", {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to sync with Prowlarr");
      }

      return (await response.json()) as ProwlarrSyncResult;
    } finally {
      setIsSyncing(false);
    }
  }, []);

  return {
    config,
    isLoading,
    isSyncing,
    error,
    updateConfig,
    syncIndexers,
  };
}
