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

import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ProviderStatus } from "./useMetadataSearchStream";
import { useProviderItems } from "./useProviderItems";

/**
 * Create a test fixture for useProviderItems hook.
 *
 * Parameters
 * ----------
 * providerStatuses : Map<string, ProviderStatus>
 *     Map of provider statuses.
 * enabledProviders : Set<string>
 *     Set of enabled provider names.
 * preferredProviders : Set<string>
 *     Set of preferred provider names.
 *
 * Returns
 * -------
 * ReturnType<typeof renderHook>
 *     Render hook result with result and rerender.
 */
function renderProviderItems(
  providerStatuses: Map<string, ProviderStatus>,
  enabledProviders: Set<string>,
  preferredProviders: Set<string>,
) {
  return renderHook(() =>
    useProviderItems({
      providerStatuses,
      enabledProviders,
      preferredProviders,
    }),
  );
}

describe("useProviderItems", () => {
  it("should return empty array when no providers are enabled", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set<string>();
    const preferredProviders = new Set<string>();

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current).toEqual([]);
  });

  it("should return only enabled providers", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books", "Amazon"]);
    const preferredProviders = new Set<string>();

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current).toHaveLength(2);
    expect(result.current.map((item) => item.name)).toContain("Google Books");
    expect(result.current.map((item) => item.name)).toContain("Amazon");
  });

  it("should use default pending status when provider status not found", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books"]);
    const preferredProviders = new Set<string>();

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current).toHaveLength(1);
    expect(result.current[0]?.status.status).toBe("pending");
    expect(result.current[0]?.status.resultCount).toBe(0);
    expect(result.current[0]?.status.discovered).toBe(0);
  });

  it("should use provider status when found", () => {
    const providerStatus: ProviderStatus = {
      id: "google-books",
      name: "Google Books",
      status: "completed",
      resultCount: 5,
      discovered: 10,
    };
    const providerStatuses = new Map([["google-books", providerStatus]]);
    const enabledProviders = new Set(["Google Books"]);
    const preferredProviders = new Set<string>();

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current).toHaveLength(1);
    expect(result.current[0]?.status).toEqual(providerStatus);
  });

  it("should set enabled to true for enabled providers", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books"]);
    const preferredProviders = new Set<string>();

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current[0]?.enabled).toBe(true);
  });

  it("should set preferred to true for preferred providers", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books"]);
    const preferredProviders = new Set(["Google Books"]);

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current[0]?.preferred).toBe(true);
  });

  it("should set preferred to false for non-preferred providers", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books"]);
    const preferredProviders = new Set<string>();

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current[0]?.preferred).toBe(false);
  });

  it("should find provider status by name", () => {
    const providerStatus: ProviderStatus = {
      id: "amazon",
      name: "Amazon",
      status: "searching",
      resultCount: 3,
      discovered: 5,
    };
    const providerStatuses = new Map([["amazon", providerStatus]]);
    const enabledProviders = new Set(["Amazon"]);
    const preferredProviders = new Set<string>();

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current).toHaveLength(1);
    expect(result.current[0]?.status.name).toBe("Amazon");
    expect(result.current[0]?.status.status).toBe("searching");
  });

  it("should handle multiple enabled providers", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books", "Amazon"]);
    const preferredProviders = new Set(["Google Books"]);

    const { result } = renderProviderItems(
      providerStatuses,
      enabledProviders,
      preferredProviders,
    );

    expect(result.current).toHaveLength(2);
    expect(
      result.current.find((item) => item.name === "Google Books")?.preferred,
    ).toBe(true);
    expect(
      result.current.find((item) => item.name === "Amazon")?.preferred,
    ).toBe(false);
  });

  it("should update when providerStatuses changes", () => {
    const providerStatuses1 = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books"]);
    const preferredProviders = new Set<string>();

    const { result, rerender } = renderHook(
      ({ providerStatuses }) =>
        useProviderItems({
          providerStatuses,
          enabledProviders,
          preferredProviders,
        }),
      { initialProps: { providerStatuses: providerStatuses1 } },
    );

    expect(result.current[0]?.status.status).toBe("pending");

    const providerStatus: ProviderStatus = {
      id: "google-books",
      name: "Google Books",
      status: "completed",
      resultCount: 10,
      discovered: 20,
    };
    const providerStatuses2 = new Map([["google-books", providerStatus]]);

    rerender({ providerStatuses: providerStatuses2 });

    expect(result.current[0]?.status.status).toBe("completed");
    expect(result.current[0]?.status.resultCount).toBe(10);
  });

  it("should update when enabledProviders changes", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders1 = new Set(["Google Books"]);
    const preferredProviders = new Set<string>();

    const { result, rerender } = renderHook(
      ({ enabledProviders }) =>
        useProviderItems({
          providerStatuses,
          enabledProviders,
          preferredProviders,
        }),
      { initialProps: { enabledProviders: enabledProviders1 } },
    );

    expect(result.current).toHaveLength(1);

    const enabledProviders2 = new Set(["Google Books", "Amazon"]);
    rerender({ enabledProviders: enabledProviders2 });

    expect(result.current).toHaveLength(2);
  });

  it("should update when preferredProviders changes", () => {
    const providerStatuses = new Map<string, ProviderStatus>();
    const enabledProviders = new Set(["Google Books"]);
    const preferredProviders1 = new Set<string>();

    const { result, rerender } = renderHook(
      ({ preferredProviders }) =>
        useProviderItems({
          providerStatuses,
          enabledProviders,
          preferredProviders,
        }),
      { initialProps: { preferredProviders: preferredProviders1 } },
    );

    expect(result.current[0]?.preferred).toBe(false);

    const preferredProviders2 = new Set(["Google Books"]);
    rerender({ preferredProviders: preferredProviders2 });

    expect(result.current[0]?.preferred).toBe(true);
  });
});
