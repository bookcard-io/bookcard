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
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useBookUploadOrchestrator } from "./useBookUploadOrchestrator";

describe("useBookUploadOrchestrator", () => {
  const mockFileUpload = {
    uploadFile: vi.fn(),
  };

  const mockTaskPolling = {
    pollTask: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return uploadBook function", () => {
    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        getIsMultiFileUpload: () => false,
      }),
    );

    expect(result.current.uploadBook).toBeDefined();
  });

  it("should handle synchronous upload with single book", async () => {
    const onSetSuccessMessage = vi.fn();
    const onUploadSuccess = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({
      book_ids: [123],
    });

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetSuccessMessage,
        onUploadSuccess,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    expect(onSetSuccessMessage).toHaveBeenCalledWith("Books processed! ✅");
    expect(onUploadSuccess).toHaveBeenCalledWith(123);
  });

  it("should handle synchronous upload with multiple books in multi-file mode", async () => {
    const onSetSuccessMessage = vi.fn();
    const onBookAdded = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({
      book_ids: [123, 456],
    });

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetSuccessMessage,
        onBookAdded,
        getIsMultiFileUpload: () => true,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    expect(onSetSuccessMessage).toHaveBeenCalledWith("Books processed! ✅");
    expect(onBookAdded).toHaveBeenCalledWith(123);
    expect(onBookAdded).toHaveBeenCalledWith(456);
  });

  it("should handle synchronous upload with multiple books in single-file mode", async () => {
    const onSetSuccessMessage = vi.fn();
    const onBookAdded = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({
      book_ids: [123, 456],
    });

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetSuccessMessage,
        onBookAdded,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    expect(onSetSuccessMessage).toHaveBeenCalledWith("Books processed! ✅");
    expect(onBookAdded).toHaveBeenCalledWith(123);
    expect(onBookAdded).toHaveBeenCalledWith(456);
  });

  it("should handle asynchronous upload with task_id", async () => {
    const onSetSuccessMessage = vi.fn();
    const onUploadSuccess = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({
      task_id: 789,
    });
    mockTaskPolling.pollTask.mockResolvedValue([123]);

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetSuccessMessage,
        onUploadSuccess,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    expect(onSetSuccessMessage).toHaveBeenCalledWith("🚀 Now processing...");
    expect(mockTaskPolling.pollTask).toHaveBeenCalledWith(789);
    expect(onSetSuccessMessage).toHaveBeenCalledWith("Books processed! ✅");
    expect(onUploadSuccess).toHaveBeenCalledWith(123);
  });

  it("should handle asynchronous upload with task_id and existing book_ids", async () => {
    const onSetSuccessMessage = vi.fn();
    const onUploadSuccess = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({
      task_id: 789,
      book_ids: [999],
    });

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetSuccessMessage,
        onUploadSuccess,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    // When book_ids exist, should not show "Now processing..." and should not poll
    // Instead, should handle book_ids directly (synchronous path)
    expect(onSetSuccessMessage).not.toHaveBeenCalledWith(
      "🚀 Now processing...",
    );
    expect(mockTaskPolling.pollTask).not.toHaveBeenCalled();
    expect(onSetSuccessMessage).toHaveBeenCalledWith("Books processed! ✅");
    expect(onUploadSuccess).toHaveBeenCalledWith(999);
  });

  it("should handle invalid response", async () => {
    const onSetErrorMessage = vi.fn();
    const onUploadError = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({});

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetErrorMessage,
        onUploadError,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    expect(onSetErrorMessage).toHaveBeenCalledWith(
      "Upload response missing both book_ids and task_id",
    );
    expect(onUploadError).toHaveBeenCalledWith(
      "Upload response missing both book_ids and task_id",
    );
  });

  it("should handle upload failure", async () => {
    mockFileUpload.uploadFile.mockResolvedValue(null);

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    // Should return early when response is null (covers line 112)
    expect(mockTaskPolling.pollTask).not.toHaveBeenCalled();
  });

  it("should handle polling with no book IDs", async () => {
    const onSetSuccessMessage = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({
      task_id: 789,
    });
    mockTaskPolling.pollTask.mockResolvedValue(null);

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetSuccessMessage,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    expect(mockTaskPolling.pollTask).toHaveBeenCalledWith(789);
    // Should not call handleBookIds when pollTask returns null
    expect(onSetSuccessMessage).not.toHaveBeenCalledWith("Books processed! ✅");
  });

  it("should handle polling with empty book IDs array", async () => {
    const onSetSuccessMessage = vi.fn();
    mockFileUpload.uploadFile.mockResolvedValue({
      task_id: 789,
    });
    mockTaskPolling.pollTask.mockResolvedValue([]);

    const { result } = renderHook(() =>
      useBookUploadOrchestrator({
        fileUpload: mockFileUpload,
        taskPolling: mockTaskPolling,
        onSetSuccessMessage,
        getIsMultiFileUpload: () => false,
      }),
    );

    const file = new File(["content"], "test.epub");
    await act(async () => {
      await result.current.uploadBook(file);
    });

    expect(mockTaskPolling.pollTask).toHaveBeenCalledWith(789);
    // Should not call handleBookIds when pollTask returns empty array
    expect(onSetSuccessMessage).not.toHaveBeenCalledWith("Books processed! ✅");
  });
});
