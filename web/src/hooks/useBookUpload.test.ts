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
import { useBookUpload } from "./useBookUpload";

describe("useBookUpload", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with isUploading false", () => {
    const { result } = renderHook(() => useBookUpload());

    expect(result.current.isUploading).toBe(false);
    expect(result.current.fileInputRef.current).toBeNull();
  });

  it("should have correct accept string", () => {
    const { result } = renderHook(() => useBookUpload());

    expect(result.current.accept).toBe(
      ".epub,.mobi,.azw,.azw3,.azw4,.cbz,.cbr,.cb7,.cbc,.chm,.djvu,.docx,.fb2,.fbz,.html,.htmlz,.kepub,.lit,.lrf,.odt,.pdf,.prc,.pdb,.pml,.rb,.rtf,.snb,.tcr,.txt,.txtz",
    );
  });

  it("should open file browser when openFileBrowser is called", () => {
    const { result } = renderHook(() => useBookUpload());

    const mockClick = vi.fn();
    const mockInput = {
      click: mockClick,
    } as unknown as HTMLInputElement;

    result.current.fileInputRef.current = mockInput;

    act(() => {
      result.current.openFileBrowser();
    });

    expect(mockClick).toHaveBeenCalled();
  });

  it("should not throw when openFileBrowser is called with null ref", () => {
    const { result } = renderHook(() => useBookUpload());

    expect(result.current.fileInputRef.current).toBeNull();

    act(() => {
      result.current.openFileBrowser();
    });

    // Should not throw
    expect(true).toBe(true);
  });

  it("should handle file change and upload successfully", async () => {
    const onUploadSuccess = vi.fn();
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ book_id: 123 }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBookUpload({ onUploadSuccess }));

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
    });
    const mockInput = {
      value: "",
    } as unknown as HTMLInputElement;

    result.current.fileInputRef.current = mockInput;

    const changeEvent = {
      target: {
        files: [file],
        value: "",
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    await act(async () => {
      result.current.handleFileChange(changeEvent);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
      expect(globalThis.fetch).toHaveBeenCalled();
      expect(onUploadSuccess).toHaveBeenCalledWith(123);
      expect(mockInput.value).toBe("");
    });
  });

  it("should handle file change without file", () => {
    const { result } = renderHook(() => useBookUpload());

    const changeEvent = {
      target: {
        files: null,
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileChange(changeEvent);
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
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

    const { result } = renderHook(() => useBookUpload({ onUploadError }));

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
    });

    const changeEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    await act(async () => {
      result.current.handleFileChange(changeEvent);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
      expect(onUploadError).toHaveBeenCalledWith("Invalid file format");
    });
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

    const { result } = renderHook(() => useBookUpload({ onUploadError }));

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
    });

    const changeEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    await act(async () => {
      result.current.handleFileChange(changeEvent);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
      expect(onUploadError).toHaveBeenCalledWith(
        "Upload failed with status 500",
      );
    });
  });

  it("should handle upload error with Error instance", async () => {
    const onUploadError = vi.fn();
    const error = new Error("Network error");
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const { result } = renderHook(() => useBookUpload({ onUploadError }));

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
    });

    const changeEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileChange(changeEvent);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });

    expect(onUploadError).toHaveBeenCalledWith("Network error");
  });

  it("should handle upload error with non-Error value", async () => {
    const onUploadError = vi.fn();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      "String error",
    );

    const { result } = renderHook(() => useBookUpload({ onUploadError }));

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
    });

    const changeEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileChange(changeEvent);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });

    expect(onUploadError).toHaveBeenCalledWith("Upload failed");
  });

  it("should set isUploading to true during upload", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ book_id: 123 }),
    };
    let resolveFetch: () => void;
    const fetchPromise = new Promise<typeof mockResponse>((resolve) => {
      resolveFetch = () => resolve(mockResponse);
    });
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockReturnValue(
      fetchPromise,
    );

    const { result } = renderHook(() => useBookUpload());

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
    });

    const changeEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileChange(changeEvent);
    });

    // Check isUploading is true
    expect(result.current.isUploading).toBe(true);

    // Resolve the promise
    await act(async () => {
      resolveFetch?.();
      await fetchPromise;
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });
  });

  it("should not call callbacks when not provided", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ book_id: 123 }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBookUpload());

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
    });

    const changeEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileChange(changeEvent);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });

    // Should not throw and fetch should be called
    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should create fresh file copy to avoid stream locking", async () => {
    const onUploadSuccess = vi.fn();
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ book_id: 123 }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBookUpload({ onUploadSuccess }));

    const file = new File(["content"], "test.epub", {
      type: "application/epub+zip",
      lastModified: 1234567890,
    });

    const changeEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleFileChange(changeEvent);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });

    // Verify FormData was created with the file
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/books/upload",
      expect.objectContaining({
        method: "POST",
        body: expect.any(FormData),
      }),
    );

    const fetchCall = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls[0];
    if (fetchCall && fetchCall.length > 1 && fetchCall[1]) {
      const formData = fetchCall[1].body as FormData;
      const formDataFile = formData.get("file") as File;

      expect(formDataFile).toBeInstanceOf(File);
      expect(formDataFile.name).toBe("test.epub");
      expect(formDataFile.type).toBe("application/epub+zip");
      expect(formDataFile.lastModified).toBe(1234567890);
    }
  });
});
