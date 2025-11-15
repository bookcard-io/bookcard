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
import { describe, expect, it, vi } from "vitest";
import { UserContext, UserProvider } from "@/contexts/UserContext";
import { useLibraryViewMode } from "./useLibraryViewMode";

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserProvider>{children}</UserProvider>
);

describe("useLibraryViewMode", () => {
  it("should initialize with grid view mode", () => {
    const { result } = renderHook(() => useLibraryViewMode(), { wrapper });
    expect(result.current.viewMode).toBe("grid");
  });

  it("should change view mode", () => {
    const { result } = renderHook(() => useLibraryViewMode(), { wrapper });
    act(() => {
      result.current.handleViewModeChange("list");
    });
    expect(result.current.viewMode).toBe("list");
  });

  it("should call onSortToggle when mode is sort", () => {
    const onSortToggle = vi.fn();
    const { result } = renderHook(() => useLibraryViewMode({ onSortToggle }), {
      wrapper,
    });
    act(() => {
      result.current.handleViewModeChange("sort");
    });
    expect(onSortToggle).toHaveBeenCalledTimes(1);
    expect(result.current.viewMode).toBe("grid"); // Should not change
  });

  it("should not call onSortToggle for other modes", () => {
    const onSortToggle = vi.fn();
    const { result } = renderHook(() => useLibraryViewMode({ onSortToggle }), {
      wrapper,
    });
    act(() => {
      result.current.handleViewModeChange("list");
    });
    expect(onSortToggle).not.toHaveBeenCalled();
    expect(result.current.viewMode).toBe("list");
  });

  it("should handle multiple view mode changes", () => {
    const { result } = renderHook(() => useLibraryViewMode(), { wrapper });
    act(() => {
      result.current.handleViewModeChange("list");
    });
    expect(result.current.viewMode).toBe("list");

    act(() => {
      result.current.handleViewModeChange("grid");
    });
    expect(result.current.viewMode).toBe("grid");
  });

  it("should initialize with list view mode from settings", () => {
    const mockGetSetting = vi.fn(() => "list");
    const { result } = renderHook(() => useLibraryViewMode(), {
      wrapper: ({ children }) => (
        <UserContext.Provider
          value={{
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
            getSetting: mockGetSetting,
            updateSetting: vi.fn(),
            defaultDevice: null,
          }}
        >
          {children}
        </UserContext.Provider>
      ),
    });
    expect(result.current.viewMode).toBe("list");
  });

  it("should sync view mode when settings load", () => {
    // When loading, getSetting should return null so it uses default
    const mockGetSettingLoading = vi.fn(() => null);

    // Test with loading state
    const { result: result1 } = renderHook(() => useLibraryViewMode(), {
      wrapper: ({ children }) => (
        <UserContext.Provider
          value={{
            user: null,
            isLoading: true,
            error: null,
            refresh: vi.fn(),
            refreshTimestamp: 0,
            updateUser: vi.fn(),
            profilePictureUrl: null,
            invalidateProfilePictureCache: vi.fn(),
            settings: {},
            isSaving: false,
            getSetting: mockGetSettingLoading,
            updateSetting: vi.fn(),
            defaultDevice: null,
          }}
        >
          {children}
        </UserContext.Provider>
      ),
    });

    // Initially loading, should use default (getSetting returns null)
    expect(result1.current.viewMode).toBe("grid");

    // Test with loaded state - new getSetting function to trigger useEffect
    const mockGetSetting2 = vi.fn(() => "list");
    const { result: result2 } = renderHook(() => useLibraryViewMode(), {
      wrapper: ({ children }) => (
        <UserContext.Provider
          value={{
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
            getSetting: mockGetSetting2,
            updateSetting: vi.fn(),
            defaultDevice: null,
          }}
        >
          {children}
        </UserContext.Provider>
      ),
    });

    // The useEffect should sync the view mode when not loading (lines 74-76)
    expect(result2.current.viewMode).toBe("list");
  });
});
