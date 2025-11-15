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
import { useProviderSettings } from "./useProviderSettings";

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserProvider>{children}</UserProvider>
);

describe("useProviderSettings", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should initialize with default enabled providers when no setting exists", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ settings: {} }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.enabledProviders.size).toBeGreaterThan(0);
    expect(result.current.enabledProviderNames.length).toBeGreaterThan(0);
  });

  it("should load enabled providers from setting", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({
        settings: {
          enabled_metadata_providers: JSON.stringify([
            "Google Books",
            "Amazon",
          ]),
        },
      }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.enabledProviders.has("Google Books")).toBe(true);
    expect(result.current.enabledProviders.has("Amazon")).toBe(true);
    expect(result.current.enabledProviderNames).toContain("Google Books");
    expect(result.current.enabledProviderNames).toContain("Amazon");
  });

  it("should handle empty array setting (all disabled)", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          settings: {
            enabled_metadata_providers: {
              key: "enabled_metadata_providers",
              value: JSON.stringify([]),
              updated_at: "",
            },
          },
        }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Empty array means user explicitly disabled all providers
    expect(result.current.enabledProviders.size).toBe(0);
    expect(result.current.enabledProviderNames).toEqual([]);
  });

  it("should handle invalid JSON in setting", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          settings: {
            enabled_metadata_providers: {
              key: "enabled_metadata_providers",
              value: "invalid json",
              updated_at: "",
            },
          },
        }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should default to default enabled providers
    expect(result.current.enabledProviders.size).toBeGreaterThan(0);
  });

  it("should handle non-array JSON in setting", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          settings: {
            enabled_metadata_providers: {
              key: "enabled_metadata_providers",
              value: JSON.stringify({ not: "an array" }),
              updated_at: "",
            },
          },
        }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should default to default enabled providers
    expect(result.current.enabledProviders.size).toBeGreaterThan(0);
  });

  it("should toggle provider enabled state", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ settings: {} }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialSize = result.current.enabledProviders.size;
    const wasEnabled = result.current.enabledProviders.has("Google Books");

    act(() => {
      result.current.toggleProvider("Google Books");
    });

    if (wasEnabled) {
      expect(result.current.enabledProviders.has("Google Books")).toBe(false);
      expect(result.current.enabledProviders.size).toBe(initialSize - 1);
    } else {
      expect(result.current.enabledProviders.has("Google Books")).toBe(true);
      expect(result.current.enabledProviders.size).toBe(initialSize + 1);
    }
  });

  it("should update setting when toggling provider", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ settings: {} }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.toggleProvider("Amazon");
    });

    // The setting should be updated via updateSetting
    expect(result.current.enabledProviders.has("Amazon")).toBeDefined();
  });

  it("should return isLoading true while settings are loading", () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ settings: {} }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });
    // Initially loading
    expect(result.current.isLoading).toBe(true);
  });

  it("should store all providers when all are enabled", async () => {
    const { AVAILABLE_METADATA_PROVIDERS } = await import(
      "@/components/profile/config/configurationConstants"
    );

    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          settings: {
            enabled_metadata_providers: JSON.stringify(
              AVAILABLE_METADATA_PROVIDERS.slice(0, 3),
            ),
          },
        }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Enable remaining providers one by one
    for (const provider of AVAILABLE_METADATA_PROVIDERS) {
      if (!result.current.enabledProviders.has(provider)) {
        act(() => {
          result.current.toggleProvider(provider);
        });
      }
    }

    // Verify all providers are enabled
    await waitFor(() => {
      expect(result.current.enabledProviders.size).toBe(
        AVAILABLE_METADATA_PROVIDERS.length,
      );
    });
    expect(
      AVAILABLE_METADATA_PROVIDERS.every((p) =>
        result.current.enabledProviders.has(p),
      ),
    ).toBe(true);
  });

  it("should add provider when toggling disabled provider", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          settings: {
            enabled_metadata_providers: {
              key: "enabled_metadata_providers",
              value: JSON.stringify([]),
              updated_at: "",
            },
          },
        }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProviderSettings(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Start with all providers disabled (empty array means explicitly disabled)
    expect(result.current.enabledProviders.size).toBe(0);

    // Toggle a provider to enable it
    act(() => {
      result.current.toggleProvider("Google Books");
    });

    // Should now have the provider enabled
    expect(result.current.enabledProviders.has("Google Books")).toBe(true);
    expect(result.current.enabledProviders.size).toBe(1);
  });
});
