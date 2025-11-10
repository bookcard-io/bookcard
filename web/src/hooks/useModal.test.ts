import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useModal } from "./useModal";

describe("useModal", () => {
  beforeEach(() => {
    document.body.style.overflow = "";
  });

  afterEach(() => {
    document.body.style.overflow = "";
  });

  it("should set body overflow to hidden when modal is open", () => {
    renderHook(() => useModal(true));
    expect(document.body.style.overflow).toBe("hidden");
  });

  it("should restore body overflow when modal is closed", () => {
    const { rerender } = renderHook(({ isOpen }) => useModal(isOpen), {
      initialProps: { isOpen: true },
    });
    expect(document.body.style.overflow).toBe("hidden");

    rerender({ isOpen: false });
    expect(document.body.style.overflow).toBe("auto");
  });

  it("should not change overflow when modal is closed", () => {
    renderHook(() => useModal(false));
    expect(document.body.style.overflow).toBe("");
  });

  it("should handle toggling modal state", () => {
    const { rerender } = renderHook(({ isOpen }) => useModal(isOpen), {
      initialProps: { isOpen: false },
    });

    rerender({ isOpen: true });
    expect(document.body.style.overflow).toBe("hidden");

    rerender({ isOpen: false });
    expect(document.body.style.overflow).toBe("auto");
  });
});
