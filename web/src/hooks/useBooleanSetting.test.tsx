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
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useSettings } from "@/contexts/SettingsContext";
import { useBooleanSetting } from "./useBooleanSetting";

describe("useBooleanSetting", () => {
  let mockGetSetting: ReturnType<typeof vi.fn<(key: string) => string | null>>;
  let mockUpdateSetting: ReturnType<
    typeof vi.fn<(key: string, value: string) => void>
  >;

  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSetting = vi.fn((_key: string) => null);
    mockUpdateSetting = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      isAuthenticated: true,
      getSetting: mockGetSetting,
      updateSetting: mockUpdateSetting,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with default value when setting is not found", async () => {
    mockGetSetting.mockReturnValue(null);

    const { result } = renderHook(() =>
      useBooleanSetting({ key: "test_key", defaultValue: false }),
    );

    await waitFor(() => {
      expect(mockGetSetting).toHaveBeenCalledWith("test_key");
    });

    expect(result.current.value).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });

  it("should load setting value from context when available", async () => {
    mockGetSetting.mockReturnValue("true");

    const { result } = renderHook(() =>
      useBooleanSetting({ key: "test_key", defaultValue: false }),
    );

    await waitFor(() => {
      expect(mockGetSetting).toHaveBeenCalledWith("test_key");
    });

    expect(result.current.value).toBe(true);
  });

  it("should load false when setting is 'false'", async () => {
    mockGetSetting.mockReturnValue("false");

    const { result } = renderHook(() =>
      useBooleanSetting({ key: "test_key", defaultValue: true }),
    );

    await waitFor(() => {
      expect(mockGetSetting).toHaveBeenCalledWith("test_key");
    });

    expect(result.current.value).toBe(false);
  });

  it("should not load when settings are still loading", () => {
    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: true,
      isSaving: false,
      isAuthenticated: true,
      getSetting: mockGetSetting,
      updateSetting: mockUpdateSetting,
    });

    const { result } = renderHook(() =>
      useBooleanSetting({ key: "test_key", defaultValue: false }),
    );

    expect(mockGetSetting).not.toHaveBeenCalled();
    expect(result.current.value).toBe(false);
    expect(result.current.isLoading).toBe(true);
  });

  it("should update value and call updateSetting", () => {
    mockGetSetting.mockReturnValue(null);

    const { result } = renderHook(() =>
      useBooleanSetting({ key: "test_key", defaultValue: false }),
    );

    act(() => {
      result.current.setValue(true);
    });

    expect(result.current.value).toBe(true);
    expect(mockUpdateSetting).toHaveBeenCalledWith("test_key", "true");
  });

  it("should update value to false and call updateSetting with 'false'", () => {
    mockGetSetting.mockReturnValue("true");

    const { result } = renderHook(() =>
      useBooleanSetting({ key: "test_key", defaultValue: false }),
    );

    act(() => {
      result.current.setValue(false);
    });

    expect(result.current.value).toBe(false);
    expect(mockUpdateSetting).toHaveBeenCalledWith("test_key", "false");
  });
});
