import { useCallback, useEffect, useState } from "react";
import type {
  DownloadClient,
  DownloadClientCreate,
  DownloadClientListResponse,
  DownloadClientStatusResponse,
  DownloadClientTestResponse,
  DownloadClientUpdate,
  DownloadItemsResponse,
} from "@/types/downloadClient";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";

export function useDownloadClients(enabled = true) {
  const [downloadClients, setDownloadClients] = useState<DownloadClient[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchDownloadClients = useCallback(async () => {
    if (!enabled) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const url = "/api/download-clients";
      const fetchKey = generateFetchKey(url, { method: "GET" });

      const data = await deduplicateFetch(fetchKey, async () => {
        const response = await fetch(url);
        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(
            errorData.detail || "Failed to fetch download clients",
          );
        }
        return (await response.json()) as DownloadClientListResponse;
      });

      setDownloadClients(data.items);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  const createDownloadClient = useCallback(
    async (data: DownloadClientCreate) => {
      const response = await fetch("/api/download-clients", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to create download client");
      }

      const newClient = (await response.json()) as DownloadClient;
      setDownloadClients((prev) => [...prev, newClient]);
      return newClient;
    },
    [],
  );

  const updateDownloadClient = useCallback(
    async (id: number, data: DownloadClientUpdate) => {
      const response = await fetch(`/api/download-clients/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to update download client");
      }

      const updatedClient = (await response.json()) as DownloadClient;
      setDownloadClients((prev) =>
        prev.map((client) => (client.id === id ? updatedClient : client)),
      );
      return updatedClient;
    },
    [],
  );

  const deleteDownloadClient = useCallback(async (id: number) => {
    const response = await fetch(`/api/download-clients/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      // DELETE often returns 204 No Content, so only check for error
      if (response.status !== 204) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to delete download client");
      }
    }

    setDownloadClients((prev) => prev.filter((client) => client.id !== id));
  }, []);

  const testConnection = useCallback(async (id: number) => {
    const response = await fetch(`/api/download-clients/${id}/test`, {
      method: "POST",
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Connection test failed");
    }

    return (await response.json()) as DownloadClientTestResponse;
  }, []);

  const testNewConnection = useCallback(async (data: DownloadClientCreate) => {
    const response = await fetch("/api/download-clients/test", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Connection test failed");
    }

    return (await response.json()) as DownloadClientTestResponse;
  }, []);

  const getClientItems = useCallback(async (id: number) => {
    const response = await fetch(`/api/download-clients/${id}/items`);
    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to fetch client items");
    }
    return (await response.json()) as DownloadItemsResponse;
  }, []);

  const getClientStatus = useCallback(async (id: number) => {
    const response = await fetch(`/api/download-clients/${id}/status`);
    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to fetch client status");
    }
    return (await response.json()) as DownloadClientStatusResponse;
  }, []);

  useEffect(() => {
    void fetchDownloadClients();
  }, [fetchDownloadClients]);

  return {
    downloadClients,
    isLoading,
    error,
    createDownloadClient,
    updateDownloadClient,
    deleteDownloadClient,
    testConnection,
    testNewConnection,
    getClientItems,
    getClientStatus,
    refresh: fetchDownloadClients,
  };
}
