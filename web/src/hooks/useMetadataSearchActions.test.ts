import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useMetadataSearchActions } from "./useMetadataSearchActions";
import type { UseMetadataSearchStreamResult } from "./useMetadataSearchStream";

describe("useMetadataSearchActions", () => {
  let mockSearchStream: UseMetadataSearchStreamResult;
  let setSearchQuery: (query: string) => void;
  let onClose: () => void;

  beforeEach(() => {
    setSearchQuery = vi.fn() as (query: string) => void;
    onClose = vi.fn() as () => void;
    mockSearchStream = {
      state: {
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
      },
      startSearch: vi.fn(),
      cancelSearch: vi.fn(),
      reset: vi.fn(),
    };
  });

  it("should handle search action", () => {
    const { result } = renderHook(() =>
      useMetadataSearchActions({
        searchStream: mockSearchStream,
        setSearchQuery,
        onClose,
      }),
    );

    act(() => {
      result.current.handleSearch("test query");
    });

    expect(setSearchQuery).toHaveBeenCalledWith("test query");
    expect(mockSearchStream.reset).toHaveBeenCalled();
    expect(mockSearchStream.startSearch).toHaveBeenCalledWith("test query");
  });

  it("should trim search query", () => {
    const { result } = renderHook(() =>
      useMetadataSearchActions({
        searchStream: mockSearchStream,
        setSearchQuery,
        onClose,
      }),
    );

    act(() => {
      result.current.handleSearch("  test query  ");
    });

    expect(setSearchQuery).toHaveBeenCalledWith("test query");
    expect(mockSearchStream.startSearch).toHaveBeenCalledWith("test query");
  });

  it("should not search if query is empty after trim", () => {
    const { result } = renderHook(() =>
      useMetadataSearchActions({
        searchStream: mockSearchStream,
        setSearchQuery,
        onClose,
      }),
    );

    act(() => {
      result.current.handleSearch("   ");
    });

    expect(setSearchQuery).not.toHaveBeenCalled();
    expect(mockSearchStream.startSearch).not.toHaveBeenCalled();
  });

  it("should handle cancel action", () => {
    const { result } = renderHook(() =>
      useMetadataSearchActions({
        searchStream: mockSearchStream,
        setSearchQuery,
        onClose,
      }),
    );

    act(() => {
      result.current.handleCancel();
    });

    expect(mockSearchStream.cancelSearch).toHaveBeenCalled();
  });

  it("should handle close action", () => {
    const { result } = renderHook(() =>
      useMetadataSearchActions({
        searchStream: mockSearchStream,
        setSearchQuery,
        onClose,
      }),
    );

    act(() => {
      result.current.handleClose();
    });

    expect(mockSearchStream.cancelSearch).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });
});
