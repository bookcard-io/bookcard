import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  MetadataSearchCompletedEvent,
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
});
