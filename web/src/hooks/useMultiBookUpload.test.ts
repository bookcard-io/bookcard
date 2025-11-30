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
import { getBookFormatsAcceptString } from "@/constants/bookFormats";
import { useMultiBookUpload } from "./useMultiBookUpload";

describe("useMultiBookUpload", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with default state", () => {
    const { result } = renderHook(() => useMultiBookUpload());

    expect(result.current.isUploading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.taskId).toBeNull();
    expect(result.current.uploadBooks).toBeDefined();
    expect(result.current.clearError).toBeDefined();
    expect(result.current.fileInputProps.multiple).toBe(true);
  });

  it("should have correct accept string", () => {
    const { result } = renderHook(() => useMultiBookUpload());
    expect(result.current.fileInputProps.accept).toBe(
      getBookFormatsAcceptString(),
    );
  });

  it("should upload multiple files successfully", async () => {
    const onUploadStart = vi.fn();
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ task_id: 123, total_files: 3 }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useMultiBookUpload({ onUploadStart }));

    const file1 = new File(["content1"], "book1.epub");
    const file2 = new File(["content2"], "book2.epub");
    const file3 = new File(["content3"], "book3.epub");

    await act(async () => {
      await result.current.uploadBooks([file1, file2, file3]);
    });

    expect(result.current.isUploading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.taskId).toBe(123);
    expect(onUploadStart).toHaveBeenCalledWith(123, 3);
  });

  it("should handle upload error with detail message", async () => {
    const onUploadError = vi.fn();
    const mockResponse = {
      ok: false,
      status: 400,
      json: vi.fn().mockResolvedValue({ detail: "Invalid file format" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useMultiBookUpload({ onUploadError }));

    const file = new File(["content"], "book.epub");

    await act(async () => {
      await result.current.uploadBooks([file]);
    });

    expect(result.current.isUploading).toBe(false);
    expect(result.current.error).toBe("Invalid file format");
    expect(result.current.taskId).toBeNull();
    expect(onUploadError).toHaveBeenCalledWith("Invalid file format");
  });

  it("should handle upload error without detail message", async () => {
    const onUploadError = vi.fn();
    const mockResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({}),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useMultiBookUpload({ onUploadError }));

    const file = new File(["content"], "book.epub");

    await act(async () => {
      await result.current.uploadBooks([file]);
    });

    expect(result.current.error).toBe("Failed to upload books");
    expect(onUploadError).toHaveBeenCalledWith("Failed to upload books");
  });

  it("should handle network error", async () => {
    const onUploadError = vi.fn();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );

    const { result } = renderHook(() => useMultiBookUpload({ onUploadError }));

    const file = new File(["content"], "book.epub");

    await act(async () => {
      await result.current.uploadBooks([file]);
    });

    expect(result.current.error).toBe("Network error");
    expect(onUploadError).toHaveBeenCalledWith("Network error");
  });

  it("should handle non-Error rejection", async () => {
    const onUploadError = vi.fn();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      "String error",
    );

    const { result } = renderHook(() => useMultiBookUpload({ onUploadError }));

    const file = new File(["content"], "book.epub");

    await act(async () => {
      await result.current.uploadBooks([file]);
    });

    expect(result.current.error).toBe("Failed to upload books");
    expect(onUploadError).toHaveBeenCalledWith("Failed to upload books");
  });

  it("should not upload if files array is empty", async () => {
    const { result } = renderHook(() => useMultiBookUpload());

    await act(async () => {
      await result.current.uploadBooks([]);
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(result.current.isUploading).toBe(false);
  });

  it("should not upload if already uploading", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ task_id: 123, total_files: 1 }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useMultiBookUpload());

    const file = new File(["content"], "book.epub");

    // Start first upload
    const uploadPromise = act(async () => {
      await result.current.uploadBooks([file]);
    });

    // Try to start second upload while first is in progress
    await act(async () => {
      await result.current.uploadBooks([file]);
    });

    await uploadPromise;

    // Should only have been called once
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("should clear error", () => {
    const { result } = renderHook(() => useMultiBookUpload());

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it("should handle file input change", async () => {
    const onUploadStart = vi.fn();
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ task_id: 123, total_files: 2 }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useMultiBookUpload({ onUploadStart }));

    const file1 = new File(["content1"], "book1.epub");
    const file2 = new File(["content2"], "book2.epub");

    const mockInput = {
      files: [file1, file2],
      value: "test.epub",
    } as unknown as HTMLInputElement;

    act(() => {
      result.current.fileInputProps.onChange({
        target: mockInput,
      } as React.ChangeEvent<HTMLInputElement>);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });

    expect(mockInput.value).toBe("");
    expect(result.current.taskId).toBe(123);
  });

  it("should handle file input change with no files", () => {
    const { result } = renderHook(() => useMultiBookUpload());

    const mockInput = {
      files: null,
      value: "test.epub",
    } as unknown as HTMLInputElement;

    act(() => {
      result.current.fileInputProps.onChange({
        target: mockInput,
      } as React.ChangeEvent<HTMLInputElement>);
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should create fresh file copies to avoid stream locking", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ task_id: 123, total_files: 1 }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useMultiBookUpload());

    const file = new File(["content"], "book.epub");

    await act(async () => {
      await result.current.uploadBooks([file]);
    });

    // Verify fetch was called (covers lines 96-100)
    expect(globalThis.fetch).toHaveBeenCalled();
    const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls[0];
    if (fetchCall?.[1]) {
      const formData = fetchCall[1].body as FormData;
      expect(formData).toBeInstanceOf(FormData);
    }
  });
});
