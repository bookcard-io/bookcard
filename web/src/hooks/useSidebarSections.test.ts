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
import { beforeEach, describe, expect, it } from "vitest";
import { useSidebarSections } from "./useSidebarSections";

describe("useSidebarSections", () => {
  beforeEach(() => {
    // No setup needed
  });

  it("should initialize with default sections", () => {
    const { result } = renderHook(() => useSidebarSections());

    expect(result.current.expandedSections).toBeInstanceOf(Set);
    expect(result.current.expandedSections.has("MY LIBRARY")).toBe(true);
    expect(result.current.expandedSections.has("MY SHELVES")).toBe(true);
    expect(result.current.expandedSections.has("DEVICES")).toBe(true);
    expect(result.current.toggleSection).toBeDefined();
  });

  it("should initialize with custom initial sections", () => {
    const { result } = renderHook(() =>
      useSidebarSections(["SECTION1", "SECTION2"]),
    );

    expect(result.current.expandedSections.has("SECTION1")).toBe(true);
    expect(result.current.expandedSections.has("SECTION2")).toBe(true);
    expect(result.current.expandedSections.has("MY LIBRARY")).toBe(false);
  });

  it("should initialize with empty array", () => {
    const { result } = renderHook(() => useSidebarSections([]));

    expect(result.current.expandedSections.size).toBe(0);
  });

  it("should toggle section from expanded to collapsed", () => {
    const { result } = renderHook(() => useSidebarSections(["SECTION1"]));

    expect(result.current.expandedSections.has("SECTION1")).toBe(true);

    act(() => {
      result.current.toggleSection("SECTION1");
    });

    expect(result.current.expandedSections.has("SECTION1")).toBe(false);
  });

  it("should toggle section from collapsed to expanded", () => {
    const { result } = renderHook(() => useSidebarSections([]));

    expect(result.current.expandedSections.has("SECTION1")).toBe(false);

    act(() => {
      result.current.toggleSection("SECTION1");
    });

    expect(result.current.expandedSections.has("SECTION1")).toBe(true);
  });

  it("should toggle multiple sections independently", () => {
    const { result } = renderHook(() =>
      useSidebarSections(["SECTION1", "SECTION2"]),
    );

    expect(result.current.expandedSections.has("SECTION1")).toBe(true);
    expect(result.current.expandedSections.has("SECTION2")).toBe(true);

    act(() => {
      result.current.toggleSection("SECTION1");
    });

    expect(result.current.expandedSections.has("SECTION1")).toBe(false);
    expect(result.current.expandedSections.has("SECTION2")).toBe(true);

    act(() => {
      result.current.toggleSection("SECTION2");
    });

    expect(result.current.expandedSections.has("SECTION1")).toBe(false);
    expect(result.current.expandedSections.has("SECTION2")).toBe(false);
  });

  it("should handle toggling the same section multiple times", () => {
    const { result } = renderHook(() => useSidebarSections(["SECTION1"]));

    act(() => {
      result.current.toggleSection("SECTION1");
      result.current.toggleSection("SECTION1");
      result.current.toggleSection("SECTION1");
    });

    expect(result.current.expandedSections.has("SECTION1")).toBe(false);
  });

  it("should add new section when toggling non-existent section", () => {
    const { result } = renderHook(() => useSidebarSections([]));

    expect(result.current.expandedSections.has("NEW_SECTION")).toBe(false);

    act(() => {
      result.current.toggleSection("NEW_SECTION");
    });

    expect(result.current.expandedSections.has("NEW_SECTION")).toBe(true);
  });

  it("should maintain other sections when toggling one", () => {
    const { result } = renderHook(() =>
      useSidebarSections(["SECTION1", "SECTION2", "SECTION3"]),
    );

    act(() => {
      result.current.toggleSection("SECTION2");
    });

    expect(result.current.expandedSections.has("SECTION1")).toBe(true);
    expect(result.current.expandedSections.has("SECTION2")).toBe(false);
    expect(result.current.expandedSections.has("SECTION3")).toBe(true);
  });

  it("should handle empty string as section title", () => {
    const { result } = renderHook(() => useSidebarSections([]));

    act(() => {
      result.current.toggleSection("");
    });

    expect(result.current.expandedSections.has("")).toBe(true);

    act(() => {
      result.current.toggleSection("");
    });

    expect(result.current.expandedSections.has("")).toBe(false);
  });

  it("should handle special characters in section title", () => {
    const { result } = renderHook(() => useSidebarSections([]));

    const specialTitle = "SECTION & MORE < >";

    act(() => {
      result.current.toggleSection(specialTitle);
    });

    expect(result.current.expandedSections.has(specialTitle)).toBe(true);
  });

  it("should return a new Set instance on each toggle", () => {
    const { result } = renderHook(() => useSidebarSections(["SECTION1"]));

    const initialSet = result.current.expandedSections;

    act(() => {
      result.current.toggleSection("SECTION1");
    });

    // The Set reference should be different (new instance)
    expect(result.current.expandedSections).not.toBe(initialSet);
  });
});
