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

import { act, renderHook } from "@testing-library/react";
import React, { type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GlobalMessageProvider } from "@/contexts/GlobalMessageContext";
import { useBookRating } from "./useBookRating";

vi.mock("@/services/bookService", () => ({
  updateBookRating: vi.fn(),
}));

const wrapper = ({ children }: { children: ReactNode }) =>
  React.createElement(GlobalMessageProvider, null, children);

import * as bookService from "@/services/bookService";

describe("useBookRating", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should update rating successfully", async () => {
    const onOptimisticUpdate = vi.fn();
    vi.mocked(bookService.updateBookRating).mockResolvedValue(undefined);

    const { result } = renderHook(() => useBookRating({ onOptimisticUpdate }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateRating(123, 5);
    });

    expect(onOptimisticUpdate).toHaveBeenCalledWith(123, 5);
    expect(bookService.updateBookRating).toHaveBeenCalledWith(123, 5);
  });

  it("should handle rating update error with onError callback", async () => {
    const onOptimisticUpdate = vi.fn();
    const onError = vi.fn();
    const error = new Error("Failed to update rating");
    vi.mocked(bookService.updateBookRating).mockRejectedValue(error);

    const { result } = renderHook(
      () => useBookRating({ onOptimisticUpdate, onError }),
      { wrapper },
    );

    await act(async () => {
      await result.current.updateRating(123, 4);
    });

    expect(onOptimisticUpdate).toHaveBeenCalledWith(123, 4);
    expect(onError).toHaveBeenCalledWith(error);
  });

  it("should handle rating update error without onError callback", async () => {
    const onOptimisticUpdate = vi.fn();
    const error = new Error("Failed to update rating");
    vi.mocked(bookService.updateBookRating).mockRejectedValue(error);

    const { result } = renderHook(() => useBookRating({ onOptimisticUpdate }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateRating(123, 3);
    });

    expect(onOptimisticUpdate).toHaveBeenCalledWith(123, 3);
    // showDanger should be called (covered by global message system)
  });

  it("should handle non-Error rejection", async () => {
    const onOptimisticUpdate = vi.fn();
    vi.mocked(bookService.updateBookRating).mockRejectedValue("String error");

    const { result } = renderHook(() => useBookRating({ onOptimisticUpdate }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateRating(123, null);
    });

    expect(onOptimisticUpdate).toHaveBeenCalledWith(123, null);
  });

  it("should set rating to null", async () => {
    const onOptimisticUpdate = vi.fn();
    vi.mocked(bookService.updateBookRating).mockResolvedValue(undefined);

    const { result } = renderHook(() => useBookRating({ onOptimisticUpdate }), {
      wrapper,
    });

    await act(async () => {
      await result.current.updateRating(123, null);
    });

    expect(onOptimisticUpdate).toHaveBeenCalledWith(123, null);
    expect(bookService.updateBookRating).toHaveBeenCalledWith(123, null);
  });
});
