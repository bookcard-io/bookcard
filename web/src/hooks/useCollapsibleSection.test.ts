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
import { useCollapsibleSection } from "./useCollapsibleSection";

describe("useCollapsibleSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should initialize with default expanded state (true)", () => {
    const { result } = renderHook(() => useCollapsibleSection());

    expect(result.current.isExpanded).toBe(true);
  });

  it("should initialize with custom initialExpanded state", () => {
    const { result } = renderHook(() =>
      useCollapsibleSection({ initialExpanded: false }),
    );

    expect(result.current.isExpanded).toBe(false);
  });

  it("should toggle expanded state", () => {
    const { result } = renderHook(() =>
      useCollapsibleSection({ initialExpanded: false }),
    );

    expect(result.current.isExpanded).toBe(false);

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isExpanded).toBe(true);

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isExpanded).toBe(false);
  });

  it("should set expanded state explicitly to true", () => {
    const { result } = renderHook(() =>
      useCollapsibleSection({ initialExpanded: false }),
    );

    expect(result.current.isExpanded).toBe(false);

    act(() => {
      result.current.setExpanded(true);
    });

    expect(result.current.isExpanded).toBe(true);
  });

  it("should set expanded state explicitly to false", () => {
    const { result } = renderHook(() =>
      useCollapsibleSection({ initialExpanded: true }),
    );

    expect(result.current.isExpanded).toBe(true);

    act(() => {
      result.current.setExpanded(false);
    });

    expect(result.current.isExpanded).toBe(false);
  });

  it("should auto-expand when condition becomes true and autoExpandOnCondition is enabled", () => {
    const { result, rerender } = renderHook(
      ({ condition }) =>
        useCollapsibleSection({
          initialExpanded: false,
          autoExpandOnCondition: true,
          condition,
        }),
      { initialProps: { condition: false } },
    );

    expect(result.current.isExpanded).toBe(false);

    rerender({ condition: true });

    expect(result.current.isExpanded).toBe(true);
  });

  it("should not auto-expand when condition is true but autoExpandOnCondition is false", () => {
    const { result, rerender } = renderHook(
      ({ condition }) =>
        useCollapsibleSection({
          initialExpanded: false,
          autoExpandOnCondition: false,
          condition,
        }),
      { initialProps: { condition: false } },
    );

    expect(result.current.isExpanded).toBe(false);

    rerender({ condition: true });

    expect(result.current.isExpanded).toBe(false);
  });

  it("should not auto-expand when already expanded", () => {
    const { result, rerender } = renderHook(
      ({ condition }) =>
        useCollapsibleSection({
          initialExpanded: true,
          autoExpandOnCondition: true,
          condition,
        }),
      { initialProps: { condition: false } },
    );

    expect(result.current.isExpanded).toBe(true);

    rerender({ condition: true });

    expect(result.current.isExpanded).toBe(true);
  });

  it("should not auto-expand when condition becomes false", () => {
    const { result, rerender } = renderHook(
      ({ condition }) =>
        useCollapsibleSection({
          initialExpanded: false,
          autoExpandOnCondition: true,
          condition,
        }),
      { initialProps: { condition: true } },
    );

    expect(result.current.isExpanded).toBe(true);

    rerender({ condition: false });

    expect(result.current.isExpanded).toBe(true); // Still expanded from previous condition
  });

  it("should handle multiple toggles and setExpanded calls", () => {
    const { result } = renderHook(() =>
      useCollapsibleSection({ initialExpanded: false }),
    );

    act(() => {
      result.current.toggle();
      result.current.setExpanded(false);
      result.current.toggle();
      result.current.setExpanded(true);
    });

    expect(result.current.isExpanded).toBe(true);
  });

  it("should maintain state when condition changes but autoExpandOnCondition is false", () => {
    const { result, rerender } = renderHook(
      ({ condition }) =>
        useCollapsibleSection({
          initialExpanded: false,
          autoExpandOnCondition: false,
          condition,
        }),
      { initialProps: { condition: false } },
    );

    act(() => {
      result.current.setExpanded(true);
    });

    expect(result.current.isExpanded).toBe(true);

    rerender({ condition: true });

    expect(result.current.isExpanded).toBe(true);
  });
});
