// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
        // biome-ignore lint/a11y/noStaticElementInteractions: test component
        // biome-ignore lint/a11y/useKeyWithClickEvents: test component
        <div onClick={handleOverlayClick} data-testid="overlay">
          <div data-testid="modal">Modal Content</div>
        </div>
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
        // biome-ignore lint/a11y/noStaticElementInteractions: test component
        // biome-ignore lint/a11y/useKeyWithClickEvents: test component
        <div onClick={handleOverlayClick} data-testid="overlay">
          {/* biome-ignore lint/a11y/noStaticElementInteractions: test component */}
          {/* biome-ignore lint/a11y/useKeyWithClickEvents: test component */}
          <div onClick={handleModalClick} data-testid="modal">
            Modal Content
          </div>
        </div>
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
        // biome-ignore lint/a11y/noStaticElementInteractions: test component
        // biome-ignore lint/a11y/useKeyWithClickEvents: test component
        <div onClick={handleOverlayClick} data-testid="overlay">
          {/* biome-ignore lint/a11y/noStaticElementInteractions: test component */}
          {/* biome-ignore lint/a11y/useKeyWithClickEvents: test component */}
          <div onClick={handleModalClick} data-testid="modal">
            Modal Content
          </div>
        </div>
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
