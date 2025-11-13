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

import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  calculateContainerScrollPosition,
  calculateScrollPosition,
  findScrollableParent,
  scrollContainerTo,
  scrollWindowTo,
} from "./scroll";

describe("scroll utils", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.body.innerHTML = "";
    window.scrollY = 0;
  });

  describe("findScrollableParent", () => {
    it("should return element with overflow auto", () => {
      const parent = document.createElement("div");
      parent.style.overflow = "auto";
      const child = document.createElement("div");
      parent.appendChild(child);
      document.body.appendChild(parent);

      const result = findScrollableParent(child);
      expect(result).toBe(parent);
    });

    it("should return element with overflow scroll", () => {
      const parent = document.createElement("div");
      parent.style.overflow = "scroll";
      const child = document.createElement("div");
      parent.appendChild(child);
      document.body.appendChild(parent);

      const result = findScrollableParent(child);
      expect(result).toBe(parent);
    });

    it("should return element with overflowY auto", () => {
      const parent = document.createElement("div");
      parent.style.overflowY = "auto";
      const child = document.createElement("div");
      parent.appendChild(child);
      document.body.appendChild(parent);

      const result = findScrollableParent(child);
      expect(result).toBe(parent);
    });

    it("should return element with overflowY scroll", () => {
      const parent = document.createElement("div");
      parent.style.overflowY = "scroll";
      const child = document.createElement("div");
      parent.appendChild(child);
      document.body.appendChild(parent);

      const result = findScrollableParent(child);
      expect(result).toBe(parent);
    });

    it("should return null when no scrollable parent exists", () => {
      const child = document.createElement("div");
      document.body.appendChild(child);

      const result = findScrollableParent(child);
      expect(result).toBeNull();
    });

    it("should find scrollable parent in nested hierarchy", () => {
      const grandparent = document.createElement("div");
      grandparent.style.overflow = "auto";
      const parent = document.createElement("div");
      const child = document.createElement("div");
      parent.appendChild(child);
      grandparent.appendChild(parent);
      document.body.appendChild(grandparent);

      const result = findScrollableParent(child);
      expect(result).toBe(grandparent);
    });

    it("should return first scrollable parent when multiple exist", () => {
      const outer = document.createElement("div");
      outer.style.overflow = "auto";
      const inner = document.createElement("div");
      inner.style.overflow = "scroll";
      const child = document.createElement("div");
      inner.appendChild(child);
      outer.appendChild(inner);
      document.body.appendChild(outer);

      const result = findScrollableParent(child);
      expect(result).toBe(inner);
    });
  });

  describe("calculateScrollPosition", () => {
    it("should return null when both elements are visible", () => {
      const headerRect = new DOMRect(10, 10, 100, 50);
      const targetRect = new DOMRect(10, 200, 100, 50);
      const viewportHeight = 1000;

      const result = calculateScrollPosition(
        headerRect,
        targetRect,
        viewportHeight,
      );

      expect(result).toBeNull();
    });

    it("should calculate scroll position when target is below viewport", () => {
      const headerRect = new DOMRect(10, 10, 100, 50);
      const targetRect = new DOMRect(10, 1200, 100, 50);
      const viewportHeight = 1000;
      window.scrollY = 0;

      const result = calculateScrollPosition(
        headerRect,
        targetRect,
        viewportHeight,
      );

      expect(result).toBeGreaterThan(0);
      expect(typeof result).toBe("number");
    });

    it("should use custom padding values", () => {
      const headerRect = new DOMRect(10, 10, 100, 50);
      const targetRect = new DOMRect(10, 1200, 100, 50);
      const viewportHeight = 1000;
      window.scrollY = 0;

      const resultWithPadding = calculateScrollPosition(
        headerRect,
        targetRect,
        viewportHeight,
        50,
        100,
      );

      const resultDefault = calculateScrollPosition(
        headerRect,
        targetRect,
        viewportHeight,
      );

      expect(resultWithPadding).not.toBe(resultDefault);
    });

    it("should account for window scrollY", () => {
      const headerRect = new DOMRect(10, 10, 100, 50);
      const targetRect = new DOMRect(10, 1200, 100, 50);
      const viewportHeight = 1000;
      window.scrollY = 500;

      const result = calculateScrollPosition(
        headerRect,
        targetRect,
        viewportHeight,
      );

      expect(result).toBeGreaterThan(0);
    });
  });

  describe("calculateContainerScrollPosition", () => {
    it("should calculate scroll position for container", () => {
      const container = document.createElement("div");
      container.scrollTop = 100;
      const headerRect = new DOMRect(10, 10, 100, 50);
      const targetRect = new DOMRect(10, 200, 100, 50);

      const result = calculateContainerScrollPosition(
        container,
        headerRect,
        targetRect,
      );

      expect(typeof result).toBe("number");
    });

    it("should use custom padding values", () => {
      const container = document.createElement("div");
      container.scrollTop = 100;
      const headerRect = new DOMRect(10, 10, 100, 50);
      const targetRect = new DOMRect(10, 200, 100, 50);

      const resultWithPadding = calculateContainerScrollPosition(
        container,
        headerRect,
        targetRect,
        50,
        100,
      );

      const resultDefault = calculateContainerScrollPosition(
        container,
        headerRect,
        targetRect,
      );

      expect(resultWithPadding).not.toBe(resultDefault);
    });

    it("should handle container with getBoundingClientRect", () => {
      const container = document.createElement("div");
      container.scrollTop = 0;
      vi.spyOn(container, "getBoundingClientRect").mockReturnValue(
        new DOMRect(0, 0, 800, 600),
      );
      const headerRect = new DOMRect(10, 10, 100, 50);
      const targetRect = new DOMRect(10, 700, 100, 50);

      const result = calculateContainerScrollPosition(
        container,
        headerRect,
        targetRect,
      );

      expect(typeof result).toBe("number");
    });
  });

  describe("scrollWindowTo", () => {
    it("should scroll window to position with default behavior", () => {
      const scrollToSpy = vi.spyOn(window, "scrollTo");

      scrollWindowTo(500);

      expect(scrollToSpy).toHaveBeenCalledWith({
        top: 500,
        behavior: "smooth",
      });
    });

    it("should scroll window to position with custom behavior", () => {
      const scrollToSpy = vi.spyOn(window, "scrollTo");

      scrollWindowTo(500, "auto");

      expect(scrollToSpy).toHaveBeenCalledWith({
        top: 500,
        behavior: "auto",
      });
    });

    it.each([
      [0, "smooth"],
      [100, "smooth"],
      [1000, "auto"],
      [-100, "smooth"],
    ])(
      "should scroll to position %d with behavior %s",
      (position, behavior) => {
        const scrollToSpy = vi.spyOn(window, "scrollTo");

        scrollWindowTo(position, behavior as ScrollBehavior);

        expect(scrollToSpy).toHaveBeenCalledWith({
          top: position,
          behavior,
        });
      },
    );
  });

  describe("scrollContainerTo", () => {
    it("should scroll container to position with default behavior", () => {
      const container = document.createElement("div");
      const scrollToSpy = vi.spyOn(container, "scrollTo");

      scrollContainerTo(container, 500);

      expect(scrollToSpy).toHaveBeenCalledWith({
        top: 500,
        behavior: "smooth",
      });
    });

    it("should scroll container to position with custom behavior", () => {
      const container = document.createElement("div");
      const scrollToSpy = vi.spyOn(container, "scrollTo");

      scrollContainerTo(container, 500, "auto");

      expect(scrollToSpy).toHaveBeenCalledWith({
        top: 500,
        behavior: "auto",
      });
    });

    it.each([
      [0, "smooth"],
      [100, "smooth"],
      [1000, "auto"],
      [-100, "smooth"],
    ])(
      "should scroll container to position %d with behavior %s",
      (position, behavior) => {
        const container = document.createElement("div");
        const scrollToSpy = vi.spyOn(container, "scrollTo");

        scrollContainerTo(container, position, behavior as ScrollBehavior);

        expect(scrollToSpy).toHaveBeenCalledWith({
          top: position,
          behavior,
        });
      },
    );
  });
});
