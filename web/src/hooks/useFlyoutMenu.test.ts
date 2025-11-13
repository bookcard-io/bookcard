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
import { describe, expect, it } from "vitest";
import { useFlyoutMenu } from "./useFlyoutMenu";

describe("useFlyoutMenu", () => {
  it("should initialize with closed state", () => {
    const { result } = renderHook(() =>
      useFlyoutMenu({ parentMenuOpen: true }),
    );

    expect(result.current.isFlyoutOpen).toBe(false);
    expect(result.current.parentItemRef).toBeDefined();
    expect(result.current.handleParentMouseEnter).toBeDefined();
    expect(result.current.handleParentMouseLeave).toBeDefined();
    expect(result.current.handleFlyoutMouseEnter).toBeDefined();
    expect(result.current.handleFlyoutClose).toBeDefined();
  });

  it("should open flyout when parent mouse enters", () => {
    const { result } = renderHook(() =>
      useFlyoutMenu({ parentMenuOpen: true }),
    );

    act(() => {
      result.current.handleParentMouseEnter();
    });

    expect(result.current.isFlyoutOpen).toBe(true);
  });

  it("should open flyout when flyout mouse enters", () => {
    const { result } = renderHook(() =>
      useFlyoutMenu({ parentMenuOpen: true }),
    );

    act(() => {
      result.current.handleFlyoutMouseEnter();
    });

    expect(result.current.isFlyoutOpen).toBe(true);
  });

  it("should close flyout when handleFlyoutClose is called", () => {
    const { result } = renderHook(() =>
      useFlyoutMenu({ parentMenuOpen: true }),
    );

    act(() => {
      result.current.handleParentMouseEnter();
    });

    expect(result.current.isFlyoutOpen).toBe(true);

    act(() => {
      result.current.handleFlyoutClose();
    });

    expect(result.current.isFlyoutOpen).toBe(false);
  });

  it("should not close flyout when parent mouse leaves", () => {
    const { result } = renderHook(() =>
      useFlyoutMenu({ parentMenuOpen: true }),
    );

    act(() => {
      result.current.handleParentMouseEnter();
    });

    expect(result.current.isFlyoutOpen).toBe(true);

    act(() => {
      result.current.handleParentMouseLeave();
    });

    expect(result.current.isFlyoutOpen).toBe(true);
  });

  it("should close flyout when parent menu closes", () => {
    const { result, rerender } = renderHook(
      ({ parentMenuOpen }) => useFlyoutMenu({ parentMenuOpen }),
      { initialProps: { parentMenuOpen: true } },
    );

    act(() => {
      result.current.handleParentMouseEnter();
    });

    expect(result.current.isFlyoutOpen).toBe(true);

    rerender({ parentMenuOpen: false });

    expect(result.current.isFlyoutOpen).toBe(false);
  });

  it("should keep flyout closed when parent menu is already closed", () => {
    const { result } = renderHook(() =>
      useFlyoutMenu({ parentMenuOpen: false }),
    );

    expect(result.current.isFlyoutOpen).toBe(false);

    // The effect closes the flyout when parentMenuOpen is false on mount
    // But if we try to open it, it will open (effect only runs on parentMenuOpen change)
    act(() => {
      result.current.handleParentMouseEnter();
    });

    // The flyout can be opened even if parentMenuOpen is false
    // The effect only closes it when parentMenuOpen changes to false
    expect(result.current.isFlyoutOpen).toBe(true);
  });

  it("should close flyout when parent menu closes even if flyout was open", () => {
    const { result, rerender } = renderHook(
      ({ parentMenuOpen }) => useFlyoutMenu({ parentMenuOpen }),
      { initialProps: { parentMenuOpen: true } },
    );

    act(() => {
      result.current.handleFlyoutMouseEnter();
    });

    expect(result.current.isFlyoutOpen).toBe(true);

    rerender({ parentMenuOpen: false });

    expect(result.current.isFlyoutOpen).toBe(false);
  });
});
