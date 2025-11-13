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
import { useProfileUpdate } from "./useProfileUpdate";

const wrapper = ({ children }: { children: ReactNode }) => (
  <UserProvider>{children}</UserProvider>
);

describe("useProfileUpdate", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should initialize with isUpdating false and error null", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ settings: {} }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    expect(result.current.isUpdating).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should update profile successfully", async () => {
    const onUpdateSuccess = vi.fn();
    const updatedUser = {
      id: 1,
      username: "newuser",
      email: "new@example.com",
      full_name: "New Name",
      profile_picture: null,
      is_admin: false,
      ereader_devices: [],
    };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(updatedUser),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate({ onUpdateSuccess }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateProfile({
        username: "newuser",
        email: "new@example.com",
        full_name: "New Name",
      });
    });

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(false);
    });

    expect(onUpdateSuccess).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBeNull();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/auth/profile",
      expect.objectContaining({
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: "newuser",
          email: "new@example.com",
          full_name: "New Name",
        }),
        credentials: "include",
      }),
    );
  });

  it("should call onUpdateError when update fails", async () => {
    const onUpdateError = vi.fn();
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Update failed" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate({ onUpdateError }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateProfile({ username: "newuser" });
    });

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(false);
    });

    expect(onUpdateError).toHaveBeenCalledWith("Update failed");
    expect(result.current.error).toBe("Update failed");
  });

  it("should handle fetch error", async () => {
    const onUpdateError = vi.fn();
    const mockFetch = vi.fn().mockRejectedValue(new Error("Network error"));
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate({ onUpdateError }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateProfile({ username: "newuser" });
    });

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(false);
    });

    expect(onUpdateError).toHaveBeenCalledWith("Network error");
    expect(result.current.error).toBe("Network error");
  });

  it("should handle non-Error exception", async () => {
    const onUpdateError = vi.fn();
    const mockFetch = vi.fn().mockRejectedValue("String error");
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate({ onUpdateError }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateProfile({ username: "newuser" });
    });

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(false);
    });

    expect(onUpdateError).toHaveBeenCalledWith("Update failed");
    expect(result.current.error).toBe("Update failed");
  });

  it("should set isUpdating to true during update", async () => {
    let resolveFetch: ((value: unknown) => void) | undefined;
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ settings: {} }),
      })
      .mockImplementationOnce(() => {
        return new Promise((resolve) => {
          resolveFetch = resolve;
        });
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    act(() => {
      void result.current.updateProfile({ username: "newuser" });
    });

    // isUpdating is set synchronously
    expect(result.current.isUpdating).toBe(true);

    if (resolveFetch) {
      resolveFetch({
        ok: true,
        json: vi.fn().mockResolvedValue({
          id: 1,
          username: "newuser",
          email: "test@example.com",
          full_name: null,
          profile_picture: null,
          is_admin: false,
          ereader_devices: [],
        }),
      } as unknown as Response);
    }

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(false);
    });
  });

  it("should clear error on new update", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ id: 1, username: "test" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ settings: {} }),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "First error" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          id: 1,
          username: "newuser",
          email: "test@example.com",
          full_name: null,
          profile_picture: null,
          is_admin: false,
          ereader_devices: [],
        }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    await act(async () => {
      await result.current.updateProfile({ username: "user1" });
    });

    await waitFor(() => {
      expect(result.current.error).toBe("First error");
    });

    await act(async () => {
      await result.current.updateProfile({ username: "user2" });
    });

    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });

  it.each([
    [{ username: "newuser" }, "username"],
    [{ email: "new@example.com" }, "email"],
    [{ full_name: "New Name" }, "full_name"],
    [{ full_name: null }, "full_name"],
    [
      { username: "user", email: "email@example.com", full_name: "Name" },
      "all fields",
    ],
  ])("should update profile with %s", async (payload, _description) => {
    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ settings: {} }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          id: 1,
          username:
            ("username" in payload ? payload.username : undefined) || "test",
          email:
            ("email" in payload ? payload.email : undefined) ||
            "test@example.com",
          full_name:
            ("full_name" in payload ? payload.full_name : undefined) ?? "Test",
          profile_picture: null,
          is_admin: false,
          ereader_devices: [],
        }),
      });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfileUpdate(), { wrapper });

    await waitFor(() => {
      expect(result.current).toBeDefined();
    });

    await act(async () => {
      await result.current.updateProfile(payload);
    });

    await waitFor(() => {
      expect(result.current.isUpdating).toBe(false);
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/auth/profile",
      expect.objectContaining({
        body: JSON.stringify(payload),
      }),
    );
  });
});
