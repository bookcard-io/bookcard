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

import { fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useClickOutside } from "./useClickOutside";

describe("useClickOutside", () => {
  let handler: () => void;

  beforeEach(() => {
    handler = vi.fn() as () => void;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return a ref", () => {
    const { result } = renderHook(() => useClickOutside(handler));
    expect(result.current).toBeDefined();
    expect(result.current.current).toBeNull();
  });

  it("should call handler when clicking outside element", () => {
    const TestComponent = () => {
      const ref = useClickOutside(handler);
      return (
        <div>
          <div ref={ref} data-testid="inside">
            Inside
          </div>
          <div data-testid="outside">Outside</div>
        </div>
      );
    };

    render(<TestComponent />);
    const outside = screen.getByTestId("outside");
    fireEvent.mouseDown(outside);
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("should not call handler when clicking inside element", () => {
    const TestComponent = () => {
      const ref = useClickOutside(handler);
      return (
        <div ref={ref} data-testid="inside">
          Inside
        </div>
      );
    };

    render(<TestComponent />);
    const inside = screen.getByTestId("inside");
    fireEvent.mouseDown(inside);
    expect(handler).not.toHaveBeenCalled();
  });

  it("should not call handler when disabled", () => {
    const TestComponent = () => {
      const ref = useClickOutside(handler, false);
      return (
        <div>
          <div ref={ref} data-testid="inside">
            Inside
          </div>
          <div data-testid="outside">Outside</div>
        </div>
      );
    };

    render(<TestComponent />);
    const outside = screen.getByTestId("outside");
    fireEvent.mouseDown(outside);
    expect(handler).not.toHaveBeenCalled();
  });

  it("should use default enabled value of true", () => {
    const TestComponent = () => {
      const ref = useClickOutside(handler);
      return (
        <div>
          <div ref={ref} data-testid="inside">
            Inside
          </div>
          <div data-testid="outside">Outside</div>
        </div>
      );
    };

    render(<TestComponent />);
    const outside = screen.getByTestId("outside");
    fireEvent.mouseDown(outside);
    expect(handler).toHaveBeenCalled();
  });

  it("should handle ref type correctly", () => {
    const { result } = renderHook(() =>
      useClickOutside<HTMLButtonElement>(handler),
    );
    expect(result.current).toBeDefined();
  });
});
