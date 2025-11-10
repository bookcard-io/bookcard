import { render, renderHook, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useModalInteractions } from "./useModalInteractions";

describe("useModalInteractions", () => {
  it("should return interaction handlers", () => {
    const onClose = vi.fn();
    const { result } = renderHook(() => useModalInteractions({ onClose }));
    expect(result.current.handleOverlayClick).toBeDefined();
    expect(result.current.handleModalClick).toBeDefined();
    expect(result.current.handleOverlayKeyDown).toBeDefined();
  });

  it("should call onClose when clicking overlay", () => {
    const onClose = vi.fn();
    const TestComponent = () => {
      const { handleOverlayClick } = useModalInteractions({ onClose });
      return (
        <button
          onClick={handleOverlayClick}
          type="button"
          data-testid="overlay"
        >
          <div data-testid="modal">Modal Content</div>
        </button>
      );
    };

    render(<TestComponent />);
    const overlay = screen.getByTestId("overlay");
    overlay.click();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("should not call onClose when clicking modal content", () => {
    const onClose = vi.fn();
    const TestComponent = () => {
      const { handleOverlayClick, handleModalClick } = useModalInteractions({
        onClose,
      });
      return (
        <button
          onClick={handleOverlayClick}
          type="button"
          data-testid="overlay"
        >
          <button onClick={handleModalClick} type="button" data-testid="modal">
            Modal Content
          </button>
        </button>
      );
    };

    render(<TestComponent />);
    const modal = screen.getByTestId("modal");
    modal.click();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("should stop propagation on modal click", () => {
    const onClose = vi.fn();
    const TestComponent = () => {
      const { handleOverlayClick, handleModalClick } = useModalInteractions({
        onClose,
      });
      return (
        <button
          onClick={handleOverlayClick}
          type="button"
          data-testid="overlay"
        >
          <button onClick={handleModalClick} type="button" data-testid="modal">
            Modal Content
          </button>
        </button>
      );
    };

    render(<TestComponent />);
    const modal = screen.getByTestId("modal");
    const clickEvent = new MouseEvent("click", { bubbles: true });
    const stopPropagationSpy = vi.spyOn(clickEvent, "stopPropagation");
    modal.dispatchEvent(clickEvent);
    expect(stopPropagationSpy).toHaveBeenCalled();
  });

  it("should provide handleOverlayKeyDown handler", () => {
    const onClose = vi.fn();
    const { result } = renderHook(() => useModalInteractions({ onClose }));
    expect(typeof result.current.handleOverlayKeyDown).toBe("function");
    // Handler exists for accessibility but doesn't do anything
    expect(() => result.current.handleOverlayKeyDown()).not.toThrow();
  });
});
