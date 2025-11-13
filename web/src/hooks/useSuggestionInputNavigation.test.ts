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
import { describe, expect, it, vi } from "vitest";
import { useSuggestionInputNavigation } from "./useSuggestionInputNavigation";

/**
 * Creates a keyboard event with the given key.
 *
 * Parameters
 * ----------
 * key : string
 *     Key value.
 *
 * Returns
 * -------
 * React.KeyboardEvent<HTMLInputElement>
 *     Mock keyboard event.
 */
function createKeyboardEvent(
  key: string,
): React.KeyboardEvent<HTMLInputElement> {
  return {
    key,
    preventDefault: vi.fn(),
  } as unknown as React.KeyboardEvent<HTMLInputElement>;
}

describe("useSuggestionInputNavigation", () => {
  it("should call onSubmit when Enter is pressed without suggestions", () => {
    const onSubmit = vi.fn();
    const onSelectSuggestion = vi.fn();
    const onHideSuggestions = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: false,
        suggestions: [],
        selectedIndex: -1,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion,
        onSubmit,
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions,
      }),
    );

    const event = createKeyboardEvent("Enter");
    result.current.handleKeyDown(event);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSelectSuggestion).not.toHaveBeenCalled();
    expect(onHideSuggestions).not.toHaveBeenCalled();
    expect(event.preventDefault).not.toHaveBeenCalled();
  });

  it("should call onSelectSuggestion when Enter is pressed with selected suggestion", () => {
    const suggestions = ["suggestion1", "suggestion2"];
    const onSelectSuggestion = vi.fn();
    const onHideSuggestions = vi.fn();
    const onSubmit = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions,
        selectedIndex: 0,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion,
        onSubmit,
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions,
      }),
    );

    const event = createKeyboardEvent("Enter");
    result.current.handleKeyDown(event);

    expect(onSelectSuggestion).toHaveBeenCalledWith("suggestion1");
    expect(onHideSuggestions).toHaveBeenCalledTimes(1);
    expect(onSubmit).not.toHaveBeenCalled();
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should use value when no suggestion is selected on Enter", () => {
    const suggestions: string[] = [];
    const onSelectSuggestion = vi.fn();
    const onHideSuggestions = vi.fn();
    const onSubmit = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions,
        selectedIndex: -1,
        value: "typed value",
        getSuggestionValue: (s) => s,
        onSelectSuggestion,
        onSubmit,
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions,
      }),
    );

    const event = createKeyboardEvent("Enter");
    result.current.handleKeyDown(event);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSelectSuggestion).not.toHaveBeenCalled();
  });

  it("should not handle Enter when suggestions are empty", () => {
    const onSubmit = vi.fn();
    const onSelectSuggestion = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions: [],
        selectedIndex: -1,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion,
        onSubmit,
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("Enter");
    result.current.handleKeyDown(event);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSelectSuggestion).not.toHaveBeenCalled();
  });

  it("should select first suggestion on Tab when no selection", () => {
    const suggestions = ["suggestion1", "suggestion2"];
    const onSelectSuggestion = vi.fn();
    const onHideSuggestions = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions,
        selectedIndex: -1,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion,
        onSubmit: vi.fn(),
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions,
      }),
    );

    const event = createKeyboardEvent("Tab");
    result.current.handleKeyDown(event);

    expect(onSelectSuggestion).toHaveBeenCalledWith("suggestion1");
    expect(onHideSuggestions).toHaveBeenCalledTimes(1);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should select selected suggestion on Tab", () => {
    const suggestions = ["suggestion1", "suggestion2"];
    const onSelectSuggestion = vi.fn();
    const onHideSuggestions = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions,
        selectedIndex: 1,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion,
        onSubmit: vi.fn(),
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions,
      }),
    );

    const event = createKeyboardEvent("Tab");
    result.current.handleKeyDown(event);

    expect(onSelectSuggestion).toHaveBeenCalledWith("suggestion2");
    expect(onHideSuggestions).toHaveBeenCalledTimes(1);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should not handle Tab when suggestions are hidden", () => {
    const onSelectSuggestion = vi.fn();
    const onHideSuggestions = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: false,
        suggestions: ["suggestion1"],
        selectedIndex: 0,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion,
        onSubmit: vi.fn(),
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions,
      }),
    );

    const event = createKeyboardEvent("Tab");
    result.current.handleKeyDown(event);

    expect(onSelectSuggestion).not.toHaveBeenCalled();
    expect(onHideSuggestions).not.toHaveBeenCalled();
    expect(event.preventDefault).not.toHaveBeenCalled();
  });

  it("should call onSelectNext on ArrowDown", () => {
    const onSelectNext = vi.fn();
    const onSelectPrevious = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions: ["suggestion1", "suggestion2"],
        selectedIndex: 0,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion: vi.fn(),
        onSubmit: vi.fn(),
        onSelectNext,
        onSelectPrevious,
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("ArrowDown");
    result.current.handleKeyDown(event);

    expect(onSelectNext).toHaveBeenCalledTimes(1);
    expect(onSelectPrevious).not.toHaveBeenCalled();
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should call onSelectNext on Down key", () => {
    const onSelectNext = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions: ["suggestion1"],
        selectedIndex: 0,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion: vi.fn(),
        onSubmit: vi.fn(),
        onSelectNext,
        onSelectPrevious: vi.fn(),
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("Down");
    result.current.handleKeyDown(event);

    expect(onSelectNext).toHaveBeenCalledTimes(1);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should call onSelectPrevious on ArrowUp", () => {
    const onSelectNext = vi.fn();
    const onSelectPrevious = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions: ["suggestion1", "suggestion2"],
        selectedIndex: 1,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion: vi.fn(),
        onSubmit: vi.fn(),
        onSelectNext,
        onSelectPrevious,
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("ArrowUp");
    result.current.handleKeyDown(event);

    expect(onSelectPrevious).toHaveBeenCalledTimes(1);
    expect(onSelectNext).not.toHaveBeenCalled();
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should call onSelectPrevious on Up key", () => {
    const onSelectPrevious = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions: ["suggestion1"],
        selectedIndex: 0,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion: vi.fn(),
        onSubmit: vi.fn(),
        onSelectNext: vi.fn(),
        onSelectPrevious,
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("Up");
    result.current.handleKeyDown(event);

    expect(onSelectPrevious).toHaveBeenCalledTimes(1);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it("should not handle ArrowDown when suggestions are hidden", () => {
    const onSelectNext = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: false,
        suggestions: ["suggestion1"],
        selectedIndex: 0,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion: vi.fn(),
        onSubmit: vi.fn(),
        onSelectNext,
        onSelectPrevious: vi.fn(),
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("ArrowDown");
    result.current.handleKeyDown(event);

    expect(onSelectNext).not.toHaveBeenCalled();
    expect(event.preventDefault).not.toHaveBeenCalled();
  });

  it("should not handle ArrowDown when suggestions are empty", () => {
    const onSelectNext = vi.fn();

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions: [],
        selectedIndex: -1,
        value: "test",
        getSuggestionValue: (s) => s,
        onSelectSuggestion: vi.fn(),
        onSubmit: vi.fn(),
        onSelectNext,
        onSelectPrevious: vi.fn(),
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("ArrowDown");
    result.current.handleKeyDown(event);

    expect(onSelectNext).not.toHaveBeenCalled();
    expect(event.preventDefault).not.toHaveBeenCalled();
  });

  it("should handle custom suggestion type with getSuggestionValue", () => {
    interface CustomSuggestion {
      id: number;
      label: string;
    }

    const suggestions: CustomSuggestion[] = [
      { id: 1, label: "Label 1" },
      { id: 2, label: "Label 2" },
    ];
    const onSelectSuggestion = vi.fn();
    const getSuggestionValue = (s: CustomSuggestion) => s.label;

    const { result } = renderHook(() =>
      useSuggestionInputNavigation({
        showSuggestions: true,
        suggestions,
        selectedIndex: 0,
        value: "test",
        getSuggestionValue,
        onSelectSuggestion,
        onSubmit: vi.fn(),
        onSelectNext: vi.fn(),
        onSelectPrevious: vi.fn(),
        onHideSuggestions: vi.fn(),
      }),
    );

    const event = createKeyboardEvent("Enter");
    result.current.handleKeyDown(event);

    expect(onSelectSuggestion).toHaveBeenCalledWith("Label 1");
  });
});
