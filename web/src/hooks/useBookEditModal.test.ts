import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useBookEditModal } from "./useBookEditModal";

describe("useBookEditModal", () => {
  it("should initialize with null editingBookId", () => {
    const { result } = renderHook(() => useBookEditModal());
    expect(result.current.editingBookId).toBeNull();
  });

  it("should open modal with book ID", () => {
    const { result } = renderHook(() => useBookEditModal());
    act(() => {
      result.current.handleEditBook(123);
    });
    expect(result.current.editingBookId).toBe(123);
  });

  it("should close modal", () => {
    const { result } = renderHook(() => useBookEditModal());
    act(() => {
      result.current.handleEditBook(123);
    });
    expect(result.current.editingBookId).toBe(123);

    act(() => {
      result.current.handleCloseModal();
    });
    expect(result.current.editingBookId).toBeNull();
  });

  it("should call onOpen callback when opening", () => {
    const onOpen = vi.fn();
    const { result } = renderHook(() => useBookEditModal({ onOpen }));
    act(() => {
      result.current.handleEditBook(123);
    });
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("should call onClose callback when closing", () => {
    const onClose = vi.fn();
    const { result } = renderHook(() => useBookEditModal({ onClose }));
    act(() => {
      result.current.handleEditBook(123);
    });
    act(() => {
      result.current.handleCloseModal();
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("should handle multiple open/close cycles", () => {
    const { result } = renderHook(() => useBookEditModal());
    act(() => {
      result.current.handleEditBook(1);
    });
    expect(result.current.editingBookId).toBe(1);

    act(() => {
      result.current.handleCloseModal();
    });
    expect(result.current.editingBookId).toBeNull();

    act(() => {
      result.current.handleEditBook(2);
    });
    expect(result.current.editingBookId).toBe(2);
  });
});
