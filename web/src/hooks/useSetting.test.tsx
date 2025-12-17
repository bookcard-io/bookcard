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

import { vi } from "vitest";

vi.mock("@/contexts/SettingsContext", async () => {
  const actual = await vi.importActual<
    typeof import("@/contexts/SettingsContext")
  >("@/contexts/SettingsContext");
  return {
    ...actual,
    useSettings: vi.fn(),
  };
});

import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { SettingsProvider, useSettings } from "@/contexts/SettingsContext";
import { UserProvider } from "@/contexts/UserContext";
import { useSetting } from "./useSetting";

/**
 * Creates a wrapper component with SettingsProvider.
 *
 * Parameters
 * ----------
 * mockSettings : Record<string, string>
 *     Mock settings to provide.
 * isLoading : boolean
 *     Loading state.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
function createWrapper(
  mockSettings: Record<string, string> = {},
  isLoading: boolean = false,
) {
  const mockGetSetting = vi.fn((key: string) => mockSettings[key] ?? null);
  const mockUpdateSetting = vi.fn();

  vi.mocked(useSettings).mockReturnValue({
    settings: Object.fromEntries(
      Object.entries(mockSettings).map(([key, value]) => [
        key,
        { key, value, updated_at: "" },
      ]),
    ),
    isLoading,
    isSaving: false,
    isAuthenticated: true,
    getSetting: mockGetSetting,
    updateSetting: mockUpdateSetting,
  });

  return ({ children }: { children: ReactNode }) => (
    <UserProvider>
      <SettingsProvider>{children}</SettingsProvider>
    </UserProvider>
  );
}

describe("useSetting", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with default value when setting is not found", async () => {
    const wrapper = createWrapper({}, false);
    const { result } = renderHook(
      () => useSetting({ key: "test_key", defaultValue: "default" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.value).toBe("default");
  });

  it("should load setting value from context when available", async () => {
    const wrapper = createWrapper({ test_key: "saved_value" }, false);
    const { result } = renderHook(
      () => useSetting({ key: "test_key", defaultValue: "default" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.value).toBe("saved_value");
  });

  it("should use default value when settings are still loading", () => {
    const wrapper = createWrapper({}, true);
    const { result } = renderHook(
      () => useSetting({ key: "test_key", defaultValue: "default" }),
      { wrapper },
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.value).toBe("default");
  });

  it("should update setting value and call updateSetting", async () => {
    const mockUpdateSetting = vi.fn();
    const mockGetSetting = vi.fn(() => null);

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      isAuthenticated: true,
      getSetting: mockGetSetting,
      updateSetting: mockUpdateSetting,
    });

    const wrapper = ({ children }: { children: ReactNode }) => (
      <UserProvider>
        <SettingsProvider>{children}</SettingsProvider>
      </UserProvider>
    );

    const { result } = renderHook(
      () => useSetting({ key: "test_key", defaultValue: "default" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setValue("new_value");
    });

    expect(result.current.value).toBe("new_value");
    expect(mockUpdateSetting).toHaveBeenCalledWith("test_key", "new_value");
  });

  it("should update value when setting changes in context", async () => {
    const mockUpdateSetting = vi.fn();
    let callCount = 0;
    const mockGetSetting = vi.fn(() => {
      callCount++;
      return callCount === 1 ? "initial" : "updated";
    });

    vi.mocked(useSettings).mockReturnValue({
      settings: {
        test_key: {
          key: "test_key",
          value: callCount === 1 ? "initial" : "updated",
          updated_at: "",
        },
      },
      isLoading: false,
      isSaving: false,
      isAuthenticated: true,
      getSetting: mockGetSetting,
      updateSetting: mockUpdateSetting,
    });

    const wrapper = ({ children }: { children: ReactNode }) => (
      <UserProvider>
        <SettingsProvider>{children}</SettingsProvider>
      </UserProvider>
    );

    const { result, rerender } = renderHook(
      () => useSetting({ key: "test_key", defaultValue: "default" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.value).toBe("initial");
    });

    // Create a new getSetting function with a different reference to trigger the effect
    const mockGetSetting2 = vi.fn(() => "updated");
    vi.mocked(useSettings).mockReturnValue({
      settings: {
        test_key: { key: "test_key", value: "updated", updated_at: "" },
      },
      isLoading: false,
      isSaving: false,
      isAuthenticated: true,
      getSetting: mockGetSetting2,
      updateSetting: mockUpdateSetting,
    });

    // Trigger a re-render with the new mock (new getSetting function reference)
    rerender();

    await waitFor(() => {
      expect(result.current.value).toBe("updated");
    });
  });

  it("should not update value when setting is not found in context", async () => {
    const wrapper = createWrapper({}, false);
    const { result } = renderHook(
      () => useSetting({ key: "test_key", defaultValue: "default" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.value).toBe("default");
  });
});
