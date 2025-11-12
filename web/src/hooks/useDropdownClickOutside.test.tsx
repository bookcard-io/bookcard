import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDropdownClickOutside } from "./useDropdownClickOutside";

describe("useDropdownClickOutside", () => {
  let onClose: () => void;
  let buttonRef: React.RefObject<HTMLDivElement>;
  let menuRef: React.RefObject<HTMLDivElement>;
  let buttonElement: HTMLDivElement;
  let menuElement: HTMLDivElement;

  beforeEach(() => {
    onClose = vi.fn();
    buttonElement = document.createElement("div");
    menuElement = document.createElement("div");
    buttonRef = { current: buttonElement };
    menuRef = { current: menuElement };
    document.body.appendChild(buttonElement);
    document.body.appendChild(menuElement);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    if (document.body.contains(buttonElement)) {
      document.body.removeChild(buttonElement);
    }
    if (document.body.contains(menuElement)) {
      document.body.removeChild(menuElement);
    }
  });

  it("should not call onClose when menu is closed", () => {
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: false,
        buttonRef,
        menuRef,
        onClose,
      });
      return <div>Test</div>;
    };

    render(<TestComponent />);
    fireEvent.mouseDown(document.body);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("should call onClose when clicking outside both button and menu", () => {
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: true,
        buttonRef,
        menuRef,
        onClose,
      });
      return (
        <div>
          <div ref={buttonRef} data-testid="button">
            Button
          </div>
          <div ref={menuRef} data-testid="menu">
            Menu
          </div>
          <div data-testid="outside">Outside</div>
        </div>
      );
    };

    render(<TestComponent />);
    const outside = screen.getByTestId("outside");
    fireEvent.mouseDown(outside);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("should not call onClose when clicking on button", () => {
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: true,
        buttonRef,
        menuRef,
        onClose,
      });
      return (
        <div>
          <div ref={buttonRef} data-testid="button">
            Button
          </div>
          <div ref={menuRef} data-testid="menu">
            Menu
          </div>
        </div>
      );
    };

    render(<TestComponent />);
    const button = screen.getByTestId("button");
    fireEvent.mouseDown(button);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("should not call onClose when clicking on menu", () => {
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: true,
        buttonRef,
        menuRef,
        onClose,
      });
      return (
        <div>
          <div ref={buttonRef} data-testid="button">
            Button
          </div>
          <div ref={menuRef} data-testid="menu">
            Menu
          </div>
        </div>
      );
    };

    render(<TestComponent />);
    const menu = screen.getByTestId("menu");
    fireEvent.mouseDown(menu);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("should not call onClose when clicking on child of button", () => {
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: true,
        buttonRef,
        menuRef,
        onClose,
      });
      return (
        <div>
          <div ref={buttonRef} data-testid="button">
            <span data-testid="button-child">Child</span>
          </div>
          <div ref={menuRef} data-testid="menu">
            Menu
          </div>
        </div>
      );
    };

    render(<TestComponent />);
    const child = screen.getByTestId("button-child");
    fireEvent.mouseDown(child);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("should not call onClose when clicking on child of menu", () => {
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: true,
        buttonRef,
        menuRef,
        onClose,
      });
      return (
        <div>
          <div ref={buttonRef} data-testid="button">
            Button
          </div>
          <div ref={menuRef} data-testid="menu">
            <span data-testid="menu-child">Child</span>
          </div>
        </div>
      );
    };

    render(<TestComponent />);
    const child = screen.getByTestId("menu-child");
    fireEvent.mouseDown(child);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("should handle null button ref gracefully", () => {
    const nullButtonRef = { current: null };
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: true,
        buttonRef: nullButtonRef,
        menuRef,
        onClose,
      });
      return (
        <div>
          <div ref={menuRef} data-testid="menu">
            Menu
          </div>
          <div data-testid="outside">Outside</div>
        </div>
      );
    };

    render(<TestComponent />);
    const outside = screen.getByTestId("outside");
    fireEvent.mouseDown(outside);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("should handle null menu ref gracefully", () => {
    const nullMenuRef = { current: null };
    const TestComponent = () => {
      useDropdownClickOutside({
        isOpen: true,
        buttonRef,
        menuRef: nullMenuRef,
        onClose,
      });
      return (
        <div>
          <div ref={buttonRef} data-testid="button">
            Button
          </div>
          <div data-testid="outside">Outside</div>
        </div>
      );
    };

    render(<TestComponent />);
    const outside = screen.getByTestId("outside");
    fireEvent.mouseDown(outside);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
