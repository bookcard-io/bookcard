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
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mockPush, usePathname } from "@/__mocks__/next-navigation";
import { SelectedShelfProvider } from "@/contexts/SelectedShelfContext";
import { useSidebarNavigation } from "./useSidebarNavigation";

/**
 * Creates a wrapper component with SelectedShelfProvider.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Child components to wrap.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
function createWrapper() {
  return ({ children }: { children: ReactNode }) => (
    <SelectedShelfProvider>{children}</SelectedShelfProvider>
  );
}

describe("useSidebarNavigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(usePathname).mockReturnValue("/");
    document.body.innerHTML = "";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should return all navigation functions and isAdminActive", () => {
    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    expect(result.current.navigateHome).toBeDefined();
    expect(result.current.navigateToShelves).toBeDefined();
    expect(result.current.navigateToAdmin).toBeDefined();
    expect(result.current.navigateToManageDevices).toBeDefined();
    expect(result.current.isAdminActive).toBe(false);
  });

  it("should set isAdminActive to true when pathname is /admin", () => {
    vi.mocked(usePathname).mockReturnValue("/admin");

    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isAdminActive).toBe(true);
  });

  it("should navigate to home and clear selected shelf", () => {
    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateHome();
    });

    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("should navigate to shelves tab", () => {
    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateToShelves();
    });

    expect(mockPush).toHaveBeenCalledWith("/?tab=shelves");
  });

  it("should navigate to admin page", () => {
    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateToAdmin();
    });

    expect(mockPush).toHaveBeenCalledWith("/admin");
  });

  it("should scroll to manage-devices when already on profile page", () => {
    vi.mocked(usePathname).mockReturnValue("/profile");
    const mockElement = document.createElement("div");
    mockElement.id = "manage-devices";
    document.body.appendChild(mockElement);
    const scrollIntoViewSpy = vi.spyOn(mockElement, "scrollIntoView");

    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateToManageDevices();
    });

    expect(scrollIntoViewSpy).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("should navigate to profile and scroll to manage-devices when not on profile page", async () => {
    vi.mocked(usePathname).mockReturnValue("/");
    const mockElement = document.createElement("div");
    mockElement.id = "manage-devices";
    const scrollIntoViewSpy = vi.spyOn(mockElement, "scrollIntoView");

    // Mock setInterval to execute immediately
    const originalSetInterval = window.setInterval;
    const intervalCalls: Array<() => void> = [];
    vi.spyOn(window, "setInterval").mockImplementation((fn) => {
      intervalCalls.push(fn as () => void);
      return 1 as unknown as NodeJS.Timeout;
    });

    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateToManageDevices();
    });

    expect(mockPush).toHaveBeenCalledWith("/profile#manage-devices");

    // Simulate element appearing after navigation
    document.body.appendChild(mockElement);

    // Execute the interval callback
    act(() => {
      intervalCalls.forEach((fn) => {
        fn();
      });
    });

    expect(scrollIntoViewSpy).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });

    vi.spyOn(window, "setInterval").mockImplementation(originalSetInterval);
  });

  it("should stop trying to scroll after max attempts", async () => {
    vi.mocked(usePathname).mockReturnValue("/");
    const getElementByIdSpy = vi.spyOn(document, "getElementById");

    // Mock setInterval to track calls
    const intervalCalls: Array<() => void> = [];
    const clearIntervalSpy = vi.spyOn(window, "clearInterval");
    vi.spyOn(window, "setInterval").mockImplementation((fn) => {
      intervalCalls.push(fn as () => void);
      return 1 as unknown as NodeJS.Timeout;
    });

    getElementByIdSpy.mockReturnValue(null);

    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateToManageDevices();
    });

    expect(mockPush).toHaveBeenCalledWith("/profile#manage-devices");

    // Execute interval callbacks 20 times (maxAttempts)
    act(() => {
      for (let i = 0; i < 20; i++) {
        intervalCalls.forEach((fn) => {
          fn();
        });
      }
    });

    expect(getElementByIdSpy).toHaveBeenCalledTimes(20);
    expect(clearIntervalSpy).toHaveBeenCalled();
  });

  it("should handle navigateToManageDevices when on profile page without element", () => {
    vi.mocked(usePathname).mockReturnValue("/profile");
    const getElementByIdSpy = vi.spyOn(document, "getElementById");
    getElementByIdSpy.mockReturnValue(null);

    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateToManageDevices();
    });

    // Should attempt to find the element but not navigate
    expect(getElementByIdSpy).toHaveBeenCalledWith("manage-devices");
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("should return false from scrollToManageDevices when element is not found", () => {
    vi.mocked(usePathname).mockReturnValue("/profile");
    const getElementByIdSpy = vi.spyOn(document, "getElementById");
    getElementByIdSpy.mockReturnValue(null);

    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateToManageDevices();
    });

    expect(getElementByIdSpy).toHaveBeenCalledWith("manage-devices");
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("should handle multiple navigation calls", () => {
    const { result } = renderHook(() => useSidebarNavigation(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.navigateHome();
      result.current.navigateToShelves();
      result.current.navigateToAdmin();
    });

    expect(mockPush).toHaveBeenCalledTimes(3);
    expect(mockPush).toHaveBeenNthCalledWith(1, "/");
    expect(mockPush).toHaveBeenNthCalledWith(2, "/?tab=shelves");
    expect(mockPush).toHaveBeenNthCalledWith(3, "/admin");
  });
});
