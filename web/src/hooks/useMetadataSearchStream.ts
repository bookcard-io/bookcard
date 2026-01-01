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

import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

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
  /** Provider timeout in milliseconds (default: 60000). */
  providerTimeoutMs?: number;
  /** Maximum SSE buffer size in bytes (default: 1048576 = 1MB). */
  maxBufferSize?: number;
}

/**
 * Progress information for search operations.
 */
export interface SearchProgress {
  /** Completion percentage (0-100). */
  percentage: number;
  /** Whether all providers have completed or failed. */
  isComplete: boolean;
  /** Whether any providers have failed. */
  hasErrors: boolean;
}

export interface UseMetadataSearchStreamResult {
  /** Current search state. */
  state: SearchState;
  /** Progress information for UX. */
  progress: SearchProgress;
  /** Start the search. */
  startSearch: (overrideQuery?: string) => void;
  /** Cancel the current search. */
  cancelSearch: () => void;
  /** Reset the search state. */
  reset: () => void;
}

/**
 * Constants for configuration defaults and limits.
 */
const DEFAULT_LOCALE = "en";
const DEFAULT_MAX_RESULTS_PER_PROVIDER = 20;
const DEFAULT_PROVIDER_TIMEOUT_MS = 60000;
const DEFAULT_MAX_BUFFER_SIZE = 1024 * 1024; // 1MB
const SSE_ENDPOINT = "/api/metadata/search/stream";

/**
 * Valid event type strings.
 */
const VALID_EVENT_TYPES = new Set([
  "search.started",
  "provider.started",
  "provider.progress",
  "provider.completed",
  "provider.failed",
  "search.progress",
  "search.completed",
]);

/**
 * Initial search state.
 */
const initialSearchState: SearchState = {
  isSearching: false,
  query: "",
  locale: DEFAULT_LOCALE,
  totalProviders: 0,
  providersCompleted: 0,
  providersFailed: 0,
  totalResults: 0,
  providerStatuses: new Map(),
  error: null,
  results: [],
};

/**
 * Action types for search state reducer.
 */
type SearchAction =
  | { type: "RESET" }
  | { type: "SEARCH_STARTED"; payload: { query: string; locale: string } }
  | { type: "SEARCH_INITIALIZED"; payload: MetadataSearchStartedEvent }
  | { type: "PROVIDER_STARTED"; payload: MetadataProviderStartedEvent }
  | { type: "PROVIDER_PROGRESS"; payload: MetadataProviderProgressEvent }
  | { type: "PROVIDER_COMPLETED"; payload: MetadataProviderCompletedEvent }
  | { type: "PROVIDER_FAILED"; payload: MetadataProviderFailedEvent }
  | { type: "SEARCH_PROGRESS"; payload: MetadataSearchProgressEvent }
  | { type: "SEARCH_COMPLETED"; payload: MetadataSearchCompletedEvent }
  | { type: "STREAM_ENDED_UNEXPECTEDLY" }
  | { type: "CONNECTION_ERROR"; payload: { message: string } }
  | { type: "PARSE_ERROR"; payload: { message: string } }
  | { type: "PROVIDER_TIMEOUT"; payload: { providerId: string } }
  | { type: "SEARCH_CANCELLED" };

/**
 * Validates if an object is a valid metadata search event.
 *
 * @param data - Object to validate.
 * @returns True if valid event, false otherwise.
 */
function isValidEvent(data: unknown): data is MetadataSearchEventUnion {
  if (!data || typeof data !== "object") {
    return false;
  }

  const event = data as Record<string, unknown>;

  if (
    !event.event ||
    typeof event.event !== "string" ||
    !VALID_EVENT_TYPES.has(event.event)
  ) {
    return false;
  }

  if (!event.request_id || typeof event.request_id !== "string") {
    return false;
  }

  if (
    event.timestamp_ms !== undefined &&
    typeof event.timestamp_ms !== "number"
  ) {
    return false;
  }

  return true;
}

/**
 * Validates and sanitizes search query input.
 *
 * @param query - Query string to validate.
 * @returns Sanitized query or null if invalid.
 */
function validateQuery(query: string): string | null {
  const trimmed = query.trim();
  if (trimmed.length === 0 || trimmed.length > 1000) {
    return null;
  }
  return trimmed;
}

/**
 * Validates and sanitizes provider IDs.
 *
 * @param providerIds - Array of provider IDs to validate.
 * @returns Sanitized array or null if invalid.
 */
function validateProviderIds(
  providerIds: string[] | undefined,
): string[] | null {
  if (!providerIds || providerIds.length === 0) {
    return null;
  }

  const sanitized = providerIds
    .map((id) => id.trim())
    .filter((id) => id.length > 0 && id.length <= 100)
    .filter((id) => /^[a-zA-Z0-9_-]+$/.test(id));

  return sanitized.length > 0 ? sanitized : null;
}

/**
 * Builds the search URL with query parameters.
 *
 * @param options - Search configuration options.
 * @param searchQuery - Query string to search for.
 * @param requestId - Request ID for correlation.
 * @returns Complete URL for SSE endpoint.
 */
function buildSearchUrl(
  options: UseMetadataSearchStreamOptions,
  searchQuery: string,
  requestId: string,
): URL {
  const url = new URL(SSE_ENDPOINT, window.location.origin);
  url.searchParams.set("query", searchQuery);
  url.searchParams.set("locale", options.locale ?? DEFAULT_LOCALE);
  url.searchParams.set(
    "max_results_per_provider",
    String(options.maxResultsPerProvider ?? DEFAULT_MAX_RESULTS_PER_PROVIDER),
  );

  const validProviderIds = validateProviderIds(options.providerIds);
  if (validProviderIds) {
    url.searchParams.set("provider_ids", validProviderIds.join(","));
  }

  if (options.enableProviders && options.enableProviders.length > 0) {
    const validEnabled = options.enableProviders
      .map((p) => p.trim())
      .filter((p) => p.length > 0 && p.length <= 100);
    if (validEnabled.length > 0) {
      url.searchParams.set("enable_providers", validEnabled.join(","));
    }
  }

  url.searchParams.set("request_id", requestId);
  return url;
}

/**
 * Generates a unique request ID.
 *
 * @param providedId - Optional provided request ID.
 * @returns Request ID string.
 */
function generateRequestId(providedId?: string): string {
  if (providedId && providedId.trim().length > 0) {
    return providedId.trim();
  }
  return `req_${Date.now()}_${Math.random().toString(36).substring(7)}`;
}

/**
 * Reducer for search state management.
 *
 * @param state - Current search state.
 * @param action - Action to apply.
 * @returns New search state.
 */
function searchReducer(state: SearchState, action: SearchAction): SearchState {
  switch (action.type) {
    case "RESET": {
      return { ...initialSearchState };
    }

    case "SEARCH_STARTED": {
      return {
        ...state,
        isSearching: true,
        query: action.payload.query,
        locale: action.payload.locale,
        error: null,
      };
    }

    case "SEARCH_INITIALIZED": {
      const evt = action.payload;
      const newProviderStatuses = new Map(state.providerStatuses);
      for (const providerId of evt.provider_ids) {
        newProviderStatuses.set(providerId, {
          id: providerId,
          name: providerId,
          status: "pending",
          resultCount: 0,
          discovered: 0,
        });
      }
      return {
        ...state,
        totalProviders: evt.total_providers,
        providerStatuses: newProviderStatuses,
      };
    }

    case "PROVIDER_STARTED": {
      const evt = action.payload;
      const newProviderStatuses = new Map(state.providerStatuses);
      newProviderStatuses.set(evt.provider_id, {
        id: evt.provider_id,
        name: evt.provider_name,
        status: "searching",
        resultCount: 0,
        discovered: 0,
      });
      return {
        ...state,
        providerStatuses: newProviderStatuses,
      };
    }

    case "PROVIDER_PROGRESS": {
      const evt = action.payload;
      const newProviderStatuses = new Map(state.providerStatuses);
      const existing = newProviderStatuses.get(evt.provider_id);
      if (existing) {
        newProviderStatuses.set(evt.provider_id, {
          ...existing,
          discovered: evt.discovered,
        });
      }
      return {
        ...state,
        providerStatuses: newProviderStatuses,
      };
    }

    case "PROVIDER_COMPLETED": {
      const evt = action.payload;
      const newProviderStatuses = new Map(state.providerStatuses);
      const existing = newProviderStatuses.get(evt.provider_id);
      if (existing) {
        newProviderStatuses.set(evt.provider_id, {
          ...existing,
          status: "completed",
          resultCount: evt.result_count,
          durationMs: evt.duration_ms,
        });
      }
      return {
        ...state,
        providerStatuses: newProviderStatuses,
        providersCompleted: state.providersCompleted + 1,
      };
    }

    case "PROVIDER_FAILED": {
      const evt = action.payload;
      const newProviderStatuses = new Map(state.providerStatuses);
      const existing = newProviderStatuses.get(evt.provider_id);
      if (existing) {
        newProviderStatuses.set(evt.provider_id, {
          ...existing,
          status: "failed",
          error: evt.message,
          errorType: evt.error_type,
        });
      }
      return {
        ...state,
        providerStatuses: newProviderStatuses,
        providersFailed: state.providersFailed + 1,
      };
    }

    case "PROVIDER_TIMEOUT": {
      const { providerId } = action.payload;
      const newProviderStatuses = new Map(state.providerStatuses);
      const existing = newProviderStatuses.get(providerId);
      if (existing && existing.status === "searching") {
        newProviderStatuses.set(providerId, {
          ...existing,
          status: "failed",
          error: "Provider search timed out",
          errorType: "TimeoutError",
        });
        return {
          ...state,
          providerStatuses: newProviderStatuses,
          providersFailed: state.providersFailed + 1,
        };
      }
      return state;
    }

    case "SEARCH_PROGRESS": {
      const evt = action.payload;
      return {
        ...state,
        providersCompleted: evt.providers_completed,
        providersFailed: evt.providers_failed,
        totalResults: evt.total_results_so_far,
        results:
          evt.results !== undefined
            ? Array.isArray(evt.results)
              ? evt.results
              : []
            : state.results,
      };
    }

    case "SEARCH_COMPLETED": {
      const evt = action.payload;
      const newProviderStatuses = new Map(state.providerStatuses);
      const backendReportedTotal =
        evt.providers_completed + evt.providers_failed;

      if (
        backendReportedTotal < state.totalProviders &&
        state.totalProviders > 0
      ) {
        let additionalFailures = 0;
        newProviderStatuses.forEach((status, providerId) => {
          if (status.status === "searching" || status.status === "pending") {
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
        return {
          ...state,
          isSearching: false,
          totalResults: evt.total_results,
          providersCompleted: evt.providers_completed,
          providersFailed: evt.providers_failed + additionalFailures,
          providerStatuses: newProviderStatuses,
          results: Array.isArray(evt.results) ? evt.results : [],
        };
      }

      return {
        ...state,
        isSearching: false,
        totalResults: evt.total_results,
        providersCompleted: evt.providers_completed,
        providersFailed: evt.providers_failed,
        providerStatuses: newProviderStatuses,
        results: Array.isArray(evt.results) ? evt.results : [],
      };
    }

    case "STREAM_ENDED_UNEXPECTEDLY": {
      if (!state.isSearching) {
        return state;
      }
      const newProviderStatuses = new Map(state.providerStatuses);
      let additionalFailures = 0;
      newProviderStatuses.forEach((status, providerId) => {
        if (status.status === "searching" || status.status === "pending") {
          newProviderStatuses.set(providerId, {
            ...status,
            status: "failed",
            error: "Search stream ended unexpectedly",
            errorType: "StreamError",
          });
          additionalFailures += 1;
        }
      });
      return {
        ...state,
        isSearching: false,
        providerStatuses: newProviderStatuses,
        providersFailed: state.providersFailed + additionalFailures,
      };
    }

    case "CONNECTION_ERROR": {
      const newProviderStatuses = new Map(state.providerStatuses);
      let additionalFailures = 0;
      newProviderStatuses.forEach((status, providerId) => {
        if (status.status === "searching" || status.status === "pending") {
          newProviderStatuses.set(providerId, {
            ...status,
            status: "failed",
            error: action.payload.message,
            errorType: "ConnectionError",
          });
          additionalFailures += 1;
        }
      });
      return {
        ...state,
        error: action.payload.message,
        isSearching: false,
        providerStatuses: newProviderStatuses,
        providersFailed: state.providersFailed + additionalFailures,
      };
    }

    case "PARSE_ERROR": {
      return {
        ...state,
        error: action.payload.message,
        isSearching: false,
      };
    }

    case "SEARCH_CANCELLED": {
      return {
        ...state,
        isSearching: false,
      };
    }

    default: {
      return state;
    }
  }
}

/**
 * Parses SSE stream and processes events.
 *
 * @param reader - Readable stream reader.
 * @param onEvent - Callback for each valid event.
 * @param onError - Callback for errors.
 * @param maxBufferSize - Maximum buffer size in bytes.
 */
async function parseSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onEvent: (event: MetadataSearchEventUnion) => void,
  onError: (error: Error) => void,
  maxBufferSize: number,
): Promise<void> {
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      if (buffer.length > maxBufferSize) {
        throw new Error(
          `SSE buffer overflow - data too large (max: ${maxBufferSize} bytes)`,
        );
      }

      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.slice(6).trim();
          if (dataStr) {
            try {
              const data = JSON.parse(dataStr);
              if (isValidEvent(data)) {
                onEvent(data);
                if (data.event === "search.completed") {
                  return;
                }
              } else {
                console.warn("Invalid event format:", data);
              }
            } catch (parseError) {
              if (parseError instanceof Error) {
                onError(parseError);
              } else {
                onError(new Error("Failed to parse event"));
              }
              return;
            }
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof Error) {
      onError(error);
    } else {
      onError(new Error("Stream read error"));
    }
  }
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
    locale = DEFAULT_LOCALE,
    requestId,
    providerTimeoutMs = DEFAULT_PROVIDER_TIMEOUT_MS,
    maxBufferSize = DEFAULT_MAX_BUFFER_SIZE,
  } = options;

  const [state, dispatch] = useReducer(searchReducer, initialSearchState);

  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(
    null,
  );
  const abortControllerRef = useRef<AbortController | null>(null);
  const providerTimeoutRefs = useRef<Map<string, NodeJS.Timeout>>(new Map());

  /**
   * Clears all provider timeouts.
   */
  const clearAllTimeouts = useCallback(() => {
    providerTimeoutRefs.current.forEach((timeout) => {
      clearTimeout(timeout);
    });
    providerTimeoutRefs.current.clear();
  }, []);

  const reset = useCallback(() => {
    clearAllTimeouts();
    dispatch({ type: "RESET" });
  }, [clearAllTimeouts]);

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
    clearAllTimeouts();
    dispatch({ type: "SEARCH_CANCELLED" });
  }, [clearAllTimeouts]);

  /**
   * Sets a timeout for a provider and dispatches timeout action if triggered.
   *
   * @param providerId - Provider ID to set timeout for.
   */
  const setProviderTimeout = useCallback(
    (providerId: string) => {
      const timeoutId = setTimeout(() => {
        dispatch({ type: "PROVIDER_TIMEOUT", payload: { providerId } });
        providerTimeoutRefs.current.delete(providerId);
      }, providerTimeoutMs);
      providerTimeoutRefs.current.set(providerId, timeoutId);
    },
    [providerTimeoutMs],
  );

  /**
   * Clears timeout for a specific provider.
   *
   * @param providerId - Provider ID to clear timeout for.
   */
  const clearProviderTimeout = useCallback((providerId: string) => {
    const timeoutId = providerTimeoutRefs.current.get(providerId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      providerTimeoutRefs.current.delete(providerId);
    }
  }, []);

  /**
   * Processes a metadata search event and updates state.
   *
   * @param data - Event data to process.
   */
  const processEvent = useCallback(
    (data: MetadataSearchEventUnion) => {
      switch (data.event) {
        case "search.started": {
          dispatch({
            type: "SEARCH_INITIALIZED",
            payload: data as MetadataSearchStartedEvent,
          });
          break;
        }

        case "provider.started": {
          const evt = data as MetadataProviderStartedEvent;
          dispatch({ type: "PROVIDER_STARTED", payload: evt });
          setProviderTimeout(evt.provider_id);
          break;
        }

        case "provider.progress": {
          dispatch({
            type: "PROVIDER_PROGRESS",
            payload: data as MetadataProviderProgressEvent,
          });
          break;
        }

        case "provider.completed": {
          const evt = data as MetadataProviderCompletedEvent;
          clearProviderTimeout(evt.provider_id);
          dispatch({ type: "PROVIDER_COMPLETED", payload: evt });
          break;
        }

        case "provider.failed": {
          const evt = data as MetadataProviderFailedEvent;
          clearProviderTimeout(evt.provider_id);
          dispatch({ type: "PROVIDER_FAILED", payload: evt });
          break;
        }

        case "search.progress": {
          dispatch({
            type: "SEARCH_PROGRESS",
            payload: data as MetadataSearchProgressEvent,
          });
          break;
        }

        case "search.completed": {
          const evt = data as MetadataSearchCompletedEvent;
          clearAllTimeouts();
          dispatch({ type: "SEARCH_COMPLETED", payload: evt });
          break;
        }
      }
    },
    [clearAllTimeouts, clearProviderTimeout, setProviderTimeout],
  );

  const startSearch = useCallback(
    (overrideQuery?: string) => {
      const searchQuery = overrideQuery ?? query;
      const validatedQuery = validateQuery(searchQuery);
      if (!validatedQuery) {
        return;
      }

      // Cancel any existing search
      cancelSearch();

      // Reset state
      reset();

      // Generate request ID
      const requestIdValue = generateRequestId(requestId);

      // Build URL
      const url = buildSearchUrl(options, validatedQuery, requestIdValue);

      // Create abort controller for fetch cancellation
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      dispatch({
        type: "SEARCH_STARTED",
        payload: { query: validatedQuery, locale },
      });

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

          await parseSSEStream(
            reader,
            (event) => {
              processEvent(event);
              if (event.event === "search.completed") {
                clearAllTimeouts();
                reader.cancel();
                readerRef.current = null;
                abortControllerRef.current = null;
              }
            },
            (error) => {
              // Handle AbortError as cancellation (don't set error)
              if (error.name === "AbortError") {
                clearAllTimeouts();
                dispatch({ type: "SEARCH_CANCELLED" });
              } else {
                // For other errors, treat as connection error and mark providers as failed
                clearAllTimeouts();
                const message =
                  error instanceof Error
                    ? error.message
                    : "Connection error occurred";
                dispatch({ type: "CONNECTION_ERROR", payload: { message } });
              }
              reader.cancel();
              readerRef.current = null;
              abortControllerRef.current = null;
            },
            maxBufferSize,
          );

          readerRef.current = null;
          abortControllerRef.current = null;

          // If stream ends without search.completed, mark all searching providers as failed
          dispatch({ type: "STREAM_ENDED_UNEXPECTEDLY" });
        })
        .catch((error) => {
          if (error.name === "AbortError") {
            // Search was cancelled, ignore but still update state
            clearAllTimeouts();
            dispatch({ type: "SEARCH_CANCELLED" });
            readerRef.current = null;
            abortControllerRef.current = null;
            return;
          }
          const message =
            error instanceof Error
              ? error.message
              : "Connection error occurred";
          clearAllTimeouts();
          dispatch({ type: "CONNECTION_ERROR", payload: { message } });
          readerRef.current = null;
          abortControllerRef.current = null;
        });
    },
    // Removed 'options' from dependencies to prevent infinite loops if 'options' object is unstable
    [
      query,
      locale,
      requestId,
      // options, // CAUSE OF INFINITE LOOP: If options is a new object on every render
      cancelSearch,
      reset,
      processEvent,
      clearAllTimeouts,
      maxBufferSize,
      // Individual option properties used in buildSearchUrl should be dependencies instead if they can change
      options.locale,
      options.maxResultsPerProvider,
      options.providerIds,
      options.enableProviders,
      options,
    ],
  );

  /**
   * Computes progress information for UX.
   */
  const progress = useMemo<SearchProgress>(() => {
    const total = state.totalProviders;
    if (total === 0) {
      return {
        percentage: 0,
        isComplete: false,
        hasErrors: false,
      };
    }

    const completed = state.providersCompleted + state.providersFailed;
    const percentage = Math.round((completed / total) * 100);
    const isComplete = completed >= total;
    const hasErrors = state.providersFailed > 0;

    return {
      percentage,
      isComplete,
      hasErrors,
    };
  }, [state.totalProviders, state.providersCompleted, state.providersFailed]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancelSearch();
    };
  }, [cancelSearch]);

  return {
    state,
    progress,
    startSearch,
    cancelSearch,
    reset,
  };
}
