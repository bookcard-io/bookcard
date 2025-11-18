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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useFileUpload } from "./useFileUpload";

describe("useFileUpload", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should upload file successfully", async () => {
    const onUploadStart = vi.fn();
    const onUploadComplete = vi.fn();
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        book_ids: [1, 2],
        task_id: null,
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useFileUpload({ onUploadStart, onUploadComplete }),
    );

    const file = new File(["content"], "book.epub");

    await act(async () => {
      await result.current.uploadFile(file);
    });

    expect(onUploadStart).toHaveBeenCalled();
    expect(onUploadComplete).toHaveBeenCalled();
    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should handle error with detail message", async () => {
    const onSetErrorMessage = vi.fn();
    const onError = vi.fn();
    const mockResponse = {
      ok: false,
      status: 400,
      json: vi.fn().mockResolvedValue({ detail: "Invalid file format" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useFileUpload({ onSetErrorMessage, onError }),
    );

    const file = new File(["content"], "book.epub");

    await act(async () => {
      const response = await result.current.uploadFile(file);
      expect(response).toBeNull();
    });

    expect(onSetErrorMessage).toHaveBeenCalledWith("Invalid file format");
    expect(onError).toHaveBeenCalledWith("Invalid file format");
  });

  it("should handle error without detail message", async () => {
    const onSetErrorMessage = vi.fn();
    const onError = vi.fn();
    const mockResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({}),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useFileUpload({ onSetErrorMessage, onError }),
    );

    const file = new File(["content"], "book.epub");

    await act(async () => {
      const response = await result.current.uploadFile(file);
      expect(response).toBeNull();
    });

    expect(onSetErrorMessage).toHaveBeenCalledWith(
      "Upload failed with status 500",
    );
    expect(onError).toHaveBeenCalledWith("Upload failed with status 500");
  });

  it("should handle error when JSON parsing fails", async () => {
    const onSetErrorMessage = vi.fn();
    const onError = vi.fn();
    const mockResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useFileUpload({ onSetErrorMessage, onError }),
    );

    const file = new File(["content"], "book.epub");

    await act(async () => {
      const response = await result.current.uploadFile(file);
      expect(response).toBeNull();
    });

    // Should use default status-based message when JSON parsing fails
    expect(onSetErrorMessage).toHaveBeenCalledWith(
      "Upload failed with status 500",
    );
    expect(onError).toHaveBeenCalledWith("Upload failed with status 500");
  });

  it("should handle network error", async () => {
    const onSetErrorMessage = vi.fn();
    const onError = vi.fn();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );

    const { result } = renderHook(() =>
      useFileUpload({ onSetErrorMessage, onError }),
    );

    const file = new File(["content"], "book.epub");

    await act(async () => {
      const response = await result.current.uploadFile(file);
      expect(response).toBeNull();
    });

    expect(onSetErrorMessage).toHaveBeenCalledWith("Network error");
    expect(onError).toHaveBeenCalledWith("Network error");
  });

  it("should handle non-Error rejection", async () => {
    const onSetErrorMessage = vi.fn();
    const onError = vi.fn();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      "String error",
    );

    const { result } = renderHook(() =>
      useFileUpload({ onSetErrorMessage, onError }),
    );

    const file = new File(["content"], "book.epub");

    await act(async () => {
      const response = await result.current.uploadFile(file);
      expect(response).toBeNull();
    });

    expect(onSetErrorMessage).toHaveBeenCalledWith("Upload failed");
    expect(onError).toHaveBeenCalledWith("Upload failed");
  });
});
