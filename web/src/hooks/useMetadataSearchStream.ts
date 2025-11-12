"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Metadata search event types from backend.
 */
export interface MetadataSearchEvent {
  event: string;
  request_id: string;
  timestamp_ms: number;
}

export interface MetadataSearchStartedEvent extends MetadataSearchEvent {
  event: "search.started";
  query: string;
  locale: string;
  provider_ids: string[];
  total_providers: number;
}

export interface MetadataProviderStartedEvent extends MetadataSearchEvent {
  event: "provider.started";
  provider_id: string;
  provider_name: string;
}

export interface MetadataProviderProgressEvent extends MetadataSearchEvent {
  event: "provider.progress";
  provider_id: string;
  discovered: number;
}

export interface MetadataProviderCompletedEvent extends MetadataSearchEvent {
  event: "provider.completed";
  provider_id: string;
  result_count: number;
  duration_ms: number;
}

export interface MetadataProviderFailedEvent extends MetadataSearchEvent {
  event: "provider.failed";
  provider_id: string;
  error_type: string;
  message: string;
}

export interface MetadataSearchProgressEvent extends MetadataSearchEvent {
  event: "search.progress";
  providers_completed: number;
  providers_failed: number;
  total_providers: number;
  total_results_so_far: number;
  results?: MetadataRecord[];
}

export interface MetadataSearchCompletedEvent extends MetadataSearchEvent {
  event: "search.completed";
  total_results: number;
  providers_completed: number;
  providers_failed: number;
  duration_ms: number;
  results?: MetadataRecord[];
}

export type MetadataSearchEventUnion =
  | MetadataSearchStartedEvent
  | MetadataProviderStartedEvent
  | MetadataProviderProgressEvent
  | MetadataProviderCompletedEvent
  | MetadataProviderFailedEvent
  | MetadataSearchProgressEvent
  | MetadataSearchCompletedEvent;

/**
 * Provider status information.
 */
export interface ProviderStatus {
  id: string;
  name: string;
  status: "pending" | "searching" | "completed" | "failed";
  resultCount: number;
  discovered: number;
  error?: string;
  errorType?: string;
  durationMs?: number;
}

export interface MetadataRecord {
  source_id: string;
  external_id: string | number;
  title: string;
  authors: string[];
  url: string;
  cover_url?: string | null;
  description?: string | null;
  series?: string | null;
  series_index?: number | null;
  identifiers?: Record<string, string>;
  publisher?: string | null;
  published_date?: string | null;
  rating?: number | null;
  languages?: string[];
  tags?: string[];
}

/**
 * Overall search state.
 */
export interface SearchState {
  isSearching: boolean;
  query: string;
  locale: string;
  totalProviders: number;
  providersCompleted: number;
  providersFailed: number;
  totalResults: number;
  providerStatuses: Map<string, ProviderStatus>;
  error: string | null;
  results: MetadataRecord[];
}

export interface UseMetadataSearchStreamOptions {
  /** Search query. */
  query: string;
  /** Locale code (default: 'en'). */
  locale?: string;
  /** Maximum results per provider (default: 20). */
  maxResultsPerProvider?: number;
  /** Provider IDs to search (default: all enabled). */
  providerIds?: string[];
  /** Provider names to enable (default: all available). */
  enableProviders?: string[];
  /** Whether to automatically start search. */
  enabled?: boolean;
  /** Request ID for correlation. */
  requestId?: string;
}

export interface UseMetadataSearchStreamResult {
  /** Current search state. */
  state: SearchState;
  /** Start the search. */
  startSearch: (overrideQuery?: string) => void;
  /** Cancel the current search. */
  cancelSearch: () => void;
  /** Reset the search state. */
  reset: () => void;
}

/**
 * Custom hook for managing metadata search via Server-Sent Events.
 *
 * Handles SSE connection, event parsing, and state management.
 * Follows SRP by focusing solely on SSE connection lifecycle.
 * Uses IOC via options and callbacks.
 *
 * @param options - Search configuration options.
 * @returns Search state and control functions.
 */
export function useMetadataSearchStream(
  options: UseMetadataSearchStreamOptions,
): UseMetadataSearchStreamResult {
  const {
    query,
    locale = "en",
    maxResultsPerProvider = 20,
    providerIds,
    enableProviders,
    requestId,
  } = options;

  const [state, setState] = useState<SearchState>({
    isSearching: false,
    query: "",
    locale: "en",
    totalProviders: 0,
    providersCompleted: 0,
    providersFailed: 0,
    totalResults: 0,
    providerStatuses: new Map(),
    error: null,
    results: [],
  });

  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(
    null,
  );
  const abortControllerRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setState({
      isSearching: false,
      query: "",
      locale: "en",
      totalProviders: 0,
      providersCompleted: 0,
      providersFailed: 0,
      totalResults: 0,
      providerStatuses: new Map(),
      error: null,
      results: [],
    });
  }, []);

  const cancelSearch = useCallback(() => {
    if (readerRef.current) {
      readerRef.current.cancel().catch(() => {
        // Ignore cancellation errors
      });
      readerRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState((prev) => ({ ...prev, isSearching: false }));
  }, []);

  const startSearch = useCallback(
    (overrideQuery?: string) => {
      const searchQuery = overrideQuery ?? query;
      if (!searchQuery.trim()) {
        return;
      }

      // Cancel any existing search
      cancelSearch();

      // Reset state
      reset();

      // Generate request ID if not provided
      const reqId =
        requestId ||
        `req_${Date.now()}_${Math.random().toString(36).substring(7)}`;

      // Build URL
      const url = new URL(
        "/api/metadata/search/stream",
        window.location.origin,
      );
      url.searchParams.set("query", searchQuery);
      url.searchParams.set("locale", locale);
      url.searchParams.set(
        "max_results_per_provider",
        String(maxResultsPerProvider),
      );
      if (providerIds && providerIds.length > 0) {
        url.searchParams.set("provider_ids", providerIds.join(","));
      }
      if (enableProviders && enableProviders.length > 0) {
        url.searchParams.set("enable_providers", enableProviders.join(","));
      }
      url.searchParams.set("request_id", reqId);

      // Create abort controller for fetch cancellation
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      setState((prev) => ({
        ...prev,
        isSearching: true,
        query: searchQuery,
        locale,
        error: null,
      }));

      // Process event and update state
      const processEvent = (data: MetadataSearchEventUnion) => {
        setState((prev) => {
          const newState = { ...prev };
          // Ensure we always have a valid Map, even if prev.providerStatuses is somehow invalid
          const newProviderStatuses = new Map(
            prev.providerStatuses || new Map(),
          );

          switch (data.event) {
            case "search.started": {
              const evt = data as MetadataSearchStartedEvent;
              newState.totalProviders = evt.total_providers;
              // Initialize provider statuses
              for (const providerId of evt.provider_ids) {
                newProviderStatuses.set(providerId, {
                  id: providerId,
                  name: providerId, // Will be updated when provider.started arrives
                  status: "pending",
                  resultCount: 0,
                  discovered: 0,
                });
              }
              break;
            }

            case "provider.started": {
              const evt = data as MetadataProviderStartedEvent;
              newProviderStatuses.set(evt.provider_id, {
                id: evt.provider_id,
                name: evt.provider_name,
                status: "searching",
                resultCount: 0,
                discovered: 0,
              });
              break;
            }

            case "provider.progress": {
              const evt = data as MetadataProviderProgressEvent;
              const existing = newProviderStatuses.get(evt.provider_id);
              if (existing) {
                newProviderStatuses.set(evt.provider_id, {
                  ...existing,
                  discovered: evt.discovered,
                });
              }
              break;
            }

            case "provider.completed": {
              const evt = data as MetadataProviderCompletedEvent;
              const existing = newProviderStatuses.get(evt.provider_id);
              if (existing) {
                newProviderStatuses.set(evt.provider_id, {
                  ...existing,
                  status: "completed",
                  resultCount: evt.result_count,
                  durationMs: evt.duration_ms,
                });
              }
              newState.providersCompleted += 1;
              break;
            }

            case "provider.failed": {
              const evt = data as MetadataProviderFailedEvent;
              const existing = newProviderStatuses.get(evt.provider_id);
              if (existing) {
                newProviderStatuses.set(evt.provider_id, {
                  ...existing,
                  status: "failed",
                  error: evt.message,
                  errorType: evt.error_type,
                });
              }
              newState.providersFailed += 1;
              break;
            }

            case "search.progress": {
              const evt = data as MetadataSearchProgressEvent;
              newState.providersCompleted = evt.providers_completed;
              newState.providersFailed = evt.providers_failed;
              newState.totalResults = evt.total_results_so_far;
              // Update results incrementally as providers complete
              // Always update if results array is provided (even if empty)
              // This ensures we show results as soon as any provider completes
              if (evt.results !== undefined) {
                newState.results = Array.isArray(evt.results)
                  ? evt.results
                  : [];
              }
              break;
            }

            case "search.completed": {
              const evt = data as MetadataSearchCompletedEvent;
              newState.isSearching = false;
              newState.totalResults = evt.total_results;
              newState.providersCompleted = evt.providers_completed;
              newState.providersFailed = evt.providers_failed;
              newState.results = Array.isArray(evt.results) ? evt.results : [];
              break;
            }
          }

          newState.providerStatuses = newProviderStatuses;
          return newState;
        });
      };

      // Fetch and parse SSE stream
      fetch(url.toString(), {
        signal: abortController.signal,
        headers: {
          Accept: "text/event-stream",
        },
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            const text = await response
              .text()
              .catch(() => "Failed to open stream");
            throw new Error(text || "Failed to open stream");
          }

          const reader = response.body.getReader();
          readerRef.current = reader;
          const decoder = new TextDecoder();
          let buffer = "";

          // Parse SSE stream
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || ""; // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const dataStr = line.slice(6).trim();
                if (dataStr) {
                  try {
                    const data = JSON.parse(
                      dataStr,
                    ) as MetadataSearchEventUnion;
                    processEvent(data);

                    // Stop reading if search completed
                    if (data.event === "search.completed") {
                      reader.cancel();
                      readerRef.current = null;
                      abortControllerRef.current = null;
                      return;
                    }
                  } catch (error) {
                    const message =
                      error instanceof Error
                        ? error.message
                        : "Failed to parse event";
                    setState((prev) => ({
                      ...prev,
                      error: message,
                      isSearching: false,
                    }));
                    reader.cancel();
                    readerRef.current = null;
                    abortControllerRef.current = null;
                    return;
                  }
                }
              }
            }
          }

          readerRef.current = null;
          abortControllerRef.current = null;
        })
        .catch((error) => {
          if (error.name === "AbortError") {
            // Search was cancelled, ignore but still update state
            setState((prev) => ({
              ...prev,
              isSearching: false,
            }));
            readerRef.current = null;
            abortControllerRef.current = null;
            return;
          }
          const message =
            error instanceof Error
              ? error.message
              : "Connection error occurred";
          setState((prev) => ({
            ...prev,
            error: message,
            isSearching: false,
          }));
          readerRef.current = null;
          abortControllerRef.current = null;
        });
    },
    [
      query,
      locale,
      maxResultsPerProvider,
      providerIds,
      enableProviders,
      requestId,
      cancelSearch,
      reset,
    ],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancelSearch();
    };
  }, [cancelSearch]);

  return {
    state,
    startSearch,
    cancelSearch,
    reset,
  };
}
