import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useCoverUrlInput } from "./useCoverUrlInput";

describe("useCoverUrlInput", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("should initialize with hidden input", () => {
    const { result } = renderHook(() => useCoverUrlInput());
    expect(result.current.isVisible).toBe(false);
    expect(result.current.value).toBe("");
  });

  it("should show input", () => {
    const onVisibilityChange = vi.fn();
    const { result } = renderHook(() =>
      useCoverUrlInput({ onVisibilityChange }),
    );

    act(() => {
      result.current.show();
    });

    expect(result.current.isVisible).toBe(true);
    expect(onVisibilityChange).toHaveBeenCalledWith(true);
  });

  it("should hide input and clear value", () => {
    const onVisibilityChange = vi.fn();
    const { result } = renderHook(() =>
      useCoverUrlInput({ onVisibilityChange }),
    );

    act(() => {
      result.current.show();
      result.current.setValue("test url");
    });

    act(() => {
      result.current.hide();
    });

    expect(result.current.isVisible).toBe(false);
    expect(result.current.value).toBe("");
    expect(onVisibilityChange).toHaveBeenCalledWith(false);
  });

  it("should handle input change", () => {
    const { result } = renderHook(() => useCoverUrlInput());
    const event = {
      target: { value: "https://example.com/cover.jpg" },
    } as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleChange(event);
    });

    expect(result.current.value).toBe("https://example.com/cover.jpg");
  });

  it("should submit on Enter key", () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useCoverUrlInput({ onSubmit }));

    act(() => {
      result.current.setValue("https://example.com/cover.jpg");
    });

    const event = {
      key: "Enter",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(onSubmit).toHaveBeenCalledWith("https://example.com/cover.jpg");
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should not submit empty value on Enter", () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useCoverUrlInput({ onSubmit }));

    const event = {
      key: "Enter",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("should hide on Escape key", () => {
    const { result } = renderHook(() => useCoverUrlInput());

    act(() => {
      result.current.show();
    });

    const event = {
      key: "Escape",
      preventDefault: vi.fn(),
      stopPropagation: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(result.current.isVisible).toBe(false);
    expect(event.preventDefault).toHaveBeenCalled();
    expect(event.stopPropagation).toHaveBeenCalled();
  });

  it("should set value programmatically", () => {
    const { result } = renderHook(() => useCoverUrlInput());

    act(() => {
      result.current.setValue("https://example.com/cover.jpg");
    });

    expect(result.current.value).toBe("https://example.com/cover.jpg");
  });

  it("should provide input ref", () => {
    const { result } = renderHook(() => useCoverUrlInput());
    expect(result.current.inputRef).toBeDefined();
    expect(result.current.inputRef.current).toBeNull();
  });
});
