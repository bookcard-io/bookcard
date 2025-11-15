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
import { useFileDropzone } from "./useFileDropzone";

/**
 * Creates a mock file.
 *
 * Parameters
 * ----------
 * name : string
 *     File name.
 * type : string
 *     MIME type.
 * content : string
 *     File content.
 *
 * Returns
 * -------
 * File
 *     Mock file object.
 */
function createMockFile(name: string, type: string, content: string = "test") {
  return new File([content], name, { type });
}

/**
 * Creates a mock drag event.
 *
 * Parameters
 * ----------
 * files : File[]
 *     Files in the drag event.
 *
 * Returns
 * -------
 * React.DragEvent
 *     Mock drag event.
 */
function createMockDragEvent(files: File[]): React.DragEvent {
  const dataTransfer = {
    files: files as unknown as FileList,
  } as DataTransfer;

  return {
    preventDefault: vi.fn(),
    stopPropagation: vi.fn(),
    dataTransfer,
  } as unknown as React.DragEvent;
}

/**
 * Creates a mock change event.
 *
 * Parameters
 * ----------
 * file : File | null
 *     File in the input.
 *
 * Returns
 * -------
 * React.ChangeEvent<HTMLInputElement>
 *     Mock change event.
 */
function createMockChangeEvent(
  file: File | null,
): React.ChangeEvent<HTMLInputElement> {
  const input = document.createElement("input");
  input.type = "file";
  if (file) {
    Object.defineProperty(input, "files", {
      value: [file],
      writable: false,
    });
  }

  return {
    target: input,
    preventDefault: vi.fn(),
    stopPropagation: vi.fn(),
  } as unknown as React.ChangeEvent<HTMLInputElement>;
}

describe("useFileDropzone", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return all required properties and handlers", () => {
    const { result } = renderHook(() => useFileDropzone());

    expect(result.current.fileInputRef).toBeDefined();
    expect(result.current.isDragging).toBe(false);
    expect(result.current.accept).toBeDefined();
    expect(result.current.openFileBrowser).toBeDefined();
    expect(result.current.dragHandlers).toBeDefined();
    expect(result.current.dragHandlers.onDragEnter).toBeDefined();
    expect(result.current.dragHandlers.onDragOver).toBeDefined();
    expect(result.current.dragHandlers.onDragLeave).toBeDefined();
    expect(result.current.dragHandlers.onDrop).toBeDefined();
    expect(result.current.handleFileChange).toBeDefined();
    expect(result.current.handleClick).toBeDefined();
    expect(result.current.handleKeyDown).toBeDefined();
  });

  it("should use default accept value", () => {
    const { result } = renderHook(() => useFileDropzone());

    expect(result.current.accept).toBe(
      "image/jpeg,image/jpg,image/png,image/gif,image/webp,image/svg+xml",
    );
  });

  it("should use custom accept value", () => {
    const customAccept = "application/pdf";
    const { result } = renderHook(() =>
      useFileDropzone({ accept: customAccept }),
    );

    expect(result.current.accept).toBe(customAccept);
  });

  it("should call onFileSelect when file is selected via input", () => {
    const mockOnFileSelect = vi.fn();
    const file = createMockFile("test.jpg", "image/jpeg");
    const { result } = renderHook(() =>
      useFileDropzone({ onFileSelect: mockOnFileSelect }),
    );

    act(() => {
      result.current.handleFileChange(createMockChangeEvent(file));
    });

    expect(mockOnFileSelect).toHaveBeenCalledWith(file);
  });

  it("should reset input value after file selection", () => {
    const file = createMockFile("test.jpg", "image/jpeg");
    const { result } = renderHook(() => useFileDropzone());

    const mockInput = document.createElement("input");
    mockInput.type = "file";
    result.current.fileInputRef.current = mockInput;

    act(() => {
      const changeEvent = createMockChangeEvent(file);
      result.current.handleFileChange(changeEvent);
    });

    expect(mockInput.value).toBe("");
  });

  it("should not call onFileSelect when no file is selected", () => {
    const mockOnFileSelect = vi.fn();
    const { result } = renderHook(() =>
      useFileDropzone({ onFileSelect: mockOnFileSelect }),
    );

    act(() => {
      result.current.handleFileChange(createMockChangeEvent(null));
    });

    expect(mockOnFileSelect).not.toHaveBeenCalled();
  });

  it("should set isDragging to true on drag enter", () => {
    const { result } = renderHook(() => useFileDropzone());
    const dragEvent = createMockDragEvent([]);

    act(() => {
      result.current.dragHandlers.onDragEnter(dragEvent);
    });

    expect(result.current.isDragging).toBe(true);
    expect(dragEvent.preventDefault).toHaveBeenCalled();
    expect(dragEvent.stopPropagation).toHaveBeenCalled();
  });

  it("should prevent default on drag over", () => {
    const { result } = renderHook(() => useFileDropzone());
    const dragEvent = createMockDragEvent([]);

    act(() => {
      result.current.dragHandlers.onDragOver(dragEvent);
    });

    expect(dragEvent.preventDefault).toHaveBeenCalled();
    expect(dragEvent.stopPropagation).toHaveBeenCalled();
  });

  it("should set isDragging to false on drag leave", () => {
    const { result } = renderHook(() => useFileDropzone());
    const dragEvent = createMockDragEvent([]);

    act(() => {
      result.current.dragHandlers.onDragEnter(dragEvent);
      result.current.dragHandlers.onDragLeave(dragEvent);
    });

    expect(result.current.isDragging).toBe(false);
    expect(dragEvent.preventDefault).toHaveBeenCalled();
    expect(dragEvent.stopPropagation).toHaveBeenCalled();
  });

  it("should process first image file when filterImages is true", () => {
    const mockOnFileSelect = vi.fn();
    const imageFile = createMockFile("test.jpg", "image/jpeg");
    const textFile = createMockFile("test.txt", "text/plain");
    const { result } = renderHook(() =>
      useFileDropzone({ onFileSelect: mockOnFileSelect, filterImages: true }),
    );

    act(() => {
      result.current.dragHandlers.onDrop(
        createMockDragEvent([textFile, imageFile]),
      );
    });

    expect(mockOnFileSelect).toHaveBeenCalledWith(imageFile);
    expect(result.current.isDragging).toBe(false);
  });

  it("should process first file when filterImages is false", () => {
    const mockOnFileSelect = vi.fn();
    const textFile = createMockFile("test.txt", "text/plain");
    const imageFile = createMockFile("test.jpg", "image/jpeg");
    const { result } = renderHook(() =>
      useFileDropzone({ onFileSelect: mockOnFileSelect, filterImages: false }),
    );

    act(() => {
      result.current.dragHandlers.onDrop(
        createMockDragEvent([textFile, imageFile]),
      );
    });

    expect(mockOnFileSelect).toHaveBeenCalledWith(textFile);
    expect(result.current.isDragging).toBe(false);
  });

  it("should not process file if no image file found when filterImages is true", () => {
    const mockOnFileSelect = vi.fn();
    const textFile = createMockFile("test.txt", "text/plain");
    const { result } = renderHook(() =>
      useFileDropzone({ onFileSelect: mockOnFileSelect, filterImages: true }),
    );

    act(() => {
      result.current.dragHandlers.onDrop(createMockDragEvent([textFile]));
    });

    expect(mockOnFileSelect).not.toHaveBeenCalled();
    expect(result.current.isDragging).toBe(false);
  });

  it("should not process file if no files in drop event", () => {
    const mockOnFileSelect = vi.fn();
    const { result } = renderHook(() =>
      useFileDropzone({ onFileSelect: mockOnFileSelect }),
    );

    act(() => {
      result.current.dragHandlers.onDrop(createMockDragEvent([]));
    });

    expect(mockOnFileSelect).not.toHaveBeenCalled();
    expect(result.current.isDragging).toBe(false);
  });

  it("should open file browser when openFileBrowser is called", () => {
    const { result } = renderHook(() => useFileDropzone());
    const mockInput = document.createElement("input");
    const clickSpy = vi.spyOn(mockInput, "click");
    result.current.fileInputRef.current = mockInput;

    act(() => {
      result.current.openFileBrowser();
    });

    expect(clickSpy).toHaveBeenCalled();
  });

  it("should open file browser when handleClick is called", () => {
    const { result } = renderHook(() => useFileDropzone());
    const mockInput = document.createElement("input");
    const clickSpy = vi.spyOn(mockInput, "click");
    result.current.fileInputRef.current = mockInput;

    act(() => {
      result.current.handleClick();
    });

    expect(clickSpy).toHaveBeenCalled();
  });

  it("should open file browser on Enter key", () => {
    const { result } = renderHook(() => useFileDropzone());
    const mockInput = document.createElement("input");
    const clickSpy = vi.spyOn(mockInput, "click");
    result.current.fileInputRef.current = mockInput;

    const keyEvent = {
      key: "Enter",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent;

    act(() => {
      result.current.handleKeyDown(keyEvent);
    });

    expect(clickSpy).toHaveBeenCalled();
    expect(keyEvent.preventDefault).toHaveBeenCalled();
  });

  it("should open file browser on Space key", () => {
    const { result } = renderHook(() => useFileDropzone());
    const mockInput = document.createElement("input");
    const clickSpy = vi.spyOn(mockInput, "click");
    result.current.fileInputRef.current = mockInput;

    const keyEvent = {
      key: " ",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent;

    act(() => {
      result.current.handleKeyDown(keyEvent);
    });

    expect(clickSpy).toHaveBeenCalled();
    expect(keyEvent.preventDefault).toHaveBeenCalled();
  });

  it("should not open file browser on other keys", () => {
    const { result } = renderHook(() => useFileDropzone());
    const mockInput = document.createElement("input");
    const clickSpy = vi.spyOn(mockInput, "click");
    result.current.fileInputRef.current = mockInput;

    const keyEvent = {
      key: "a",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent;

    act(() => {
      result.current.handleKeyDown(keyEvent);
    });

    expect(clickSpy).not.toHaveBeenCalled();
  });

  it("should handle drop event with preventDefault and stopPropagation", () => {
    const { result } = renderHook(() => useFileDropzone());
    const dragEvent = createMockDragEvent([]);

    act(() => {
      result.current.dragHandlers.onDrop(dragEvent);
    });

    expect(dragEvent.preventDefault).toHaveBeenCalled();
    expect(dragEvent.stopPropagation).toHaveBeenCalled();
  });
});
