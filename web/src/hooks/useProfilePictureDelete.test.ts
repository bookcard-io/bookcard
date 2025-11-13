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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useProfilePictureDelete } from "./useProfilePictureDelete";

describe("useProfilePictureDelete", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should initialize with isDeleting false", () => {
    const { result } = renderHook(() => useProfilePictureDelete());
    expect(result.current.isDeleting).toBe(false);
  });

  it("should set isDeleting to true during delete", async () => {
    let resolveFetch: ((value: unknown) => void) | undefined;
    const mockFetch = vi.fn().mockImplementation(() => {
      return new Promise((resolve) => {
        resolveFetch = resolve;
      });
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfilePictureDelete());

    act(() => {
      void result.current.deleteProfilePicture();
    });

    // isDeleting is set synchronously
    expect(result.current.isDeleting).toBe(true);

    if (resolveFetch) {
      resolveFetch({
        ok: true,
        json: vi.fn().mockResolvedValue({}),
      } as unknown as Response);
    }

    await waitFor(() => {
      expect(result.current.isDeleting).toBe(false);
    });
  });

  it("should call onDeleteSuccess when delete succeeds", async () => {
    const onDeleteSuccess = vi.fn();
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureDelete({ onDeleteSuccess }),
    );

    await act(async () => {
      await result.current.deleteProfilePicture();
    });

    expect(onDeleteSuccess).toHaveBeenCalledTimes(1);
    expect(result.current.isDeleting).toBe(false);
  });

  it("should call onDeleteError when delete fails", async () => {
    const onDeleteError = vi.fn();
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Delete failed" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureDelete({ onDeleteError }),
    );

    await act(async () => {
      await result.current.deleteProfilePicture();
    });

    expect(onDeleteError).toHaveBeenCalledWith("Delete failed");
    expect(result.current.isDeleting).toBe(false);
  });

  it("should call onDeleteError with default message when response has no detail", async () => {
    const onDeleteError = vi.fn();
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureDelete({ onDeleteError }),
    );

    await act(async () => {
      await result.current.deleteProfilePicture();
    });

    expect(onDeleteError).toHaveBeenCalledWith(
      "Failed to delete profile picture",
    );
  });

  it("should handle fetch error", async () => {
    const onDeleteError = vi.fn();
    const mockFetch = vi.fn().mockRejectedValue(new Error("Network error"));
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureDelete({ onDeleteError }),
    );

    await act(async () => {
      await result.current.deleteProfilePicture();
    });

    expect(onDeleteError).toHaveBeenCalledWith("Network error");
    expect(result.current.isDeleting).toBe(false);
  });

  it("should handle non-Error exception", async () => {
    const onDeleteError = vi.fn();
    const mockFetch = vi.fn().mockRejectedValue("String error");
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureDelete({ onDeleteError }),
    );

    await act(async () => {
      await result.current.deleteProfilePicture();
    });

    expect(onDeleteError).toHaveBeenCalledWith(
      "Failed to delete profile picture",
    );
  });

  it("should make DELETE request to correct endpoint", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfilePictureDelete());

    await act(async () => {
      await result.current.deleteProfilePicture();
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/auth/profile-picture",
      expect.objectContaining({
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      }),
    );
  });
});
