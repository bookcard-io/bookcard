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

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useExclusiveFlyoutMenus } from "./useExclusiveFlyoutMenus";

describe("useExclusiveFlyoutMenus", () => {
  const createMockFlyout = (isOpen: boolean) => ({
    isFlyoutOpen: isOpen,
    handleFlyoutClose: vi.fn(),
    handleParentMouseEnter: vi.fn(),
    parentItemRef: { current: null },
    handleParentMouseLeave: vi.fn(),
    handleFlyoutMouseEnter: vi.fn(),
  });

  it("should return wrapped handlers", () => {
    const firstFlyout = createMockFlyout(false);
    const secondFlyout = createMockFlyout(false);

    const { result } = renderHook(() =>
      useExclusiveFlyoutMenus(firstFlyout, secondFlyout),
    );

    expect(result.current.handleFirstMouseEnter).toBeDefined();
    expect(result.current.handleSecondMouseEnter).toBeDefined();
  });

  it("should close second flyout when opening first", () => {
    const firstFlyout = createMockFlyout(false);
    const secondFlyout = createMockFlyout(true);

    const { result } = renderHook(() =>
      useExclusiveFlyoutMenus(firstFlyout, secondFlyout),
    );

    act(() => {
      result.current.handleFirstMouseEnter();
    });

    expect(secondFlyout.handleFlyoutClose).toHaveBeenCalledTimes(1);
    expect(firstFlyout.handleParentMouseEnter).toHaveBeenCalledTimes(1);
  });

  it("should not close second flyout if it's already closed", () => {
    const firstFlyout = createMockFlyout(false);
    const secondFlyout = createMockFlyout(false);

    const { result } = renderHook(() =>
      useExclusiveFlyoutMenus(firstFlyout, secondFlyout),
    );

    act(() => {
      result.current.handleFirstMouseEnter();
    });

    expect(secondFlyout.handleFlyoutClose).not.toHaveBeenCalled();
    expect(firstFlyout.handleParentMouseEnter).toHaveBeenCalledTimes(1);
  });

  it("should close first flyout when opening second", () => {
    const firstFlyout = createMockFlyout(true);
    const secondFlyout = createMockFlyout(false);

    const { result } = renderHook(() =>
      useExclusiveFlyoutMenus(firstFlyout, secondFlyout),
    );

    act(() => {
      result.current.handleSecondMouseEnter();
    });

    expect(firstFlyout.handleFlyoutClose).toHaveBeenCalledTimes(1);
    expect(secondFlyout.handleParentMouseEnter).toHaveBeenCalledTimes(1);
  });

  it("should not close first flyout if it's already closed", () => {
    const firstFlyout = createMockFlyout(false);
    const secondFlyout = createMockFlyout(false);

    const { result } = renderHook(() =>
      useExclusiveFlyoutMenus(firstFlyout, secondFlyout),
    );

    act(() => {
      result.current.handleSecondMouseEnter();
    });

    expect(firstFlyout.handleFlyoutClose).not.toHaveBeenCalled();
    expect(secondFlyout.handleParentMouseEnter).toHaveBeenCalledTimes(1);
  });

  it("should update when flyout states change", () => {
    const firstFlyout = createMockFlyout(false);
    const secondFlyout = createMockFlyout(false);

    const { result, rerender } = renderHook(
      ({ first, second }) => useExclusiveFlyoutMenus(first, second),
      { initialProps: { first: firstFlyout, second: secondFlyout } },
    );

    // Update second flyout to be open
    const updatedSecondFlyout = {
      ...secondFlyout,
      isFlyoutOpen: true,
    };

    rerender({ first: firstFlyout, second: updatedSecondFlyout });

    act(() => {
      result.current.handleFirstMouseEnter();
    });

    expect(updatedSecondFlyout.handleFlyoutClose).toHaveBeenCalledTimes(1);
    expect(firstFlyout.handleParentMouseEnter).toHaveBeenCalledTimes(1);
  });
});
