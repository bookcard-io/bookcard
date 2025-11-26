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
  const providerTimeoutRefs = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const reset = useCallback(() => {
    // Clear all provider timeouts
    providerTimeoutRefs.current.forEach((timeout) => {
      clearTimeout(timeout);
    });
    providerTimeoutRefs.current.clear();
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
    // Clear all provider timeouts
    providerTimeoutRefs.current.forEach((timeout) => {
      clearTimeout(timeout);
    });
    providerTimeoutRefs.current.clear();
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
              // Set timeout for provider (60 seconds)
              // Note: In test environments, timers may be mocked, but we still set the timeout
              // Tests should use vi.useFakeTimers() and advance time if they want to test timeouts
              const timeoutId = setTimeout(() => {
                setState((prev) => {
                  const statuses = new Map(prev.providerStatuses);
                  const existing = statuses.get(evt.provider_id);
                  if (existing && existing.status === "searching") {
                    statuses.set(evt.provider_id, {
                      ...existing,
                      status: "failed",
                      error: "Provider search timed out after 60 seconds",
                      errorType: "TimeoutError",
                    });
                    providerTimeoutRefs.current.delete(evt.provider_id);
                    return {
                      ...prev,
                      providerStatuses: statuses,
                      providersFailed: prev.providersFailed + 1,
                    };
                  }
                  return prev;
                });
              }, 60000);
              providerTimeoutRefs.current.set(evt.provider_id, timeoutId);
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
              // Clear timeout for this provider
              const timeoutId = providerTimeoutRefs.current.get(
                evt.provider_id,
              );
              if (timeoutId) {
                clearTimeout(timeoutId);
                providerTimeoutRefs.current.delete(evt.provider_id);
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
              // Clear timeout for this provider
              const timeoutId = providerTimeoutRefs.current.get(
                evt.provider_id,
              );
              if (timeoutId) {
                clearTimeout(timeoutId);
                providerTimeoutRefs.current.delete(evt.provider_id);
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

              // Clear all timeouts immediately to prevent race conditions
              providerTimeoutRefs.current.forEach((timeout) => {
                clearTimeout(timeout);
              });
              providerTimeoutRefs.current.clear();

              newState.isSearching = false;
              newState.totalResults = evt.total_results;
              newState.providersCompleted = evt.providers_completed;
              newState.providersFailed = evt.providers_failed;
              newState.results = Array.isArray(evt.results) ? evt.results : [];

              // Only mark providers as failed if backend reports mismatch
              // (i.e., backend says fewer completed/failed than total providers)
              // This handles cases where backend didn't send failure events
              const backendReportedTotal =
                evt.providers_completed + evt.providers_failed;
              if (
                backendReportedTotal < newState.totalProviders &&
                newState.totalProviders > 0
              ) {
                // Backend didn't report all providers - mark missing ones as failed
                let additionalFailures = 0;
                newProviderStatuses.forEach((status, providerId) => {
                  if (
                    status.status === "searching" ||
                    status.status === "pending"
                  ) {
                    newProviderStatuses.set(providerId, {
                      ...status,
                      status: "failed",
                      error:
                        "Provider did not complete search (connection may have been lost)",
                      errorType: "ConnectionError",
                    });
                    additionalFailures += 1;
                  }
                });
                if (additionalFailures > 0) {
                  newState.providersFailed += additionalFailures;
                }
              }
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
                      // Clear all timeouts when search completes
                      providerTimeoutRefs.current.forEach((timeout) => {
                        clearTimeout(timeout);
                      });
                      providerTimeoutRefs.current.clear();
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

          // If stream ends without search.completed, mark all searching providers as failed
          setState((prev) => {
            if (prev.isSearching) {
              const statuses = new Map(prev.providerStatuses);
              let additionalFailures = 0;
              statuses.forEach((status, providerId) => {
                if (
                  status.status === "searching" ||
                  status.status === "pending"
                ) {
                  statuses.set(providerId, {
                    ...status,
                    status: "failed",
                    error: "Search stream ended unexpectedly",
                    errorType: "StreamError",
                  });
                  additionalFailures += 1;
                }
              });
              // Clear all timeouts
              providerTimeoutRefs.current.forEach((timeout) => {
                clearTimeout(timeout);
              });
              providerTimeoutRefs.current.clear();
              return {
                ...prev,
                isSearching: false,
                providerStatuses: statuses,
                providersFailed: prev.providersFailed + additionalFailures,
              };
            }
            return prev;
          });
        })
        .catch((error) => {
          if (error.name === "AbortError") {
            // Search was cancelled, ignore but still update state
            providerTimeoutRefs.current.forEach((timeout) => {
              clearTimeout(timeout);
            });
            providerTimeoutRefs.current.clear();
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
          // Mark all searching providers as failed on connection error
          setState((prev) => {
            const statuses = new Map(prev.providerStatuses);
            let additionalFailures = 0;
            statuses.forEach((status, providerId) => {
              if (
                status.status === "searching" ||
                status.status === "pending"
              ) {
                statuses.set(providerId, {
                  ...status,
                  status: "failed",
                  error: message,
                  errorType: "ConnectionError",
                });
                additionalFailures += 1;
              }
            });
            // Clear all timeouts
            providerTimeoutRefs.current.forEach((timeout) => {
              clearTimeout(timeout);
            });
            providerTimeoutRefs.current.clear();
            return {
              ...prev,
              error: message,
              isSearching: false,
              providerStatuses: statuses,
              providersFailed: prev.providersFailed + additionalFailures,
            };
          });
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
