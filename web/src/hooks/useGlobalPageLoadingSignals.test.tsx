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

vi.mock("@/contexts/ShelvesContext", () => ({
  useShelvesContext: vi.fn(),
}));

vi.mock("@/contexts/LibraryLoadingContext", () => ({
  useLibraryLoading: vi.fn(),
}));

import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useLibraryLoading } from "@/contexts/LibraryLoadingContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useUser } from "@/contexts/UserContext";
import { useGlobalPageLoadingSignals } from "./useGlobalPageLoadingSignals";

describe("useGlobalPageLoadingSignals", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return false when all loading signals are false", () => {
    vi.mocked(useUser).mockReturnValue({
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
      getSetting: vi.fn(),
      updateSetting: vi.fn(),
      defaultDevice: null,
    });

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    vi.mocked(useLibraryLoading).mockReturnValue({
      isBooksLoading: false,
      incrementBooksLoading: vi.fn(),
      decrementBooksLoading: vi.fn(),
    });

    const { result } = renderHook(() => useGlobalPageLoadingSignals(false));

    expect(result.current).toBe(false);
  });

  it("should return true when isUserLoading is true", () => {
    vi.mocked(useUser).mockReturnValue({
      user: null,
      isLoading: true,
      error: null,
      refresh: vi.fn(),
      refreshTimestamp: 0,
      updateUser: vi.fn(),
      profilePictureUrl: null,
      invalidateProfilePictureCache: vi.fn(),
      settings: {},
      isSaving: false,
      getSetting: vi.fn(),
      updateSetting: vi.fn(),
      defaultDevice: null,
    });

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    vi.mocked(useLibraryLoading).mockReturnValue({
      isBooksLoading: false,
      incrementBooksLoading: vi.fn(),
      decrementBooksLoading: vi.fn(),
    });

    const { result } = renderHook(() => useGlobalPageLoadingSignals(false));

    expect(result.current).toBe(true);
  });

  it("should return true when isShelvesLoading is true", () => {
    vi.mocked(useUser).mockReturnValue({
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
      getSetting: vi.fn(),
      updateSetting: vi.fn(),
      defaultDevice: null,
    });

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: true,
      error: null,
      refresh: vi.fn(),
    });

    vi.mocked(useLibraryLoading).mockReturnValue({
      isBooksLoading: false,
      incrementBooksLoading: vi.fn(),
      decrementBooksLoading: vi.fn(),
    });

    const { result } = renderHook(() => useGlobalPageLoadingSignals(false));

    expect(result.current).toBe(true);
  });

  it("should return true when isBooksLoading is true", () => {
    vi.mocked(useUser).mockReturnValue({
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
      getSetting: vi.fn(),
      updateSetting: vi.fn(),
      defaultDevice: null,
    });

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    vi.mocked(useLibraryLoading).mockReturnValue({
      isBooksLoading: true,
      incrementBooksLoading: vi.fn(),
      decrementBooksLoading: vi.fn(),
    });

    const { result } = renderHook(() => useGlobalPageLoadingSignals(false));

    expect(result.current).toBe(true);
  });

  it("should return true when isNavTransition is true", () => {
    vi.mocked(useUser).mockReturnValue({
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
      getSetting: vi.fn(),
      updateSetting: vi.fn(),
      defaultDevice: null,
    });

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    vi.mocked(useLibraryLoading).mockReturnValue({
      isBooksLoading: false,
      incrementBooksLoading: vi.fn(),
      decrementBooksLoading: vi.fn(),
    });

    const { result } = renderHook(() => useGlobalPageLoadingSignals(true));

    expect(result.current).toBe(true);
  });

  it("should return true when multiple loading signals are true", () => {
    vi.mocked(useUser).mockReturnValue({
      user: null,
      isLoading: true,
      error: null,
      refresh: vi.fn(),
      refreshTimestamp: 0,
      updateUser: vi.fn(),
      profilePictureUrl: null,
      invalidateProfilePictureCache: vi.fn(),
      settings: {},
      isSaving: false,
      getSetting: vi.fn(),
      updateSetting: vi.fn(),
      defaultDevice: null,
    });

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: true,
      error: null,
      refresh: vi.fn(),
    });

    vi.mocked(useLibraryLoading).mockReturnValue({
      isBooksLoading: true,
      incrementBooksLoading: vi.fn(),
      decrementBooksLoading: vi.fn(),
    });

    const { result } = renderHook(() => useGlobalPageLoadingSignals(true));

    expect(result.current).toBe(true);
  });
});
