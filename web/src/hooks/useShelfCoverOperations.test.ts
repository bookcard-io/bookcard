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

import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Shelf } from "@/types/shelf";
import { useShelfCoverOperations } from "./useShelfCoverOperations";

function createMockShelf(id: number): Shelf {
  return {
    id,
    uuid: `uuid-${id}`,
    name: `Shelf ${id}`,
    description: null,
    cover_picture: null,
    is_public: false,
    is_active: true,
    shelf_type: "shelf",
    user_id: 1,
    library_id: 1,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    last_modified: "2024-01-01T00:00:00Z",
    book_count: 0,
  };
}

describe("useShelfCoverOperations", () => {
  let mockUploadCover: ReturnType<
    typeof vi.fn<(shelfId: number, file: File) => Promise<Shelf>>
  >;
  let mockDeleteCover: ReturnType<
    typeof vi.fn<(shelfId: number) => Promise<Shelf>>
  >;
  let onCoverSaved: ReturnType<typeof vi.fn<(shelf: Shelf) => void>>;
  let onCoverDeleted: ReturnType<typeof vi.fn<(shelf: Shelf) => void>>;
  let onError: ReturnType<typeof vi.fn<(error: string) => void>>;

  beforeEach(() => {
    mockUploadCover = vi.fn<(shelfId: number, file: File) => Promise<Shelf>>();
    mockDeleteCover = vi.fn<(shelfId: number) => Promise<Shelf>>();
    onCoverSaved = vi.fn<(shelf: Shelf) => void>();
    onCoverDeleted = vi.fn<(shelf: Shelf) => void>();
    onError = vi.fn<(error: string) => void>();
  });

  it("should upload cover when coverFile is provided", async () => {
    const shelf = createMockShelf(1);
    const coverFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const updatedShelf = { ...shelf, cover_picture: "new-cover.jpg" };

    mockUploadCover.mockResolvedValue(updatedShelf);

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await result.current.executeCoverOperations(shelf, coverFile, false);

    expect(mockUploadCover).toHaveBeenCalledWith(1, coverFile);
    expect(onCoverSaved).toHaveBeenCalledWith(updatedShelf);
    expect(mockDeleteCover).not.toHaveBeenCalled();
    expect(onCoverDeleted).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("should delete cover when isCoverDeleteStaged is true", async () => {
    const shelf = createMockShelf(1);
    const updatedShelf = { ...shelf, cover_picture: null };

    mockDeleteCover.mockResolvedValue(updatedShelf);

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await result.current.executeCoverOperations(shelf, null, true);

    expect(mockDeleteCover).toHaveBeenCalledWith(1);
    expect(onCoverDeleted).toHaveBeenCalledWith(updatedShelf);
    expect(mockUploadCover).not.toHaveBeenCalled();
    expect(onCoverSaved).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("should delete then upload when both are staged", async () => {
    const shelf = createMockShelf(1);
    const coverFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const deletedShelf = { ...shelf, cover_picture: null };
    const finalShelf = { ...shelf, cover_picture: "new-cover.jpg" };

    mockDeleteCover.mockResolvedValue(deletedShelf);
    mockUploadCover.mockResolvedValue(finalShelf);

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await result.current.executeCoverOperations(shelf, coverFile, true);

    expect(mockDeleteCover).toHaveBeenCalledWith(1);
    expect(onCoverDeleted).toHaveBeenCalledWith(deletedShelf);
    expect(mockUploadCover).toHaveBeenCalledWith(1, coverFile);
    expect(onCoverSaved).toHaveBeenCalledWith(finalShelf);
    expect(onError).not.toHaveBeenCalled();
  });

  it("should do nothing when neither delete nor upload is staged", async () => {
    const shelf = createMockShelf(1);

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await result.current.executeCoverOperations(shelf, null, false);

    expect(mockDeleteCover).not.toHaveBeenCalled();
    expect(mockUploadCover).not.toHaveBeenCalled();
    expect(onCoverSaved).not.toHaveBeenCalled();
    expect(onCoverDeleted).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("should handle upload error with Error instance", async () => {
    const shelf = createMockShelf(1);
    const coverFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const error = new Error("Upload failed");

    mockUploadCover.mockRejectedValue(error);

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await expect(
      result.current.executeCoverOperations(shelf, coverFile, false),
    ).rejects.toThrow("Upload failed");

    expect(onError).toHaveBeenCalledWith("Upload failed");
    expect(onCoverSaved).not.toHaveBeenCalled();
  });

  it("should handle upload error with non-Error value", async () => {
    const shelf = createMockShelf(1);
    const coverFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });

    mockUploadCover.mockRejectedValue("String error");

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await expect(
      result.current.executeCoverOperations(shelf, coverFile, false),
    ).rejects.toBe("String error");

    expect(onError).toHaveBeenCalledWith("Failed to upload cover picture");
    expect(onCoverSaved).not.toHaveBeenCalled();
  });

  it("should handle delete error with Error instance", async () => {
    const shelf = createMockShelf(1);
    const error = new Error("Delete failed");

    mockDeleteCover.mockRejectedValue(error);

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await expect(
      result.current.executeCoverOperations(shelf, null, true),
    ).rejects.toThrow("Delete failed");

    expect(onError).toHaveBeenCalledWith("Delete failed");
    expect(onCoverDeleted).not.toHaveBeenCalled();
  });

  it("should handle delete error with non-Error value", async () => {
    const shelf = createMockShelf(1);

    mockDeleteCover.mockRejectedValue("String error");

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
        onCoverSaved,
        onCoverDeleted,
        onError,
      }),
    );

    await expect(
      result.current.executeCoverOperations(shelf, null, true),
    ).rejects.toBe("String error");

    expect(onError).toHaveBeenCalledWith("Failed to delete cover picture");
    expect(onCoverDeleted).not.toHaveBeenCalled();
  });

  it("should not call callbacks when not provided", async () => {
    const shelf = createMockShelf(1);
    const coverFile = new File(["test"], "cover.jpg", { type: "image/jpeg" });
    const updatedShelf = { ...shelf, cover_picture: "new-cover.jpg" };

    mockUploadCover.mockResolvedValue(updatedShelf);

    const { result } = renderHook(() =>
      useShelfCoverOperations({
        operations: {
          uploadCover: mockUploadCover,
          deleteCover: mockDeleteCover,
        },
      }),
    );

    await result.current.executeCoverOperations(shelf, coverFile, false);

    expect(mockUploadCover).toHaveBeenCalledWith(1, coverFile);
    // Should not throw even if callbacks are undefined
    expect(true).toBe(true);
  });
});
