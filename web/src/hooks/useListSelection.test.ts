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
import { useListSelection } from "./useListSelection";

describe("useListSelection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("initialization", () => {
    it.each([
      { itemCount: 0, initialIndex: undefined, expected: -1 },
      { itemCount: 5, initialIndex: undefined, expected: -1 },
      { itemCount: 5, initialIndex: -1, expected: -1 },
      { itemCount: 5, initialIndex: 0, expected: 0 },
      { itemCount: 5, initialIndex: 2, expected: 2 },
      { itemCount: 5, initialIndex: 4, expected: 4 },
    ])(
      "should initialize with itemCount=$itemCount, initialIndex=$initialIndex",
      ({ itemCount, initialIndex, expected }) => {
        const { result } = renderHook(() =>
          useListSelection({
            itemCount,
            ...(initialIndex !== undefined && { initialIndex }),
          }),
        );

        expect(result.current.selectedIndex).toBe(expected);
        expect(result.current.hoveredIndex).toBe(-1);
      },
    );
  });

  describe("setSelectedIndex", () => {
    it.each([{ index: -1 }, { index: 0 }, { index: 2 }, { index: 4 }])(
      "should set selected index to $index",
      ({ index }) => {
        const { result } = renderHook(() => useListSelection({ itemCount: 5 }));

        act(() => {
          result.current.setSelectedIndex(index);
        });

        expect(result.current.selectedIndex).toBe(index);
      },
    );
  });

  describe("setHoveredIndex", () => {
    it.each([{ index: -1 }, { index: 0 }, { index: 2 }, { index: 4 }])(
      "should set hovered index to $index",
      ({ index }) => {
        const { result } = renderHook(() => useListSelection({ itemCount: 5 }));

        act(() => {
          result.current.setHoveredIndex(index);
        });

        expect(result.current.hoveredIndex).toBe(index);
      },
    );
  });

  describe("selectNext", () => {
    it.each([
      { itemCount: 0, prevIndex: -1, expected: -1 },
      { itemCount: 5, prevIndex: -1, expected: 0 },
      { itemCount: 5, prevIndex: 0, expected: 1 },
      { itemCount: 5, prevIndex: 3, expected: 4 },
      { itemCount: 5, prevIndex: 4, expected: 0 }, // Wraps around
    ])(
      "should select next with itemCount=$itemCount, prevIndex=$prevIndex",
      ({ itemCount, prevIndex, expected }) => {
        const { result } = renderHook(() => useListSelection({ itemCount }));

        if (prevIndex >= 0) {
          act(() => {
            result.current.setSelectedIndex(prevIndex);
          });
        }

        act(() => {
          result.current.selectNext();
        });

        expect(result.current.selectedIndex).toBe(expected);
      },
    );

    it("should not select next when disabled", () => {
      const { result } = renderHook(() =>
        useListSelection({ itemCount: 5, enabled: false }),
      );

      act(() => {
        result.current.setSelectedIndex(2);
      });

      act(() => {
        result.current.selectNext();
      });

      expect(result.current.selectedIndex).toBe(2); // Unchanged
    });
  });

  describe("selectPrevious", () => {
    it.each([
      { itemCount: 0, prevIndex: -1, expected: -1 },
      { itemCount: 5, prevIndex: -1, expected: 4 }, // Wraps to last
      { itemCount: 5, prevIndex: 0, expected: 4 }, // Wraps around
      { itemCount: 5, prevIndex: 1, expected: 0 },
      { itemCount: 5, prevIndex: 4, expected: 3 },
    ])(
      "should select previous with itemCount=$itemCount, prevIndex=$prevIndex",
      ({ itemCount, prevIndex, expected }) => {
        const { result } = renderHook(() => useListSelection({ itemCount }));

        if (prevIndex >= 0) {
          act(() => {
            result.current.setSelectedIndex(prevIndex);
          });
        }

        act(() => {
          result.current.selectPrevious();
        });

        expect(result.current.selectedIndex).toBe(expected);
      },
    );

    it("should not select previous when disabled", () => {
      const { result } = renderHook(() =>
        useListSelection({ itemCount: 5, enabled: false }),
      );

      act(() => {
        result.current.setSelectedIndex(2);
      });

      act(() => {
        result.current.selectPrevious();
      });

      expect(result.current.selectedIndex).toBe(2); // Unchanged
    });
  });

  describe("reset", () => {
    it("should reset selected index to -1", () => {
      const { result } = renderHook(() =>
        useListSelection({ itemCount: 5, initialIndex: 2 }),
      );

      expect(result.current.selectedIndex).toBe(2);

      act(() => {
        result.current.reset();
      });

      expect(result.current.selectedIndex).toBe(-1);
      expect(result.current.hoveredIndex).toBe(-1); // Unchanged
    });
  });

  describe("resetHover", () => {
    it("should reset hovered index to -1", () => {
      const { result } = renderHook(() => useListSelection({ itemCount: 5 }));

      act(() => {
        result.current.setHoveredIndex(3);
      });

      expect(result.current.hoveredIndex).toBe(3);

      act(() => {
        result.current.resetHover();
      });

      expect(result.current.hoveredIndex).toBe(-1);
      expect(result.current.selectedIndex).toBe(-1); // Unchanged
    });
  });

  describe("resetAll", () => {
    it("should reset both selected and hovered indices to -1", () => {
      const { result } = renderHook(() =>
        useListSelection({ itemCount: 5, initialIndex: 2 }),
      );

      act(() => {
        result.current.setHoveredIndex(3);
      });

      expect(result.current.selectedIndex).toBe(2);
      expect(result.current.hoveredIndex).toBe(3);

      act(() => {
        result.current.resetAll();
      });

      expect(result.current.selectedIndex).toBe(-1);
      expect(result.current.hoveredIndex).toBe(-1);
    });
  });

  describe("enabled state", () => {
    it("should allow operations when enabled is true", () => {
      const { result } = renderHook(() =>
        useListSelection({ itemCount: 5, enabled: true }),
      );

      act(() => {
        result.current.selectNext();
      });

      expect(result.current.selectedIndex).toBe(0);
    });

    it("should prevent operations when enabled is false", () => {
      const { result } = renderHook(() =>
        useListSelection({ itemCount: 5, enabled: false }),
      );

      act(() => {
        result.current.selectNext();
        result.current.selectPrevious();
      });

      expect(result.current.selectedIndex).toBe(-1);
    });
  });
});
