import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useDragReorder } from "./useDragReorder";

describe("useDragReorder", () => {
  const createMockDragEvent = (
    clientY: number,
    rect: DOMRect,
  ): React.DragEvent<HTMLElement> => {
    const element = document.createElement("div");
    element.getBoundingClientRect = () => rect;
    return {
      clientY,
      currentTarget: element,
      preventDefault: vi.fn(),
    } as unknown as React.DragEvent<HTMLElement>;
  };

  it("should initialize with null states", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    expect(result.current.draggedIndex).toBeNull();
    expect(result.current.dragOverIndex).toBeNull();
    expect(result.current.dropIndicator).toBeNull();
  });

  it("should set draggedIndex when handleDragStart is called", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(2);
    });

    expect(result.current.draggedIndex).toBe(2);
  });

  it("should not set dropIndicator when dragging over same index", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(2);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(125, rect);

    act(() => {
      result.current.handleDragOver(event, 2);
    });

    expect(result.current.dropIndicator).toBeNull();
  });

  it("should set dropIndicator to 'before' when dragging over item above midpoint", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50); // top: 100, height: 50, midpoint: 125
    const event = createMockDragEvent(110, rect); // clientY < midpoint

    act(() => {
      result.current.handleDragOver(event, 1);
    });

    expect(result.current.dragOverIndex).toBe(1);
    expect(result.current.dropIndicator).toEqual({
      index: 1,
      position: "before",
    });
  });

  it("should set dropIndicator to 'after' when dragging over item below midpoint", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50); // top: 100, height: 50, midpoint: 125
    const event = createMockDragEvent(140, rect); // clientY > midpoint

    act(() => {
      result.current.handleDragOver(event, 1);
    });

    expect(result.current.dragOverIndex).toBe(1);
    expect(result.current.dropIndicator).toEqual({
      index: 1,
      position: "after",
    });
  });

  it("should clear dragOverIndex and dropIndicator when handleDragLeave is called", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(125, rect);

    act(() => {
      result.current.handleDragOver(event, 1);
    });

    expect(result.current.dragOverIndex).toBe(1);
    expect(result.current.dropIndicator).not.toBeNull();

    act(() => {
      result.current.handleDragLeave();
    });

    expect(result.current.dragOverIndex).toBeNull();
    expect(result.current.dropIndicator).toBeNull();
  });

  it("should call onReorder and reset state when handleDrop is called", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(110, rect); // before position

    act(() => {
      result.current.handleDragOver(event, 2);
    });

    const dropEvent = createMockDragEvent(110, rect);

    act(() => {
      result.current.handleDrop(dropEvent, 2);
    });

    // draggedIndex (0) < toIndex (2), so after adjustment: insertionIndex = 2 - 1 = 1
    expect(onReorder).toHaveBeenCalledWith(0, 1);
    expect(result.current.draggedIndex).toBeNull();
    expect(result.current.dragOverIndex).toBeNull();
    expect(result.current.dropIndicator).toBeNull();
  });

  it("should adjust insertion index when dropping after target", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(140, rect); // after position

    act(() => {
      result.current.handleDragOver(event, 2);
    });

    const dropEvent = createMockDragEvent(140, rect);

    act(() => {
      result.current.handleDrop(dropEvent, 2);
    });

    // toIndex (2) + 1 = 3, but draggedIndex (0) < 3, so after adjustment: 3 - 1 = 2
    expect(onReorder).toHaveBeenCalledWith(0, 2);
  });

  it("should adjust insertion index when dragging from above to below", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(140, rect); // after position

    act(() => {
      result.current.handleDragOver(event, 2);
    });

    const dropEvent = createMockDragEvent(140, rect);

    act(() => {
      result.current.handleDrop(dropEvent, 2);
    });

    // draggedIndex (0) < insertionIndex (3), so insertionIndex -= 1
    expect(onReorder).toHaveBeenCalledWith(0, 2);
  });

  it("should not call onReorder when draggedIndex equals insertionIndex", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(2);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(110, rect); // before position

    act(() => {
      result.current.handleDragOver(event, 2);
    });

    const dropEvent = createMockDragEvent(110, rect);

    act(() => {
      result.current.handleDrop(dropEvent, 2);
    });

    // After adjustment, insertionIndex would be 2, same as draggedIndex
    expect(onReorder).not.toHaveBeenCalled();
  });

  it("should not call onReorder when draggedIndex is null", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    const rect = new DOMRect(0, 100, 100, 50);
    const dropEvent = createMockDragEvent(110, rect);

    act(() => {
      result.current.handleDrop(dropEvent, 2);
    });

    expect(onReorder).not.toHaveBeenCalled();
  });

  it("should reset all state when handleDragEnd is called", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(125, rect);

    act(() => {
      result.current.handleDragOver(event, 1);
    });

    expect(result.current.draggedIndex).toBe(0);
    expect(result.current.dragOverIndex).toBe(1);
    expect(result.current.dropIndicator).not.toBeNull();

    act(() => {
      result.current.handleDragEnd();
    });

    expect(result.current.draggedIndex).toBeNull();
    expect(result.current.dragOverIndex).toBeNull();
    expect(result.current.dropIndicator).toBeNull();
  });

  it("should prevent default on dragOver event", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(125, rect);

    act(() => {
      result.current.handleDragOver(event, 1);
    });

    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should prevent default on drop event", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(0);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const dropEvent = createMockDragEvent(110, rect);

    act(() => {
      result.current.handleDrop(dropEvent, 1);
    });

    expect(dropEvent.preventDefault).toHaveBeenCalled();
  });

  it("should handle complex reorder scenario: drag from below to above", () => {
    const onReorder = vi.fn();
    const { result } = renderHook(() => useDragReorder({ onReorder }));

    act(() => {
      result.current.handleDragStart(3);
    });

    const rect = new DOMRect(0, 100, 100, 50);
    const event = createMockDragEvent(110, rect); // before position

    act(() => {
      result.current.handleDragOver(event, 1);
    });

    const dropEvent = createMockDragEvent(110, rect);

    act(() => {
      result.current.handleDrop(dropEvent, 1);
    });

    // draggedIndex (3) > insertionIndex (1), so no adjustment needed
    expect(onReorder).toHaveBeenCalledWith(3, 1);
  });

  it("should maintain stable handlers", () => {
    const onReorder = vi.fn();
    const { result, rerender } = renderHook(() =>
      useDragReorder({ onReorder }),
    );

    const initialHandleDragStart = result.current.handleDragStart;
    const initialHandleDragOver = result.current.handleDragOver;
    const initialHandleDragLeave = result.current.handleDragLeave;
    const initialHandleDrop = result.current.handleDrop;
    const initialHandleDragEnd = result.current.handleDragEnd;

    rerender();

    expect(result.current.handleDragStart).toBe(initialHandleDragStart);
    expect(result.current.handleDragOver).toBe(initialHandleDragOver);
    expect(result.current.handleDragLeave).toBe(initialHandleDragLeave);
    expect(result.current.handleDrop).toBe(initialHandleDrop);
    expect(result.current.handleDragEnd).toBe(initialHandleDragEnd);
  });
});
