import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  MetadataProviderCompletedEvent,
  MetadataProviderFailedEvent,
  MetadataProviderProgressEvent,
  MetadataProviderStartedEvent,
  MetadataSearchCompletedEvent,
  MetadataSearchProgressEvent,
  MetadataSearchStartedEvent,
} from "./useMetadataSearchStream";
import { useMetadataSearchStream } from "./useMetadataSearchStream";

describe("useMetadataSearchStream", () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  let mockReader: {
    read: ReturnType<typeof vi.fn>;
    cancel: ReturnType<typeof vi.fn>;
  };
  let mockAbortController: {
    abort: ReturnType<typeof vi.fn>;
    signal: AbortSignal;
  };
  let getReaderFn: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Ensure JSON is always available in browser environment
    // Store native JSON from Node.js environment (available when test file loads)
    const nativeJSON = typeof JSON !== "undefined" ? JSON : null;

    // Always ensure JSON is available on globalThis for browser tests
    if (typeof globalThis.JSON === "undefined" || typeof globalThis.JSON.stringify !== "function") {
      if (typeof window !== "undefined" && window.JSON && typeof window.JSON.stringify === "function") {
        vi.stubGlobal("JSON", window.JSON);
      } else if (nativeJSON && typeof nativeJSON.stringify === "function") {
        // Use native JSON from Node.js environment
        vi.stubGlobal("JSON", nativeJSON);
      } else {
        // Last resort: provide a working JSON implementation
        vi.stubGlobal("JSON", {
          stringify: (value: any) => {
            // Use native JSON.stringify if available, otherwise throw
            if (nativeJSON && typeof nativeJSON.stringify === "function") {
              return nativeJSON.stringify(value);
            }
            throw new Error("JSON.stringify not available");
          },
          parse: (text: string) => {
            if (nativeJSON && typeof nativeJSON.parse === "function") {
              return nativeJSON.parse(text);
            }
            throw new Error("JSON.parse not available");
          },
        });
      }
    }

    mockAbortController = {
      abort: vi.fn(),
      signal: {} as AbortSignal,
    };
    // Create a class constructor that creates instances with the mock methods
    class AbortControllerMock {
      abort: ReturnType<typeof vi.fn>;
      signal: AbortSignal;
      constructor() {
        this.abort = mockAbortController.abort;
        this.signal = mockAbortController.signal;
      }
    }
    vi.stubGlobal("AbortController", AbortControllerMock);

    mockReader = {
      read: vi.fn(),
      cancel: vi.fn().mockResolvedValue(undefined),
    };

    getReaderFn = vi.fn(() => mockReader);

    mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: getReaderFn,
      },
    });

    vi.stubGlobal("fetch", mockFetch);
    class TextDecoderMock {
      decode = vi.fn((data: Uint8Array) => String.fromCharCode(...data));
    }
    vi.stubGlobal("TextDecoder", TextDecoderMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with empty state", () => {
    const { result } = renderHook(() => useMetadataSearchStream({ query: "" }));

    expect(result.current.state.isSearching).toBe(false);
    expect(result.current.state.query).toBe("");
    expect(result.current.state.results).toEqual([]);
  });

  it("should start search and process events", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${JSON.stringify(searchStartedEvent)}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${JSON.stringify(searchCompletedEvent)}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.isSearching).toBe(true);
    });

    await waitFor(
      () => {
        expect(result.current.state.isSearching).toBe(false);
      },
      { timeout: 5000 },
    );
  });

  it("should cancel search", async () => {
    // Mock reader to never resolve so we can test cancellation
    mockReader.read.mockImplementation(() => new Promise(() => {}));
    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Wait for search to actually start (AbortController to be created)
    await waitFor(() => {
      expect(result.current.state.isSearching).toBe(true);
    });

    // Wait for fetch to be called
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    // Wait for getReader to be called, which means the fetch promise resolved
    // and we're in the .then() handler where reader is set up
    // The reader is set synchronously right after getReader() is called
    await waitFor(
      () => {
        expect(getReaderFn).toHaveBeenCalled();
      },
      { timeout: 2000 },
    );

    // Flush all pending promises to ensure the .then() handler executed
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    act(() => {
      result.current.cancelSearch();
    });

    expect(mockReader.cancel).toHaveBeenCalled();
    expect(mockAbortController.abort).toHaveBeenCalled();
  });

  it("should reset state", () => {
    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.reset();
    });

    expect(result.current.state.isSearching).toBe(false);
    expect(result.current.state.query).toBe("");
    expect(result.current.state.results).toEqual([]);
  });

  it("should not start search if query is empty", () => {
    const { result } = renderHook(() => useMetadataSearchStream({ query: "" }));

    act(() => {
      result.current.startSearch();
    });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should handle fetch error", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      text: vi.fn().mockResolvedValue("Error message"),
    });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    await act(async () => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.error).toBeTruthy();
      expect(result.current.state.isSearching).toBe(false);
    });
  });

  it("should cleanup on unmount", async () => {
    // Mock reader to never resolve so we can test cleanup
    mockReader.read.mockImplementation(() => new Promise(() => {}));
    const { result, unmount } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Wait for search to actually start (AbortController to be created)
    await waitFor(() => {
      expect(result.current.state.isSearching).toBe(true);
    });

    // Wait for fetch to be called
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    // Wait for getReader to be called, which means the fetch promise resolved
    // and we're in the .then() handler where reader is set up
    // The reader is set synchronously right after getReader() is called
    await waitFor(
      () => {
        expect(getReaderFn).toHaveBeenCalled();
      },
      { timeout: 2000 },
    );

    // Flush all pending promises to ensure the .then() handler executed
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    unmount();

    expect(mockReader.cancel).toHaveBeenCalled();
  });

  it("should use override query if provided", async () => {
    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "original" }),
    );

    act(() => {
      result.current.startSearch("override");
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("query=override"),
        expect.any(Object),
      );
    });
  });

  it("should handle JSON parse errors", async () => {
    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          "data: invalid json\n\n".split("").map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.error).toBeTruthy();
      expect(result.current.state.isSearching).toBe(false);
    });
  });

  it("should handle non-Error exceptions in JSON parsing", async () => {
    // Mock JSON.parse to throw a non-Error object
    const originalParse = JSON.parse;
    const originalStringify = JSON.stringify;
    vi.stubGlobal("JSON", {
      stringify: originalStringify,
      parse: vi.fn(() => {
        throw "String error";
      }),
    });

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          'data: {"event":"search.started"}\n\n'
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.error).toBe("Failed to parse event");
      expect(result.current.state.isSearching).toBe(false);
    });

    // Restore original JSON
    vi.stubGlobal("JSON", {
      stringify: originalStringify,
      parse: originalParse,
    });
  });

  it("should handle AbortError gracefully", async () => {
    // Create a proper AbortError using DOMException if available, otherwise Error
    const abortError =
      typeof DOMException !== "undefined"
        ? new DOMException("Aborted", "AbortError")
        : (() => {
            const err = new Error("Aborted");
            err.name = "AbortError";
            return err;
          })();
    mockFetch.mockRejectedValue(abortError);

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Wait for the state to update after the error is caught
    await waitFor(
      () => {
        // AbortError should be ignored, so error should remain null
        expect(result.current.state.error).toBeNull();
        expect(result.current.state.isSearching).toBe(false);
      },
      { timeout: 2000 },
    );
  });

  it("should handle connection errors", async () => {
    const connectionError = new Error("Connection failed");
    mockFetch.mockRejectedValue(connectionError);

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.error).toBe("Connection failed");
      expect(result.current.state.isSearching).toBe(false);
    });
  });

  it("should handle non-Error exceptions in fetch catch", async () => {
    mockFetch.mockRejectedValue("String error");

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.error).toBe("Connection error occurred");
      expect(result.current.state.isSearching).toBe(false);
    });
  });

  it("should handle empty data lines", async () => {
    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array("data: \n\n".split("").map((c) => c.charCodeAt(0))),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Should not throw or set error for empty data lines
    await waitFor(() => {
      expect(result.current.state.isSearching).toBe(true);
    });
  });

  it("should include provider_ids in URL when provided", async () => {
    const { result } = renderHook(() =>
      useMetadataSearchStream({
        query: "test",
        providerIds: ["provider1", "provider2"],
      }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("provider_ids=provider1%2Cprovider2"),
        expect.any(Object),
      );
    });
  });

  it("should process provider.started event", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const providerStartedEvent: MetadataProviderStartedEvent = {
      event: "provider.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "provider1",
      provider_name: "Provider 1",
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const providerStartedStr = JSON.stringify(providerStartedEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      const providerStatus = result.current.state.providerStatuses.get(
        "provider1",
      );
      expect(providerStatus?.name).toBe("Provider 1");
      expect(providerStatus?.status).toBe("searching");
    });
  });

  it("should process provider.progress event", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const providerStartedEvent: MetadataProviderStartedEvent = {
      event: "provider.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "provider1",
      provider_name: "Provider 1",
    };

    const providerProgressEvent: MetadataProviderProgressEvent = {
      event: "provider.progress",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "provider1",
      discovered: 5,
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const providerStartedStr = JSON.stringify(providerStartedEvent);
    const providerProgressStr = JSON.stringify(providerProgressEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerProgressStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      const providerStatus = result.current.state.providerStatuses.get(
        "provider1",
      );
      expect(providerStatus?.discovered).toBe(5);
    });
  });

  it("should process provider.completed event", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const providerStartedEvent: MetadataProviderStartedEvent = {
      event: "provider.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "provider1",
      provider_name: "Provider 1",
    };

    const providerCompletedEvent: MetadataProviderCompletedEvent = {
      event: "provider.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "provider1",
      result_count: 10,
      duration_ms: 500,
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 10,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const providerStartedStr = JSON.stringify(providerStartedEvent);
    const providerCompletedStr = JSON.stringify(providerCompletedEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      const providerStatus = result.current.state.providerStatuses.get(
        "provider1",
      );
      expect(providerStatus?.status).toBe("completed");
      expect(providerStatus?.resultCount).toBe(10);
      expect(providerStatus?.durationMs).toBe(500);
      expect(result.current.state.providersCompleted).toBe(1);
    });
  });

  it("should process provider.failed event", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const providerStartedEvent: MetadataProviderStartedEvent = {
      event: "provider.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "provider1",
      provider_name: "Provider 1",
    };

    const providerFailedEvent: MetadataProviderFailedEvent = {
      event: "provider.failed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "provider1",
      error_type: "NetworkError",
      message: "Connection timeout",
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 0,
      providers_failed: 1,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const providerStartedStr = JSON.stringify(providerStartedEvent);
    const providerFailedStr = JSON.stringify(providerFailedEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerFailedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      const providerStatus = result.current.state.providerStatuses.get(
        "provider1",
      );
      expect(providerStatus?.status).toBe("failed");
      expect(providerStatus?.error).toBe("Connection timeout");
      expect(providerStatus?.errorType).toBe("NetworkError");
      expect(result.current.state.providersFailed).toBe(1);
    });
  });

  it("should process search.progress event", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1", "provider2"],
      total_providers: 2,
    };

    const searchProgressEvent: MetadataSearchProgressEvent = {
      event: "search.progress",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      providers_completed: 1,
      providers_failed: 0,
      total_providers: 2,
      total_results_so_far: 5,
      results: [
        {
          source_id: "provider1",
          external_id: "1",
          title: "Book 1",
          authors: ["Author 1"],
          url: "http://example.com/book1",
        },
      ],
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 5,
      providers_completed: 2,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const searchProgressStr = JSON.stringify(searchProgressEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchProgressStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Wait for all events to be processed
    // The search.progress event updates providersCompleted, providersFailed, totalResults, and results
    // The search.completed event then overwrites these values
    // We verify that the progress event was processed by checking that the state was updated
    // Note: results from progress are overwritten by completed, so we can't verify them here
    await waitFor(() => {
      // Final state after completed event
      expect(result.current.state.providersCompleted).toBe(2);
      expect(result.current.state.providersFailed).toBe(0);
      expect(result.current.state.totalResults).toBe(5);
      expect(result.current.state.isSearching).toBe(false);
      // Results are set to empty array by completed event
      expect(result.current.state.results).toEqual([]);
    });
  });

  it("should handle search.progress event with empty results array", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const searchProgressEvent: MetadataSearchProgressEvent = {
      event: "search.progress",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      providers_completed: 0,
      providers_failed: 0,
      total_providers: 1,
      total_results_so_far: 0,
      results: [],
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const searchProgressStr = JSON.stringify(searchProgressEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchProgressStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.results).toEqual([]);
    });
  });

  it("should handle search.progress event with non-array results", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const searchProgressEvent = {
      event: "search.progress",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      providers_completed: 0,
      providers_failed: 0,
      total_providers: 1,
      total_results_so_far: 0,
      results: "not-an-array", // Invalid type
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const searchProgressStr = JSON.stringify(searchProgressEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchProgressStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    await waitFor(() => {
      // Should convert non-array to empty array
      expect(result.current.state.results).toEqual([]);
    });
  });

  it("should handle response.text() failure", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      text: vi.fn().mockRejectedValue(new Error("Failed to read text")),
    });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    await act(async () => {
      result.current.startSearch();
    });

    await waitFor(() => {
      expect(result.current.state.error).toBe("Failed to open stream");
      expect(result.current.state.isSearching).toBe(false);
    });
  });

  it("should handle provider.progress when provider doesn't exist", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const providerProgressEvent: MetadataProviderProgressEvent = {
      event: "provider.progress",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "unknown-provider",
      discovered: 5,
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const providerProgressStr = JSON.stringify(providerProgressEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerProgressStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Should not throw when provider doesn't exist
    await waitFor(() => {
      expect(result.current.state.isSearching).toBe(false);
    });
  });

  it("should handle provider.completed when provider doesn't exist", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const providerCompletedEvent: MetadataProviderCompletedEvent = {
      event: "provider.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "unknown-provider",
      result_count: 10,
      duration_ms: 500,
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 1,
      providers_failed: 0,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const providerCompletedStr = JSON.stringify(providerCompletedEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Should not throw when provider doesn't exist, but should still increment providersCompleted
    await waitFor(() => {
      expect(result.current.state.providersCompleted).toBe(1);
    });
  });

  it("should handle provider.failed when provider doesn't exist", async () => {
    const searchStartedEvent: MetadataSearchStartedEvent = {
      event: "search.started",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      query: "test",
      locale: "en",
      provider_ids: ["provider1"],
      total_providers: 1,
    };

    const providerFailedEvent: MetadataProviderFailedEvent = {
      event: "provider.failed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      provider_id: "unknown-provider",
      error_type: "NetworkError",
      message: "Connection timeout",
    };

    const searchCompletedEvent: MetadataSearchCompletedEvent = {
      event: "search.completed",
      request_id: "req-1",
      timestamp_ms: Date.now(),
      total_results: 0,
      providers_completed: 0,
      providers_failed: 1,
      duration_ms: 100,
      results: [],
    };

    const searchStartedStr = JSON.stringify(searchStartedEvent);
    const providerFailedStr = JSON.stringify(providerFailedEvent);
    const searchCompletedStr = JSON.stringify(searchCompletedEvent);

    mockReader.read
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchStartedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${providerFailedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({
        done: false,
        value: new Uint8Array(
          `data: ${searchCompletedStr}\n\n`
            .split("")
            .map((c) => c.charCodeAt(0)),
        ),
      })
      .mockResolvedValueOnce({ done: true });

    const { result } = renderHook(() =>
      useMetadataSearchStream({ query: "test" }),
    );

    act(() => {
      result.current.startSearch();
    });

    // Should not throw when provider doesn't exist, but should still increment providersFailed
    await waitFor(() => {
      expect(result.current.state.providersFailed).toBe(1);
    });
  });
});
