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

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { highlightText } from "./textHighlight";

describe("textHighlight utils", () => {
  describe("highlightText", () => {
    it("should return text as-is when query is empty", () => {
      const result = highlightText("Hello World", "");
      expect(result).toBe("Hello World");
    });

    it("should return text as-is when query is only whitespace", () => {
      const result = highlightText("Hello World", "   ");
      expect(result).toBe("Hello World");
    });

    it("should highlight matching text (case-insensitive)", () => {
      const { container } = render(highlightText("Hello World", "hello"));
      const span = container.querySelector("span");
      expect(span).toBeTruthy();
      expect(span?.textContent).toBe("Hello");
    });

    it("should preserve original case in highlighted text", () => {
      const { container } = render(highlightText("Hello World", "HELLO"));
      const span = container.querySelector("span");
      expect(span?.textContent).toBe("Hello");
    });

    it("should highlight text in the middle", () => {
      const { container } = render(highlightText("Hello World", "wor"));
      const span = container.querySelector("span");
      expect(span?.textContent).toBe("Wor");
    });

    it("should return text as-is when no match found", () => {
      const result = highlightText("Hello World", "xyz");
      expect(result).toBe("Hello World");
    });

    it("should handle text before and after match", () => {
      const { container } = render(highlightText("Hello World", "World"));
      const textContent = container.textContent;
      expect(textContent).toBe("Hello World");
      const span = container.querySelector("span");
      expect(span?.textContent).toBe("World");
    });

    it("should use custom highlight class name", () => {
      const { container } = render(
        highlightText("Hello World", "Hello", "custom-highlight"),
      );
      const span = container.querySelector("span");
      expect(span?.className).toBe("custom-highlight");
    });

    it("should use empty string as default class name", () => {
      const { container } = render(highlightText("Hello World", "Hello"));
      const span = container.querySelector("span");
      expect(span?.className).toBe("");
    });

    it("should handle multiple occurrences (only first match)", () => {
      const { container } = render(highlightText("Hello Hello World", "Hello"));
      const spans = container.querySelectorAll("span");
      expect(spans).toHaveLength(1);
      expect(spans[0]?.textContent).toBe("Hello");
    });

    it("should handle special characters in query", () => {
      const { container } = render(highlightText("Hello (World)", "("));
      const span = container.querySelector("span");
      expect(span?.textContent).toBe("(");
    });

    it("should handle unicode characters", () => {
      const { container } = render(highlightText("Hello 世界", "世界"));
      const span = container.querySelector("span");
      expect(span?.textContent).toBe("世界");
    });
  });
});
