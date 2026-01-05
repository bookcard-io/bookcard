import { useCallback, useEffect, useState } from "react";
import type {
  Indexer,
  IndexerCreate,
  IndexerTestResponse,
  IndexerUpdate,
} from "@/types/indexer";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";

export interface UseIndexersResult {
  indexers: Indexer[];
  isLoading: boolean;
  error: string | null;
  refresh: (options?: { silent?: boolean }) => Promise<void>;
  createIndexer: (data: IndexerCreate) => Promise<Indexer>;
  updateIndexer: (id: number, data: IndexerUpdate) => Promise<Indexer>;
  deleteIndexer: (id: number) => Promise<void>;
  testConnection: (id: number) => Promise<IndexerTestResponse>;
  testNewConnection: (data: IndexerCreate) => Promise<IndexerTestResponse>;
}

export function useIndexers(enabled = true): UseIndexersResult {
  const [indexers, setIndexers] = useState<Indexer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchIndexers = useCallback(
    async (options?: { silent?: boolean }) => {
      if (!enabled) {
        return;
      }

      if (!options?.silent) {
        setIsLoading(true);
      }
      setError(null);

      try {
        const url = "/api/indexers";
        const fetchKey = generateFetchKey(url, { method: "GET" });

        const result = await deduplicateFetch(fetchKey, async () => {
          const response = await fetch(url);
          if (!response.ok) {
            const errorData = (await response.json()) as { detail?: string };
            throw new Error(errorData.detail || "Failed to fetch indexers");
          }
          return (await response.json()) as { items: Indexer[]; total: number };
        });

        setIndexers(result.items);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
      } finally {
        if (!options?.silent) {
          setIsLoading(false);
        }
      }
    },
    [enabled],
  );

  useEffect(() => {
    void fetchIndexers();
  }, [fetchIndexers]);

  const createIndexer = useCallback(async (data: IndexerCreate) => {
    const response = await fetch("/api/indexers", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to create indexer");
    }

    const newIndexer = (await response.json()) as Indexer;
    setIndexers((prev) => [...prev, newIndexer]);
    return newIndexer;
  }, []);

  const updateIndexer = useCallback(async (id: number, data: IndexerUpdate) => {
    const response = await fetch(`/api/indexers/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to update indexer");
    }

    const updatedIndexer = (await response.json()) as Indexer;
    setIndexers((prev) =>
      prev.map((indexer) => (indexer.id === id ? updatedIndexer : indexer)),
    );
    return updatedIndexer;
  }, []);

  const deleteIndexer = useCallback(async (id: number) => {
    const response = await fetch(`/api/indexers/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to delete indexer");
    }

    setIndexers((prev) => prev.filter((indexer) => indexer.id !== id));
  }, []);

  const testConnection = useCallback(async (id: number) => {
    const response = await fetch(`/api/indexers/${id}/test`, {
      method: "POST",
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to test connection");
    }

    return (await response.json()) as IndexerTestResponse;
  }, []);

  const testNewConnection = useCallback(async (data: IndexerCreate) => {
    const response = await fetch("/api/indexers/test", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to test connection");
    }

    return (await response.json()) as IndexerTestResponse;
  }, []);

  return {
    indexers,
    isLoading,
    error,
    refresh: fetchIndexers,
    createIndexer,
    updateIndexer,
    deleteIndexer,
    testConnection,
    testNewConnection,
  };
}
