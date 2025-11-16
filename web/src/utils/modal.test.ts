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

import * as reactDom from "react-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderModalPortal } from "./modal";

vi.mock("react-dom", () => ({
  createPortal: vi.fn((content, container) => ({
    type: "portal",
    content,
    container,
  })),
}));

describe("modal utils", () => {
  let mockBody: HTMLElement;
  let mockContainer: HTMLElement;

  beforeEach(() => {
    // Create mock DOM elements
    mockBody = {
      appendChild: vi.fn(),
      removeChild: vi.fn(),
    } as unknown as HTMLElement;

    mockContainer = {} as HTMLElement;

    // Mock global document if not available
    if (typeof document === "undefined") {
      vi.stubGlobal("document", {
        body: mockBody,
        createElement: vi.fn(() => mockContainer),
      });
    }

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("renderModalPortal", () => {
    it("should render content in default container (document.body)", () => {
      const content = "Test Content";
      const result = renderModalPortal(content);
      expect(result).toBeDefined();
      // Verify createPortal was called with correct arguments
      expect(reactDom.createPortal).toHaveBeenCalledWith(
        content,
        typeof document !== "undefined" ? document.body : mockBody,
      );
      expect(result).toHaveProperty("type", "portal");
    });

    it("should render content in custom container", () => {
      const customContainer = mockContainer;
      const content = "Test Content";
      const result = renderModalPortal(content, customContainer);
      expect(result).toBeDefined();
      expect(reactDom.createPortal).toHaveBeenCalledWith(
        content,
        customContainer,
      );
      expect(result).toHaveProperty("type", "portal");
    });

    it("should handle different content types", () => {
      const container = mockContainer;

      const stringContent = "String content";
      const result1 = renderModalPortal(stringContent, container);
      expect(result1).toBeDefined();
      expect(reactDom.createPortal).toHaveBeenCalledWith(
        stringContent,
        container,
      );

      const numberContent = 123;
      const result2 = renderModalPortal(numberContent, container);
      expect(result2).toBeDefined();
      expect(reactDom.createPortal).toHaveBeenCalledWith(
        numberContent,
        container,
      );

      const nullContent = null;
      const result3 = renderModalPortal(nullContent, container);
      expect(result3).toBeDefined();
      expect(reactDom.createPortal).toHaveBeenCalledWith(
        nullContent,
        container,
      );
    });
  });
});
