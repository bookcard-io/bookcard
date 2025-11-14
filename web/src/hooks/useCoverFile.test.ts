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
import { useCoverFile } from "./useCoverFile";

vi.mock("@/utils/imageValidation", () => ({
  validateImageFile: vi.fn(),
}));

import { validateImageFile } from "@/utils/imageValidation";

// Mock URL.createObjectURL and URL.revokeObjectURL
const mockCreateObjectURL = vi.fn();
const mockRevokeObjectURL = vi.fn();

describe("useCoverFile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateObjectURL.mockReturnValue("blob:mock-url");
    vi.mocked(validateImageFile).mockReturnValue({ valid: true });
    // Create a mock that preserves URL's prototype chain
    const OriginalURL = globalThis.URL;
    const MockURL = function (this: URL, ...args: unknown[]) {
      return new OriginalURL(...(args as [string | URL, string?]));
    } as unknown as typeof URL;
    MockURL.prototype = OriginalURL.prototype;
    MockURL.createObjectURL = mockCreateObjectURL;
    MockURL.revokeObjectURL = mockRevokeObjectURL;
    vi.stubGlobal("URL", MockURL);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should initialize with null cover file when no initialCoverFile", () => {
    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    expect(result.current.coverFile).toBeNull();
    expect(result.current.coverPreviewUrl).toBeNull();
    expect(result.current.coverError).toBeNull();
    expect(result.current.isCoverDeleteStaged).toBe(false);
  });

  it("should initialize with initialCoverFile in create mode", () => {
    const initialFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const { result } = renderHook(() =>
      useCoverFile({ initialCoverFile: initialFile, isEditMode: false }),
    );

    expect(result.current.coverFile).toBe(initialFile);
    expect(mockCreateObjectURL).toHaveBeenCalledWith(initialFile);
    expect(result.current.coverPreviewUrl).toBe("blob:mock-url");
  });

  it("should not create preview URL in edit mode", () => {
    const initialFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const { result } = renderHook(() =>
      useCoverFile({ initialCoverFile: initialFile, isEditMode: true }),
    );

    expect(result.current.coverFile).toBe(initialFile);
    expect(mockCreateObjectURL).not.toHaveBeenCalled();
    expect(result.current.coverPreviewUrl).toBeNull();
  });

  it("should handle file input change with valid file", () => {
    const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    vi.mocked(validateImageFile).mockReturnValue({ valid: true });

    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    const mockEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(validateImageFile).toHaveBeenCalledWith(file);
    expect(result.current.coverFile).toBe(file);
    expect(result.current.coverError).toBeNull();
    expect(result.current.isCoverDeleteStaged).toBe(false);
    expect(mockCreateObjectURL).toHaveBeenCalledWith(file);
  });

  it("should handle file input change with invalid file", () => {
    const file = new File(["test"], "cover.txt", { type: "text/plain" });
    vi.mocked(validateImageFile).mockReturnValue({
      valid: false,
      error: "Invalid file type",
    });

    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    const mockEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(validateImageFile).toHaveBeenCalledWith(file);
    expect(result.current.coverFile).toBeNull();
    expect(result.current.coverError).toBe("Invalid file type");
    expect(mockCreateObjectURL).not.toHaveBeenCalled();
  });

  it("should handle file input change with invalid file and no error message", () => {
    const file = new File(["test"], "cover.txt", { type: "text/plain" });
    vi.mocked(validateImageFile).mockReturnValue({ valid: false });

    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    const mockEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(result.current.coverError).toBe("Invalid file");
  });

  it("should handle file input change with no file selected", () => {
    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    const mockEvent = {
      target: {
        files: null,
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(result.current.coverFile).toBeNull();
    expect(validateImageFile).not.toHaveBeenCalled();
  });

  it("should clear cover file and reset input", () => {
    const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const mockInput = {
      value: "test.jpg",
    } as HTMLInputElement;

    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    // Set a file first
    const mockEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(result.current.coverFile).toBe(file);

    // Set the ref
    result.current.fileInputRef.current = mockInput;

    act(() => {
      result.current.handleClearCoverFile();
    });

    expect(result.current.coverFile).toBeNull();
    expect(result.current.coverError).toBeNull();
    expect(result.current.isCoverDeleteStaged).toBe(false);
    expect(mockInput.value).toBe("");
  });

  it("should stage cover deletion", () => {
    const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const mockInput = {
      value: "test.jpg",
    } as HTMLInputElement;

    const { result } = renderHook(() =>
      useCoverFile({ initialCoverFile: file, isEditMode: true }),
    );

    result.current.fileInputRef.current = mockInput;

    act(() => {
      result.current.handleCoverDelete();
    });

    expect(result.current.isCoverDeleteStaged).toBe(true);
    expect(result.current.coverFile).toBeNull();
    expect(result.current.coverError).toBeNull();
    expect(mockInput.value).toBe("");
  });

  it("should cancel staged deletion", () => {
    const { result } = renderHook(() => useCoverFile({ isEditMode: true }));

    act(() => {
      result.current.handleCoverDelete();
    });

    expect(result.current.isCoverDeleteStaged).toBe(true);

    act(() => {
      result.current.handleCancelDelete();
    });

    expect(result.current.isCoverDeleteStaged).toBe(false);
  });

  it("should reset cover state", () => {
    const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const mockInput = {
      value: "test.jpg",
    } as HTMLInputElement;

    const { result } = renderHook(() =>
      useCoverFile({ initialCoverFile: file, isEditMode: false }),
    );

    result.current.fileInputRef.current = mockInput;

    // Set some state
    act(() => {
      result.current.handleCoverDelete();
    });

    expect(result.current.isCoverDeleteStaged).toBe(true);

    act(() => {
      result.current.reset();
    });

    expect(result.current.coverFile).toBeNull();
    expect(result.current.coverError).toBeNull();
    expect(result.current.isCoverDeleteStaged).toBe(false);
    expect(mockInput.value).toBe("");
  });

  it("should revoke object URL when cover file changes", () => {
    const file1 = new File(["test1"], "cover1.jpg", { type: "image/jpeg" });
    const file2 = new File(["test2"], "cover2.jpg", { type: "image/jpeg" });
    mockCreateObjectURL
      .mockReturnValueOnce("blob:url1")
      .mockReturnValueOnce("blob:url2");

    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    const mockEvent1 = {
      target: {
        files: [file1],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent1);
    });

    expect(result.current.coverPreviewUrl).toBe("blob:url1");

    const mockEvent2 = {
      target: {
        files: [file2],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent2);
    });

    expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:url1");
    expect(result.current.coverPreviewUrl).toBe("blob:url2");
  });

  it("should revoke object URL on unmount", () => {
    const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    mockCreateObjectURL.mockReturnValue("blob:url1");

    const { result, unmount } = renderHook(() =>
      useCoverFile({ isEditMode: false }),
    );

    const mockEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(result.current.coverPreviewUrl).toBe("blob:url1");

    unmount();

    expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:url1");
  });

  it("should sync with initialCoverFile in create mode when user hasn't touched", () => {
    const initialFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const { result, rerender } = renderHook(
      ({ initialCoverFile }: { initialCoverFile?: File | null }) =>
        useCoverFile({ initialCoverFile, isEditMode: false }),
      { initialProps: { initialCoverFile: null as File | null } },
    );

    expect(result.current.coverFile).toBeNull();

    rerender({ initialCoverFile: initialFile as File | null });

    expect(result.current.coverFile).toBe(initialFile);
  });

  it("should not sync with initialCoverFile if user has already touched", () => {
    const initialFile = new File(["test"], "cover.jpg", {
      type: "image/jpeg",
    });
    const userFile = new File(["user"], "user.jpg", { type: "image/jpeg" });

    const { result, rerender } = renderHook(
      ({ initialCoverFile }: { initialCoverFile?: File | null }) =>
        useCoverFile({ initialCoverFile, isEditMode: false }),
      { initialProps: { initialCoverFile: null as File | null } },
    );

    // User selects a file
    const mockEvent = {
      target: {
        files: [userFile],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(result.current.coverFile).toBe(userFile);

    // Update initialCoverFile - should not overwrite
    rerender({ initialCoverFile: initialFile as File | null });

    expect(result.current.coverFile).toBe(userFile); // Still user's file
  });

  it("should not sync with initialCoverFile in edit mode", () => {
    const initialFile = new File(["test"], "cover.jpg", {
      type: "image/jpeg",
    });
    const { result, rerender } = renderHook(
      ({ initialCoverFile }: { initialCoverFile?: File | null }) =>
        useCoverFile({ initialCoverFile, isEditMode: true }),
      { initialProps: { initialCoverFile: null as File | null } },
    );

    expect(result.current.coverFile).toBeNull();

    rerender({ initialCoverFile: initialFile as File | null });

    expect(result.current.coverFile).toBeNull(); // Should not sync in edit mode
  });

  it("should clear preview URL when cover file is cleared", () => {
    const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    mockCreateObjectURL.mockReturnValue("blob:url1");

    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    const mockEvent = {
      target: {
        files: [file],
      },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleCoverFileChange(mockEvent);
    });

    expect(result.current.coverPreviewUrl).toBe("blob:url1");

    act(() => {
      result.current.handleClearCoverFile();
    });

    expect(result.current.coverPreviewUrl).toBeNull();
    expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:url1");
  });

  it("should handle clear when fileInputRef is null", () => {
    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    expect(result.current.fileInputRef.current).toBeNull();

    act(() => {
      result.current.handleClearCoverFile();
    });

    // Should not throw
    expect(result.current.coverFile).toBeNull();
  });

  it("should handle delete when fileInputRef is null", () => {
    const { result } = renderHook(() => useCoverFile({ isEditMode: true }));

    expect(result.current.fileInputRef.current).toBeNull();

    act(() => {
      result.current.handleCoverDelete();
    });

    // Should not throw
    expect(result.current.isCoverDeleteStaged).toBe(true);
  });

  it("should handle reset when fileInputRef is null", () => {
    const { result } = renderHook(() => useCoverFile({ isEditMode: false }));

    expect(result.current.fileInputRef.current).toBeNull();

    act(() => {
      result.current.reset();
    });

    // Should not throw
    expect(result.current.coverFile).toBeNull();
  });

  it("should update preview URL when switching from edit to create mode", () => {
    const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const { result, rerender } = renderHook(
      ({ isEditMode }) => useCoverFile({ initialCoverFile: file, isEditMode }),
      { initialProps: { isEditMode: true } },
    );

    expect(result.current.coverPreviewUrl).toBeNull();

    rerender({ isEditMode: false });

    expect(mockCreateObjectURL).toHaveBeenCalledWith(file);
    expect(result.current.coverPreviewUrl).toBe("blob:mock-url");
  });
});
