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
import { useArraySetting } from "./useArraySetting";

/**
 * Creates a wrapper component with SettingsProvider.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
function createWrapper() {
  return ({ children }: { children: ReactNode }) => (
    <UserProvider>
      <SettingsProvider>{children}</SettingsProvider>
    </UserProvider>
  );
}

describe("useArraySetting", () => {
  let mockSetValue: ReturnType<typeof vi.fn<(value: string[]) => void>>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockSetValue = vi.fn<(value: string[]) => void>();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should load setting value from context when available", async () => {
    const savedArray = ["item1", "item2", "item3"];
    const mockGetSettingForTest = vi.fn((key: string) =>
      key === "test_key" ? JSON.stringify(savedArray) : null,
    );
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue: [],
          value: [],
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    await waitFor(() => {
      expect(mockSetValue).toHaveBeenCalledWith(savedArray);
    });

    expect(mockGetSettingForTest).toHaveBeenCalledWith("test_key");
  });

  it("should use default value when setting is not found", async () => {
    const defaultValue = ["default1", "default2"];
    const mockGetSettingForTest = vi.fn((_key: string) => null);
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue,
          value: [],
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    await waitFor(() => {
      expect(mockGetSettingForTest).toHaveBeenCalledWith("test_key");
    });

    // Should not call setValue when setting is not found (uses default internally)
    expect(mockSetValue).not.toHaveBeenCalled();
  });

  it("should handle invalid JSON and use default value", async () => {
    const defaultValue = ["default"];
    const mockGetSettingForTest = vi.fn((key: string) =>
      key === "test_key" ? "invalid json" : null,
    );
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue,
          value: [],
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    await waitFor(() => {
      expect(mockGetSettingForTest).toHaveBeenCalledWith("test_key");
    });

    // Should call setValue with default when JSON is invalid
    expect(mockSetValue).toHaveBeenCalledWith(defaultValue);
  });

  it("should handle non-array parsed value and use default", async () => {
    const defaultValue = ["default"];
    const mockGetSettingForTest = vi.fn((key: string) =>
      key === "test_key" ? JSON.stringify({ not: "an array" }) : null,
    );
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue,
          value: [],
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    await waitFor(() => {
      expect(mockGetSettingForTest).toHaveBeenCalledWith("test_key");
    });

    // Should not call setValue when parsed value is not an array
    expect(mockSetValue).not.toHaveBeenCalled();
  });

  it("should not load when settings are still loading", () => {
    const mockGetSettingForTest = vi.fn((_key: string) => null);
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: true,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue: [],
          value: [],
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    expect(mockGetSettingForTest).not.toHaveBeenCalled();
    expect(mockSetValue).not.toHaveBeenCalled();
  });

  it("should save changes when value changes after initial load", async () => {
    const initialValue: string[] = [];
    let currentValue = initialValue;
    const mockGetSettingForTest = vi.fn((_key: string) => null);
    const mockUpdateSettingForTest = vi.fn();

    mockSetValue.mockImplementation((newValue: string[]) => {
      currentValue = newValue;
    });

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    const { rerender } = renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue: [],
          value: currentValue,
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    // Wait for initial load to complete
    await waitFor(() => {
      expect(mockGetSettingForTest).toHaveBeenCalled();
    });

    // Wait for setTimeout to complete (marking initial load as done)
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    // Change value
    currentValue = ["new", "items"];
    rerender();

    await waitFor(() => {
      expect(mockUpdateSettingForTest).toHaveBeenCalledWith(
        "test_key",
        JSON.stringify(["new", "items"]),
      );
    });
  });

  it("should not save when value hasn't changed (same array content)", async () => {
    const value = ["item1", "item2"];
    const mockGetSettingForTest = vi.fn((_key: string) => null);
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    const { rerender } = renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue: [],
          value,
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    // Wait for initial load to complete
    await waitFor(() => {
      expect(mockGetSettingForTest).toHaveBeenCalled();
    });

    // Wait for setTimeout to complete
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    // Rerender with same value (different array reference but same content)
    rerender();

    // Should not save because content is the same (sorted comparison)
    expect(mockUpdateSettingForTest).not.toHaveBeenCalled();
  });

  it("should not save during initial load even if value changes", async () => {
    let currentValue: string[] = [];
    const mockGetSettingForTest = vi.fn((_key: string) => null);
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    const { rerender } = renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue: [],
          value: currentValue,
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    // Change value before initial load completes
    currentValue = ["changed"];
    rerender();

    // Wait a bit
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
    });

    // Should not save during initial load
    expect(mockUpdateSettingForTest).not.toHaveBeenCalled();
  });

  it("should not save when settings are loading", async () => {
    const initialValue: string[] = [];
    let currentValue = initialValue;
    const mockGetSettingForTest = vi.fn((_key: string) => null);
    const mockUpdateSettingForTest = vi.fn();

    mockSetValue.mockImplementation((newValue: string[]) => {
      currentValue = newValue;
    });

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    const { rerender } = renderHook(
      () =>
        useArraySetting({
          key: "test_key",
          defaultValue: [],
          value: currentValue,
          setValue: mockSetValue,
        }),
      { wrapper },
    );

    // Wait for initial load to complete
    await waitFor(() => {
      expect(mockGetSettingForTest).toHaveBeenCalled();
    });

    // Wait for setTimeout to complete
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    // Set loading to true
    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: true,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    // Change value
    currentValue = ["new"];
    rerender();

    // Should not save when loading
    expect(mockUpdateSettingForTest).not.toHaveBeenCalled();
  });

  it("should handle array with different order as same value", async () => {
    // Start with an initial value that gets loaded
    const initialValue = ["item1", "item2"];
    const value2 = ["item2", "item1"]; // Same items, different order
    const mockGetSettingForTest = vi.fn((key: string) =>
      key === "test_key" ? JSON.stringify(initialValue) : null,
    );
    const mockUpdateSettingForTest = vi.fn();

    vi.mocked(useSettings).mockReturnValue({
      settings: {},
      isLoading: false,
      isSaving: false,
      getSetting: mockGetSettingForTest,
      updateSetting: mockUpdateSettingForTest,
    });

    const wrapper = createWrapper();
    const { rerender } = renderHook(
      ({ value }) =>
        useArraySetting({
          key: "test_key",
          defaultValue: [],
          value,
          setValue: mockSetValue,
        }),
      { wrapper, initialProps: { value: initialValue } },
    );

    // Wait for initial load to complete
    await waitFor(() => {
      expect(mockGetSettingForTest).toHaveBeenCalled();
    });

    // Wait for setTimeout to complete
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    // Clear any saves from initial load
    mockUpdateSettingForTest.mockClear();

    // Change to value2 (same items, different order)
    rerender({ value: value2 });

    // Wait a bit for the effect to run
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    // Should not save because sorted content is the same
    expect(mockUpdateSettingForTest).not.toHaveBeenCalled();
  });
});
