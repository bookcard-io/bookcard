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

import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { THEME_PREFERENCE_SETTING_KEY } from "@/components/profile/config/configurationConstants";
import { UserContext } from "@/contexts/UserContext";
import { useTheme } from "./useTheme";

type UserContextValue = NonNullable<
  React.ComponentProps<typeof UserContext.Provider>["value"]
>;

/**
 * Creates a wrapper component with UserContext.
 *
 * Parameters
 * ----------
 * mockContext : Partial<UserContextValue>
 *     Mock context values.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
function createWrapper(mockContext: Partial<UserContextValue> = {}) {
  const defaultContext: UserContextValue = {
    user: null,
    isLoading: false,
    error: null,
    refresh: vi.fn(),
    refreshTimestamp: 0,
    updateUser: vi.fn(),
    profilePictureUrl: null,
    invalidateProfilePictureCache: vi.fn(),
    settings: {},
    isSaving: false,
    getSetting: vi.fn(() => null),
    updateSetting: vi.fn(),
    defaultDevice: null,
    hasPermission: vi.fn(() => false),
    canPerformAction: vi.fn(() => false),
    ...mockContext,
  };

  return ({ children }: { children: ReactNode }) => (
    <UserContext.Provider value={defaultContext}>
      {children}
    </UserContext.Provider>
  );
}

describe("useTheme", () => {
  let mockLocalStorage: Record<string, string>;
  let mockGetItem: ReturnType<typeof vi.fn>;
  let mockSetItem: ReturnType<typeof vi.fn>;
  let setAttributeSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    mockLocalStorage = {};
    mockGetItem = vi.fn((key: string) => mockLocalStorage[key] ?? null);
    mockSetItem = vi.fn((key: string, value: string) => {
      mockLocalStorage[key] = value;
    });

    vi.stubGlobal("localStorage", {
      getItem: mockGetItem,
      setItem: mockSetItem,
      removeItem: vi.fn(),
      clear: vi.fn(() => {
        mockLocalStorage = {};
      }),
    });

    // Spy on the real document.documentElement.setAttribute instead of stubbing document
    setAttributeSpy = vi.spyOn(document.documentElement, "setAttribute");
  });

  afterEach(() => {
    setAttributeSpy.mockRestore();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should initialize with default theme when localStorage is empty", () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe("dark");
    expect(setAttributeSpy).toHaveBeenCalledWith("data-theme", "dark");
  });

  it("should initialize with theme from localStorage after hydration", async () => {
    mockLocalStorage["theme-preference"] = "light";

    const { result } = renderHook(() => useTheme());

    // In SSR, initial render is "dark" (default), then syncs from localStorage after hydration
    // In test environment, effects may run synchronously, so we verify the end state
    await waitFor(() => {
      expect(result.current.theme).toBe("light");
    });
    expect(setAttributeSpy).toHaveBeenCalledWith("data-theme", "light");
  });

  it("should handle invalid theme value in localStorage", async () => {
    mockLocalStorage["theme-preference"] = "invalid";

    const { result } = renderHook(() => useTheme());

    // Should remain default theme even after hydration
    await waitFor(() => {
      expect(result.current.theme).toBe("dark");
    });
  });

  it("should handle localStorage.getItem error", async () => {
    mockGetItem.mockImplementation(() => {
      throw new Error("Storage error");
    });

    const { result } = renderHook(() => useTheme());

    // Should remain default theme even after hydration attempt
    await waitFor(() => {
      expect(result.current.theme).toBe("dark");
    });
  });

  it("should load theme from UserContext when available", async () => {
    const mockGetSetting = vi.fn(() => "light");
    const wrapper = createWrapper({
      isLoading: false,
      getSetting: mockGetSetting,
    });

    const { result } = renderHook(() => useTheme(), { wrapper });

    // Wait for hydration, then UserContext sync
    await waitFor(() => {
      expect(result.current.theme).toBe("light");
    });

    expect(mockGetSetting).toHaveBeenCalledWith(THEME_PREFERENCE_SETTING_KEY);
    expect(setAttributeSpy).toHaveBeenCalledWith("data-theme", "light");
  });

  it("should not update theme when UserContext theme matches current theme", async () => {
    mockLocalStorage["theme-preference"] = "dark";
    const mockGetSetting = vi.fn(() => "dark");
    const wrapper = createWrapper({
      isLoading: false,
      getSetting: mockGetSetting,
    });

    const { result } = renderHook(() => useTheme(), { wrapper });

    // Wait for hydration and UserContext sync
    await waitFor(() => {
      expect(result.current.theme).toBe("dark");
    });

    const initialCallCount = setAttributeSpy.mock.calls.length;

    // Trigger effect again - wait for any potential updates
    await waitFor(() => {
      expect(setAttributeSpy).toHaveBeenCalledTimes(initialCallCount);
    });
  });

  it("should sync localStorage to backend when backend has no theme", async () => {
    mockLocalStorage["theme-preference"] = "light";
    const mockGetSetting = vi.fn(() => null);
    const mockUpdateSetting = vi.fn();
    const wrapper = createWrapper({
      isLoading: false,
      getSetting: mockGetSetting,
      updateSetting: mockUpdateSetting,
    });

    renderHook(() => useTheme(), { wrapper });

    // Wait for hydration, then UserContext sync
    await waitFor(() => {
      expect(mockUpdateSetting).toHaveBeenCalledWith(
        THEME_PREFERENCE_SETTING_KEY,
        "light",
      );
    });
  });

  it("should not sync when localStorage is empty", async () => {
    const mockGetSetting = vi.fn(() => null);
    const mockUpdateSetting = vi.fn();
    const wrapper = createWrapper({
      isLoading: false,
      getSetting: mockGetSetting,
      updateSetting: mockUpdateSetting,
    });

    renderHook(() => useTheme(), { wrapper });

    await waitFor(() => {
      expect(mockUpdateSetting).not.toHaveBeenCalled();
    });
  });

  it("should toggle theme from dark to light", () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe("dark");

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe("light");
    expect(mockSetItem).toHaveBeenCalledWith("theme-preference", "light");
    expect(setAttributeSpy).toHaveBeenCalledWith("data-theme", "light");
  });

  it("should toggle theme from light to dark", async () => {
    mockLocalStorage["theme-preference"] = "light";
    const { result } = renderHook(() => useTheme());

    // Wait for hydration to sync from localStorage
    await waitFor(() => {
      expect(result.current.theme).toBe("light");
    });

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe("dark");
    expect(mockSetItem).toHaveBeenCalledWith("theme-preference", "dark");
  });

  it("should sync toggle to backend when UserContext is available", () => {
    const mockUpdateSetting = vi.fn();
    const wrapper = createWrapper({
      isLoading: false,
      updateSetting: mockUpdateSetting,
    });

    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => {
      result.current.toggleTheme();
    });

    expect(mockUpdateSetting).toHaveBeenCalledWith(
      THEME_PREFERENCE_SETTING_KEY,
      "light",
    );
  });

  it("should not sync toggle when UserContext is not available", () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe("light");
    expect(mockSetItem).toHaveBeenCalledWith("theme-preference", "light");
  });

  it("should handle localStorage.setItem error when toggling", () => {
    mockSetItem.mockImplementation(() => {
      throw new Error("Storage error");
    });

    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe("light");
  });

  it("should return isLoading from UserContext when available", () => {
    const wrapper = createWrapper({
      isLoading: true,
    });

    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.isLoading).toBe(true);
  });

  it("should return isLoading false when UserContext is not available", () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.isLoading).toBe(false);
  });

  it("should update document attribute when theme changes", () => {
    const { result } = renderHook(() => useTheme());

    expect(setAttributeSpy).toHaveBeenCalledWith("data-theme", "dark");

    act(() => {
      result.current.toggleTheme();
    });

    expect(setAttributeSpy).toHaveBeenCalledWith("data-theme", "light");
  });

  it("should handle invalid theme from UserContext", async () => {
    mockLocalStorage["theme-preference"] = "dark";
    const mockGetSetting = vi.fn(() => "invalid");
    const wrapper = createWrapper({
      isLoading: false,
      getSetting: mockGetSetting,
    });

    const { result } = renderHook(() => useTheme(), { wrapper });

    // Wait for hydration to sync from localStorage, then UserContext check
    await waitFor(() => {
      expect(result.current.theme).toBe("dark");
    });
  });
});
