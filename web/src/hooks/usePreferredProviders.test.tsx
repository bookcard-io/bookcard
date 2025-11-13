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
import { UserProvider } from "@/contexts/UserContext";
import { usePreferredProviders } from "./usePreferredProviders";

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserProvider>{children}</UserProvider>
);

/**
 * Create a mock fetch fixture for UserProvider initialization.
 *
 * Parameters
 * ----------
 * settings : Record<string, unknown>
 *     Optional settings to include in the settings response.
 *
 * Returns
 * -------
 * ReturnType<typeof vi.fn>
 *     Configured mock fetch function.
 */
function createMockFetch(settings: Record<string, unknown> = {}) {
  const mockFetch = vi
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: vi.fn().mockResolvedValue({ settings }),
    });
  vi.stubGlobal("fetch", mockFetch);
  return mockFetch;
}

describe("usePreferredProviders", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should initialize with empty set when no setting exists", async () => {
    createMockFetch();

    const { result } = renderHook(() => usePreferredProviders(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.preferredProviders.size).toBe(0);
    expect(result.current.preferredProviderNames).toEqual([]);
  });

  it("should load preferred providers from setting", async () => {
    createMockFetch({
      preferred_metadata_providers: {
        key: "preferred_metadata_providers",
        value: JSON.stringify(["Google Books", "Amazon"]),
        updated_at: "",
      },
    });

    const { result } = renderHook(() => usePreferredProviders(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.preferredProviders.has("Google Books")).toBe(true);
    expect(result.current.preferredProviders.has("Amazon")).toBe(true);
    expect(result.current.preferredProviderNames).toContain("Google Books");
    expect(result.current.preferredProviderNames).toContain("Amazon");
  });

  it("should handle invalid JSON in setting", async () => {
    createMockFetch({
      preferred_metadata_providers: {
        key: "preferred_metadata_providers",
        value: "invalid json",
        updated_at: "",
      },
    });

    const { result } = renderHook(() => usePreferredProviders(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.preferredProviders.size).toBe(0);
  });

  it("should handle non-array JSON in setting", async () => {
    createMockFetch({
      preferred_metadata_providers: {
        key: "preferred_metadata_providers",
        value: JSON.stringify({ not: "an array" }),
        updated_at: "",
      },
    });

    const { result } = renderHook(() => usePreferredProviders(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.preferredProviders.size).toBe(0);
  });

  it("should toggle provider preferred state", async () => {
    createMockFetch();

    const { result } = renderHook(() => usePreferredProviders(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.togglePreferred("Google Books");
    });

    expect(result.current.preferredProviders.has("Google Books")).toBe(true);
    expect(result.current.preferredProviderNames).toContain("Google Books");

    act(() => {
      result.current.togglePreferred("Google Books");
    });

    expect(result.current.preferredProviders.has("Google Books")).toBe(false);
    expect(result.current.preferredProviderNames).not.toContain("Google Books");
  });

  it("should update setting when toggling provider", async () => {
    createMockFetch();

    const { result } = renderHook(() => usePreferredProviders(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.togglePreferred("Amazon");
    });

    expect(result.current.preferredProviders.has("Amazon")).toBe(true);
  });

  it("should return isLoading true while settings are loading", () => {
    createMockFetch();

    const { result } = renderHook(() => usePreferredProviders(), { wrapper });
    // Initially loading
    expect(result.current.isLoading).toBe(true);
  });
});
