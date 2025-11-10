import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useBookDataUpdates } from "./useBookDataUpdates";

describe("useBookDataUpdates", () => {
  it("should initialize with empty bookDataOverrides", () => {
    const { result } = renderHook(() => useBookDataUpdates());
    expect(result.current.bookDataOverrides.size).toBe(0);
  });

  it("should update book data", () => {
    const { result } = renderHook(() => useBookDataUpdates());
    act(() => {
      result.current.updateBook(1, { title: "Updated Title" });
    });
    expect(result.current.bookDataOverrides.get(1)).toEqual({
      title: "Updated Title",
    });
  });

  it("should merge book data updates", () => {
    const { result } = renderHook(() => useBookDataUpdates());
    act(() => {
      result.current.updateBook(1, { title: "Updated Title" });
    });
    act(() => {
      result.current.updateBook(1, { authors: ["New Author"] });
    });
    expect(result.current.bookDataOverrides.get(1)).toEqual({
      title: "Updated Title",
      authors: ["New Author"],
    });
  });

  it("should update cover with cache buster", () => {
    const { result } = renderHook(() => useBookDataUpdates());
    act(() => {
      result.current.updateCover(1);
    });
    const override = result.current.bookDataOverrides.get(1);
    expect(override?.thumbnail_url).toMatch(/^\/api\/books\/1\/cover\?v=\d+$/);
  });

  it("should clear all overrides", () => {
    const { result } = renderHook(() => useBookDataUpdates());
    act(() => {
      result.current.updateBook(1, { title: "Title 1" });
      result.current.updateBook(2, { title: "Title 2" });
    });
    expect(result.current.bookDataOverrides.size).toBe(2);

    act(() => {
      result.current.clearOverrides();
    });
    expect(result.current.bookDataOverrides.size).toBe(0);
  });

  it("should expose updateBook and updateCover via ref", () => {
    const updateRef = { current: null };
    renderHook(() => useBookDataUpdates({ updateRef }));

    expect(updateRef.current).toBeDefined();
    expect(updateRef.current?.updateBook).toBeDefined();
    expect(updateRef.current?.updateCover).toBeDefined();
  });

  it("should allow external updates via ref", () => {
    const updateRef = { current: null };
    const { result } = renderHook(() => useBookDataUpdates({ updateRef }));

    act(() => {
      updateRef.current?.updateBook(1, { title: "External Update" });
    });

    expect(result.current.bookDataOverrides.get(1)).toEqual({
      title: "External Update",
    });
  });
});
