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
import { useMultiTextInput } from "./useMultiTextInput";

describe("useMultiTextInput", () => {
  let mockOnChange: ReturnType<typeof vi.fn<(values: string[]) => void>>;

  beforeEach(() => {
    vi.useFakeTimers();
    mockOnChange = vi.fn<(values: string[]) => void>();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should initialize with empty input value", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    expect(result.current.inputValue).toBe("");
  });

  it("should update input value when setInputValue is called", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("test");
    });

    expect(result.current.inputValue).toBe("test");
  });

  it("should add value when addValue is called with valid input", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("test");
    });

    act(() => {
      result.current.addValue();
    });

    expect(mockOnChange).toHaveBeenCalledWith(["test"]);
    expect(result.current.inputValue).toBe("");
  });

  it("should not add empty value when addValue is called", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("   ");
    });

    act(() => {
      result.current.addValue();
    });

    expect(mockOnChange).not.toHaveBeenCalled();
    expect(result.current.inputValue).toBe("   ");
  });

  it("should trim value when adding", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("  test  ");
    });

    act(() => {
      result.current.addValue();
    });

    expect(mockOnChange).toHaveBeenCalledWith(["test"]);
  });

  it("should not add duplicate value when allowDuplicates is false", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: ["existing"],
        onChange: mockOnChange,
        allowDuplicates: false,
      }),
    );

    act(() => {
      result.current.setInputValue("existing");
    });

    act(() => {
      result.current.addValue();
    });

    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it("should add duplicate value when allowDuplicates is true", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: ["existing"],
        onChange: mockOnChange,
        allowDuplicates: true,
      }),
    );

    act(() => {
      result.current.setInputValue("existing");
    });

    act(() => {
      result.current.addValue();
    });

    expect(mockOnChange).toHaveBeenCalledWith(["existing", "existing"]);
  });

  it("should add value from suggestion", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.addSuggestion("suggestion");
    });

    expect(mockOnChange).toHaveBeenCalledWith(["suggestion"]);
    expect(result.current.inputValue).toBe("");
  });

  it("should remove value when removeValue is called", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: ["value1", "value2", "value3"],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.removeValue("value2");
    });

    expect(mockOnChange).toHaveBeenCalledWith(["value1", "value3"]);
  });

  it("should add value on Enter key press", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("test");
    });

    const event = {
      key: "Enter",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(event.preventDefault).toHaveBeenCalled();
    expect(mockOnChange).toHaveBeenCalledWith(["test"]);
    expect(result.current.inputValue).toBe("");
  });

  it("should add value on comma key press", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("test");
    });

    const event = {
      key: ",",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(event.preventDefault).toHaveBeenCalled();
    expect(mockOnChange).toHaveBeenCalledWith(["test"]);
  });

  it("should remove last value on Backspace when input is empty", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: ["value1", "value2"],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("");
    });

    const event = {
      key: "Backspace",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(mockOnChange).toHaveBeenCalledWith(["value1"]);
  });

  it("should not remove value on Backspace when input has value", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: ["value1", "value2"],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("test");
    });

    const event = {
      key: "Backspace",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it("should not remove value on Backspace when values array is empty", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("");
    });

    const event = {
      key: "Backspace",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent<HTMLInputElement>;

    act(() => {
      result.current.handleKeyDown(event);
    });

    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it("should add value on blur after delay", () => {
    const { result } = renderHook(() =>
      useMultiTextInput({
        values: [],
        onChange: mockOnChange,
      }),
    );

    act(() => {
      result.current.setInputValue("test");
    });

    act(() => {
      result.current.handleBlur();
    });

    expect(mockOnChange).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(150);
    });

    expect(mockOnChange).toHaveBeenCalledWith(["test"]);
    expect(result.current.inputValue).toBe("");
  });

  it("should handle multiple values correctly", () => {
    const { result, rerender } = renderHook(
      ({ values }) =>
        useMultiTextInput({
          values,
          onChange: mockOnChange,
        }),
      { initialProps: { values: ["value1"] } },
    );

    act(() => {
      result.current.setInputValue("value2");
    });

    act(() => {
      result.current.addValue();
    });

    expect(mockOnChange).toHaveBeenCalledWith(["value1", "value2"]);

    rerender({ values: ["value1", "value2"] });

    act(() => {
      result.current.setInputValue("value3");
    });

    act(() => {
      result.current.addValue();
    });

    expect(mockOnChange).toHaveBeenLastCalledWith([
      "value1",
      "value2",
      "value3",
    ]);
  });
});
