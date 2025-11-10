import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useStagedCoverUrl } from "./useStagedCoverUrl";

describe("useStagedCoverUrl", () => {
  it("should initialize with null stagedCoverUrl", () => {
    const { result } = renderHook(() => useStagedCoverUrl({ bookId: 1 }));
    expect(result.current.stagedCoverUrl).toBeNull();
  });

  it("should set staged cover URL", () => {
    const { result } = renderHook(() => useStagedCoverUrl({ bookId: 1 }));
    act(() => {
      result.current.setStagedCoverUrl("https://example.com/cover.jpg");
    });
    expect(result.current.stagedCoverUrl).toBe("https://example.com/cover.jpg");
  });

  it("should clear staged cover URL", () => {
    const { result } = renderHook(() => useStagedCoverUrl({ bookId: 1 }));
    act(() => {
      result.current.setStagedCoverUrl("https://example.com/cover.jpg");
    });
    act(() => {
      result.current.clearStagedCoverUrl();
    });
    expect(result.current.stagedCoverUrl).toBeNull();
  });

  it("should reset when bookId changes", () => {
    const { result, rerender } = renderHook(
      ({ bookId }) => useStagedCoverUrl({ bookId }),
      { initialProps: { bookId: 1 } },
    );

    act(() => {
      result.current.setStagedCoverUrl("https://example.com/cover.jpg");
    });
    expect(result.current.stagedCoverUrl).toBe("https://example.com/cover.jpg");

    rerender({ bookId: 2 });
    expect(result.current.stagedCoverUrl).toBeNull();
  });

  it("should call onCoverSet when setting cover", () => {
    const onCoverSet = vi.fn();
    const { result } = renderHook(() =>
      useStagedCoverUrl({ bookId: 1, onCoverSet }),
    );
    act(() => {
      result.current.setStagedCoverUrl("https://example.com/cover.jpg");
    });
    expect(onCoverSet).toHaveBeenCalledWith("https://example.com/cover.jpg");
  });

  it("should call onCoverSet when clearing cover", () => {
    const onCoverSet = vi.fn();
    const { result } = renderHook(() =>
      useStagedCoverUrl({ bookId: 1, onCoverSet }),
    );
    act(() => {
      result.current.clearStagedCoverUrl();
    });
    expect(onCoverSet).toHaveBeenCalledWith(null);
  });

  it("should not reset when bookId is null initially", () => {
    const { result } = renderHook(() => useStagedCoverUrl({ bookId: null }));
    act(() => {
      result.current.setStagedCoverUrl("https://example.com/cover.jpg");
    });
    expect(result.current.stagedCoverUrl).toBe("https://example.com/cover.jpg");
  });
});
