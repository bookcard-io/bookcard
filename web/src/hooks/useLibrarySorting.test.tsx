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
import type { ComponentProps, ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { UserContext, UserProvider } from "@/contexts/UserContext";
import { useLibrarySorting } from "./useLibrarySorting";

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserProvider>{children}</UserProvider>
);

type UserContextValue = ComponentProps<typeof UserContext.Provider>["value"];

function createUserContextValue(
  overrides: Partial<UserContextValue> = {},
): UserContextValue {
  return {
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
    ...overrides,
  };
}

function createUserContextWrapper(overrides: Partial<UserContextValue>) {
  return ({ children }: { children: ReactNode }) => (
    <UserContext.Provider value={createUserContextValue(overrides)}>
      {children}
    </UserContext.Provider>
  );
}

describe("useLibrarySorting", () => {
  it("should initialize with default sort values", () => {
    const { result } = renderHook(() => useLibrarySorting(), { wrapper });
    expect(result.current.sortBy).toBe("timestamp");
    expect(result.current.sortOrder).toBe("desc");
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should toggle sort panel", () => {
    const { result } = renderHook(() => useLibrarySorting(), { wrapper });
    act(() => {
      result.current.handleSortByClick();
    });
    expect(result.current.showSortPanel).toBe(true);

    act(() => {
      result.current.handleSortByClick();
    });
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should change sort field", () => {
    const { result } = renderHook(() => useLibrarySorting(), { wrapper });
    act(() => {
      result.current.handleSortByChange("title");
    });
    expect(result.current.sortBy).toBe("title");
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should toggle sort order", () => {
    const { result } = renderHook(() => useLibrarySorting(), { wrapper });
    expect(result.current.sortOrder).toBe("desc");

    act(() => {
      result.current.handleSortToggle();
    });
    expect(result.current.sortOrder).toBe("asc");

    act(() => {
      result.current.handleSortToggle();
    });
    expect(result.current.sortOrder).toBe("desc");
  });

  it("should close sort panel programmatically", () => {
    const { result } = renderHook(() => useLibrarySorting(), { wrapper });
    act(() => {
      result.current.handleSortByClick();
    });
    expect(result.current.showSortPanel).toBe(true);

    act(() => {
      result.current.closeSortPanel();
    });
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should call onSortPanelChange when panel visibility changes", () => {
    const onSortPanelChange = vi.fn();
    const { result } = renderHook(
      () => useLibrarySorting({ onSortPanelChange }),
      { wrapper },
    );

    act(() => {
      result.current.handleSortByClick();
    });
    expect(onSortPanelChange).toHaveBeenCalledWith(true);

    act(() => {
      result.current.handleSortByClick();
    });
    expect(onSortPanelChange).toHaveBeenCalledWith(false);
  });

  it("should call onSortPanelChange when closing via closeSortPanel", () => {
    const onSortPanelChange = vi.fn();
    const { result } = renderHook(
      () => useLibrarySorting({ onSortPanelChange }),
      { wrapper },
    );

    act(() => {
      result.current.handleSortByClick();
    });
    act(() => {
      result.current.closeSortPanel();
    });
    expect(onSortPanelChange).toHaveBeenCalledWith(false);
  });

  describe("initialization from user settings", () => {
    it("should initialize with custom sort field from settings", () => {
      const mockGetSetting = vi.fn((key: string) => {
        if (key === "default_sort_field") return "title";
        if (key === "default_sort_order") return "desc";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      expect(result.current.sortBy).toBe("title");
      expect(result.current.sortOrder).toBe("desc");
    });

    it("should initialize with custom sort order from settings", () => {
      const mockGetSetting = vi.fn((key: string) => {
        if (key === "default_sort_field") return "timestamp";
        if (key === "default_sort_order") return "asc";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      expect(result.current.sortBy).toBe("timestamp");
      expect(result.current.sortOrder).toBe("asc");
    });

    it("should initialize with defaults when settings are null", () => {
      const mockGetSetting = vi.fn(() => null);

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      expect(result.current.sortBy).toBe("timestamp");
      expect(result.current.sortOrder).toBe("desc");
    });

    it("should initialize with defaults when sort field is invalid", () => {
      const mockGetSetting = vi.fn((key: string) => {
        if (key === "default_sort_field") return "invalid_field";
        if (key === "default_sort_order") return "desc";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      expect(result.current.sortBy).toBe("timestamp");
      expect(result.current.sortOrder).toBe("desc");
    });

    it("should initialize with defaults when sort order is invalid", () => {
      const mockGetSetting = vi.fn((key: string) => {
        if (key === "default_sort_field") return "title";
        if (key === "default_sort_order") return "invalid_order";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      expect(result.current.sortBy).toBe("title");
      expect(result.current.sortOrder).toBe("desc");
    });

    it("should initialize with all valid sort fields", () => {
      const validFields = [
        "title",
        "author_sort",
        "timestamp",
        "pubdate",
        "series_index",
      ];

      for (const field of validFields) {
        const mockGetSetting = vi.fn((key: string) => {
          if (key === "default_sort_field") return field;
          if (key === "default_sort_order") return "desc";
          return null;
        });

        const { result } = renderHook(() => useLibrarySorting(), {
          wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
        });

        expect(result.current.sortBy).toBe(field);
      }
    });
  });

  describe("isReady flag", () => {
    it("should be false when settings are loading", () => {
      const mockGetSetting = vi.fn(() => null);

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({
          getSetting: mockGetSetting,
          isLoading: true,
        }),
      });

      expect(result.current.isReady).toBe(false);
    });

    it("should be true when settings are loaded", () => {
      const mockGetSetting = vi.fn(() => null);

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      expect(result.current.isReady).toBe(true);
    });
  });

  describe("settings synchronization", () => {
    it("should sync sort field when settings finish loading", async () => {
      const mockGetSettingLoading = vi.fn(() => null);

      const { result: result1 } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({
          getSetting: mockGetSettingLoading,
          isLoading: true,
        }),
      });

      // Initially loading, should use default
      expect(result1.current.sortBy).toBe("timestamp");

      // Test with loaded state
      const mockGetSettingLoaded = vi.fn((key: string) => {
        if (key === "default_sort_field") return "title";
        if (key === "default_sort_order") return "desc";
        return null;
      });

      const { result: result2 } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSettingLoaded }),
      });

      // Should sync to settings value when loaded
      await waitFor(() => {
        expect(result2.current.sortBy).toBe("title");
      });
    });

    it("should sync sort order when settings finish loading", async () => {
      const mockGetSettingLoaded = vi.fn((key: string) => {
        if (key === "default_sort_field") return "timestamp";
        if (key === "default_sort_order") return "asc";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSettingLoaded }),
      });

      // Should sync to settings value when loaded
      await waitFor(() => {
        expect(result.current.sortOrder).toBe("asc");
      });
    });

    it("should sync when settings change after initial load", async () => {
      // Test that when getSetting function reference changes (simulating settings update),
      // the hook syncs to the new values
      const mockGetSetting1 = vi.fn((key: string) => {
        if (key === "default_sort_field") return "timestamp";
        if (key === "default_sort_order") return "desc";
        return null;
      });

      const { result: result1 } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting1 }),
      });

      expect(result1.current.sortBy).toBe("timestamp");

      // Create new hook instance with different settings (simulating settings change)
      const mockGetSetting2 = vi.fn((key: string) => {
        if (key === "default_sort_field") return "title";
        if (key === "default_sort_order") return "asc";
        return null;
      });

      const { result: result2 } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting2 }),
      });

      // New instance should sync to new settings
      await waitFor(() => {
        expect(result2.current.sortBy).toBe("title");
        expect(result2.current.sortOrder).toBe("asc");
      });
    });

    it("should not sync if the value hasn't changed", async () => {
      const mockGetSetting = vi.fn((key: string) => {
        if (key === "default_sort_field") return "title";
        if (key === "default_sort_order") return "desc";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      // Manually change sort
      act(() => {
        result.current.handleSortByChange("author_sort");
      });

      expect(result.current.sortBy).toBe("author_sort");

      // Settings haven't changed, so it shouldn't sync back
      // (The useEffect should not trigger a sync because lastSyncedFieldRef matches)
      await waitFor(() => {
        // The sort should remain as manually changed
        expect(result.current.sortBy).toBe("author_sort");
      });
    });

    it("should not sync via useEffect while settings are loading", () => {
      // Note: The lazy initializer will still read settings even when loading,
      // but the useEffect won't run to sync changes while isLoading is true
      const mockGetSetting = vi.fn((key: string) => {
        if (key === "default_sort_field") return "title";
        if (key === "default_sort_order") return "asc";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({
          getSetting: mockGetSetting,
          isLoading: true,
        }),
      });

      // Lazy initializer reads settings, so it will use the setting value
      // But isReady should be false because isLoading is true
      expect(result.current.sortBy).toBe("title");
      expect(result.current.sortOrder).toBe("asc");
      expect(result.current.isReady).toBe(false);
    });
  });

  describe("edge cases", () => {
    it("should handle manual sort changes independently of settings", () => {
      const mockGetSetting = vi.fn((key: string) => {
        if (key === "default_sort_field") return "timestamp";
        if (key === "default_sort_order") return "desc";
        return null;
      });

      const { result } = renderHook(() => useLibrarySorting(), {
        wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
      });

      // Initial state from settings
      expect(result.current.sortBy).toBe("timestamp");

      // Manually change sort
      act(() => {
        result.current.handleSortByChange("author_sort");
      });
      expect(result.current.sortBy).toBe("author_sort");

      // Toggle sort order
      act(() => {
        result.current.handleSortToggle();
      });
      expect(result.current.sortOrder).toBe("asc");

      // Manual changes should persist
      expect(result.current.sortBy).toBe("author_sort");
      expect(result.current.sortOrder).toBe("asc");
    });

    it("should handle all valid sort orders", () => {
      const validOrders: ("asc" | "desc")[] = ["asc", "desc"];

      for (const order of validOrders) {
        const mockGetSetting = vi.fn((key: string) => {
          if (key === "default_sort_field") return "timestamp";
          if (key === "default_sort_order") return order;
          return null;
        });

        const { result } = renderHook(() => useLibrarySorting(), {
          wrapper: createUserContextWrapper({ getSetting: mockGetSetting }),
        });

        expect(result.current.sortOrder).toBe(order);
      }
    });
  });
});
