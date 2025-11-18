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

vi.mock("@/contexts/UserContext", () => ({
  useUser: vi.fn(),
}));

import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useUser } from "@/contexts/UserContext";
import { usePermission } from "./usePermission";

describe("usePermission", () => {
  it("should return hasPermission false when loading", () => {
    vi.mocked(useUser).mockReturnValue({
      canPerformAction: vi.fn(() => true),
      isLoading: true,
    } as unknown as ReturnType<typeof useUser>);

    const { result } = renderHook(() =>
      usePermission({ resource: "books", action: "read" }),
    );

    expect(result.current.hasPermission).toBe(false);
    expect(result.current.isLoading).toBe(true);
  });

  it("should return hasPermission based on canPerformAction when not loading", () => {
    const canPerformAction = vi.fn(() => true);
    vi.mocked(useUser).mockReturnValue({
      canPerformAction,
      isLoading: false,
    } as unknown as ReturnType<typeof useUser>);

    const { result } = renderHook(() =>
      usePermission({ resource: "books", action: "read" }),
    );

    expect(result.current.hasPermission).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(canPerformAction).toHaveBeenCalledWith("books", "read", undefined);
  });

  it("should pass resourceData to canPerformAction", () => {
    const canPerformAction = vi.fn(() => false);
    const resourceData = { authors: ["Author 1"] };
    vi.mocked(useUser).mockReturnValue({
      canPerformAction,
      isLoading: false,
    } as unknown as ReturnType<typeof useUser>);

    const { result } = renderHook(() =>
      usePermission({
        resource: "books",
        action: "write",
        resourceData,
      }),
    );

    expect(result.current.hasPermission).toBe(false);
    expect(canPerformAction).toHaveBeenCalledWith(
      "books",
      "write",
      resourceData,
    );
  });

  it("should update when resource changes", () => {
    const canPerformAction = vi
      .fn()
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(false);
    vi.mocked(useUser).mockReturnValue({
      canPerformAction,
      isLoading: false,
    } as unknown as ReturnType<typeof useUser>);

    const { result, rerender } = renderHook(
      ({ resource }) => usePermission({ resource, action: "read" }),
      { initialProps: { resource: "books" } },
    );

    expect(result.current.hasPermission).toBe(true);

    rerender({ resource: "shelves" });

    expect(result.current.hasPermission).toBe(false);
    expect(canPerformAction).toHaveBeenCalledWith("shelves", "read", undefined);
  });

  it("should update when action changes", () => {
    const canPerformAction = vi
      .fn()
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(false);
    vi.mocked(useUser).mockReturnValue({
      canPerformAction,
      isLoading: false,
    } as unknown as ReturnType<typeof useUser>);

    const { result, rerender } = renderHook(
      ({ action }) => usePermission({ resource: "books", action }),
      { initialProps: { action: "read" } },
    );

    expect(result.current.hasPermission).toBe(true);

    rerender({ action: "write" });

    expect(result.current.hasPermission).toBe(false);
    expect(canPerformAction).toHaveBeenCalledWith("books", "write", undefined);
  });

  it("should update when resourceData changes", () => {
    const canPerformAction = vi.fn(() => true);
    vi.mocked(useUser).mockReturnValue({
      canPerformAction,
      isLoading: false,
    } as unknown as ReturnType<typeof useUser>);

    const { rerender } = renderHook(
      ({ resourceData }) =>
        usePermission({
          resource: "books",
          action: "write",
          resourceData,
        }),
      { initialProps: { resourceData: { authors: ["Author 1"] } } },
    );

    expect(canPerformAction).toHaveBeenCalledWith("books", "write", {
      authors: ["Author 1"],
    });

    rerender({ resourceData: { authors: ["Author 2"] } });

    expect(canPerformAction).toHaveBeenCalledWith("books", "write", {
      authors: ["Author 2"],
    });
  });
});
