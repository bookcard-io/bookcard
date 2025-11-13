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
import { useProfilePictureUpload } from "./useProfilePictureUpload";

vi.mock("./useFileDropzone", () => ({
  useFileDropzone: vi.fn(),
}));

import { useFileDropzone } from "./useFileDropzone";

describe("useProfilePictureUpload", () => {
  let mockFileDropzone: ReturnType<typeof useFileDropzone>;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    mockFileDropzone = {
      fileInputRef: { current: null },
      isDragging: false,
      accept:
        "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
      openFileBrowser: vi.fn(),
      dragHandlers: {
        onDragEnter: vi.fn(),
        onDragOver: vi.fn(),
        onDragLeave: vi.fn(),
        onDrop: vi.fn(),
      },
      handleFileChange: vi.fn(),
      handleClick: vi.fn(),
      handleKeyDown: vi.fn(),
    };
    (useFileDropzone as ReturnType<typeof vi.fn>).mockReturnValue(
      mockFileDropzone,
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should initialize with isUploading false", () => {
    const { result } = renderHook(() => useProfilePictureUpload());
    expect(result.current.isUploading).toBe(false);
  });

  it("should return useFileDropzone properties", () => {
    const { result } = renderHook(() => useProfilePictureUpload());
    expect(result.current.fileInputRef).toBe(mockFileDropzone.fileInputRef);
    expect(result.current.isDragging).toBe(false);
    expect(result.current.accept).toBe(
      "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
    );
  });

  it("should call useFileDropzone with correct options", () => {
    const onFileSelect = vi.fn();
    renderHook(() =>
      useProfilePictureUpload({ onUploadSuccess: onFileSelect }),
    );

    expect(useFileDropzone).toHaveBeenCalledWith({
      onFileSelect: expect.any(Function),
      accept:
        "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
      filterImages: true,
    });
  });

  it("should validate file size and reject files over 5MB", async () => {
    const onUploadError = vi.fn();
    const largeFile = new File(["x".repeat(6 * 1024 * 1024)], "large.jpg", {
      type: "image/jpeg",
    });

    renderHook(() => useProfilePictureUpload({ onUploadError }));

    // Extract the onFileSelect callback from the mock call
    const mockCall = (useFileDropzone as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const onFileSelect = mockCall?.[0]?.onFileSelect;

    expect(onFileSelect).toBeDefined();

    if (onFileSelect) {
      await act(async () => {
        await onFileSelect(largeFile);
      });

      expect(onUploadError).toHaveBeenCalledWith(
        "File size must be less than 5MB",
      );
    }
  });

  it("should upload file successfully", async () => {
    const onUploadSuccess = vi.fn();
    const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureUpload({ onUploadSuccess }),
    );

    const mockCall = (useFileDropzone as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const onFileSelect = mockCall?.[0]?.onFileSelect;

    expect(onFileSelect).toBeDefined();

    if (onFileSelect) {
      await act(async () => {
        await onFileSelect(file);
      });

      await waitFor(() => {
        expect(result.current.isUploading).toBe(false);
      });

      expect(onUploadSuccess).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/auth/profile-picture",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
          credentials: "include",
        }),
      );
    }
  });

  it("should call onUploadError when upload fails", async () => {
    const onUploadError = vi.fn();
    const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Upload failed" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureUpload({ onUploadError }),
    );

    const mockCall = (useFileDropzone as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const onFileSelect = mockCall?.[0]?.onFileSelect;

    expect(onFileSelect).toBeDefined();

    if (onFileSelect) {
      await act(async () => {
        await onFileSelect(file);
      });

      await waitFor(() => {
        expect(result.current.isUploading).toBe(false);
      });

      expect(onUploadError).toHaveBeenCalledWith("Upload failed");
    }
  });

  it("should handle fetch error", async () => {
    const onUploadError = vi.fn();
    const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const mockFetch = vi.fn().mockRejectedValue(new Error("Network error"));
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureUpload({ onUploadError }),
    );

    const mockCall = (useFileDropzone as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const onFileSelect = mockCall?.[0]?.onFileSelect;

    expect(onFileSelect).toBeDefined();

    if (onFileSelect) {
      await act(async () => {
        await onFileSelect(file);
      });

      await waitFor(() => {
        expect(result.current.isUploading).toBe(false);
      });

      expect(onUploadError).toHaveBeenCalledWith("Network error");
    }
  });

  it("should handle non-Error exception", async () => {
    const onUploadError = vi.fn();
    const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
    const mockFetch = vi.fn().mockRejectedValue("String error");
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() =>
      useProfilePictureUpload({ onUploadError }),
    );

    const mockCall = (useFileDropzone as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const onFileSelect = mockCall?.[0]?.onFileSelect;

    expect(onFileSelect).toBeDefined();

    if (onFileSelect) {
      await act(async () => {
        await onFileSelect(file);
      });

      await waitFor(() => {
        expect(result.current.isUploading).toBe(false);
      });

      expect(onUploadError).toHaveBeenCalledWith("Upload failed");
    }
  });

  it("should set isUploading to true during upload", async () => {
    const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
    let resolveFetch: ((value: unknown) => void) | undefined;
    const mockFetch = vi.fn().mockImplementation(() => {
      return new Promise((resolve) => {
        resolveFetch = resolve;
      });
    });
    vi.stubGlobal("fetch", mockFetch);

    const { result } = renderHook(() => useProfilePictureUpload());

    const mockCall = (useFileDropzone as ReturnType<typeof vi.fn>).mock
      .calls[0];
    const onFileSelect = mockCall?.[0]?.onFileSelect;

    expect(onFileSelect).toBeDefined();

    if (onFileSelect) {
      act(() => {
        void onFileSelect(file);
      });

      // Wait for isUploading to be set to true
      await waitFor(() => {
        expect(result.current.isUploading).toBe(true);
      });

      if (resolveFetch) {
        resolveFetch({
          ok: true,
          json: vi.fn().mockResolvedValue({}),
        } as unknown as Response);
      }

      await waitFor(() => {
        expect(result.current.isUploading).toBe(false);
      });
    }
  });
});
