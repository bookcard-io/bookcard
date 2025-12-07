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

import type { Contents, Rendition } from "epubjs";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  FontFamily,
  PageColor,
} from "@/components/reading/ReadingThemeSettings";
import {
  applyDocumentTheme,
  applyThemeToRendition,
  createContentHook,
  ensureFontFacesInjected,
  refreshPageForTheme,
} from "./epubRendering";

/**
 * Create a mock rendition with themes.
 */
function createMockRendition(): Rendition {
  const themes = {
    override: vi.fn(),
    fontSize: vi.fn(),
  };
  return {
    themes,
  } as unknown as Rendition;
}

/**
 * Create a mock document.
 */
function createMockDocument(): Document {
  const head = {
    appendChild: vi.fn(),
  };
  const getElementById = vi.fn();
  const createElement = vi.fn((tag: string) => {
    if (tag === "style") {
      return {
        id: "",
        appendChild: vi.fn(),
      } as unknown as HTMLStyleElement;
    }
    return {} as HTMLElement;
  });
  const createTextNode = vi.fn((text: string) => text);

  return {
    head,
    getElementById,
    createElement,
    createTextNode,
    body: {
      style: {
        color: "",
        backgroundColor: "",
        setProperty: vi.fn(),
      },
    },
    querySelector: vi.fn(),
  } as unknown as Document;
}

/**
 * Create a mock contents object.
 */
function createMockContents(document: Document): Contents {
  return {
    window: {
      document,
    },
  } as unknown as Contents;
}

describe("epubRendering", () => {
  describe("applyThemeToRendition", () => {
    it.each([
      {
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
      },
      {
        pageColor: "dark" as PageColor,
        fontFamily: "Amazon Ember" as FontFamily,
        fontSize: 18,
      },
      {
        pageColor: "sepia" as PageColor,
        fontFamily: "Literata" as FontFamily,
        fontSize: 14,
      },
      {
        pageColor: "lightGreen" as PageColor,
        fontFamily: "OpenDyslexic" as FontFamily,
        fontSize: 20,
      },
    ])(
      "should apply theme for $pageColor, $fontFamily, fontSize $fontSize",
      ({ pageColor, fontFamily, fontSize }) => {
        const rendition = createMockRendition();
        applyThemeToRendition(rendition, pageColor, fontFamily, fontSize);

        expect(rendition.themes.override).toHaveBeenCalledWith(
          "color",
          expect.any(String),
        );
        expect(rendition.themes.override).toHaveBeenCalledWith(
          "background",
          expect.any(String),
        );
        expect(rendition.themes.override).toHaveBeenCalledWith(
          "font-family",
          `"${fontFamily}"`,
        );
        expect(rendition.themes.fontSize).toHaveBeenCalledWith(
          expect.stringContaining("%"),
        );
      },
    );

    it("should convert fontSize to percentage", () => {
      const rendition = createMockRendition();
      applyThemeToRendition(rendition, "light", "Bookerly", 16);
      expect(rendition.themes.fontSize).toHaveBeenCalledWith("100%");
    });

    it("should apply correct colors for light theme", () => {
      const rendition = createMockRendition();
      applyThemeToRendition(rendition, "light", "Bookerly", 16);
      expect(rendition.themes.override).toHaveBeenCalledWith("color", "#000");
      expect(rendition.themes.override).toHaveBeenCalledWith(
        "background",
        "#f1f1f1",
      );
    });

    it("should apply correct colors for dark theme", () => {
      const rendition = createMockRendition();
      applyThemeToRendition(rendition, "dark", "Bookerly", 16);
      expect(rendition.themes.override).toHaveBeenCalledWith("color", "#fff");
      expect(rendition.themes.override).toHaveBeenCalledWith(
        "background",
        "#0b0e14",
      );
    });
  });

  describe("ensureFontFacesInjected", () => {
    it("should inject font faces when not present", () => {
      const document = createMockDocument();
      document.getElementById = vi.fn().mockReturnValue(null);

      ensureFontFacesInjected(document);

      expect(document.getElementById).toHaveBeenCalledWith("epub-reader-fonts");
      expect(document.createElement).toHaveBeenCalledWith("style");
      expect(document.head.appendChild).toHaveBeenCalled();
    });

    it("should not inject font faces when already present", () => {
      const document = createMockDocument();
      const existingStyle = { id: "epub-reader-fonts" } as HTMLStyleElement;
      document.getElementById = vi.fn().mockReturnValue(existingStyle);

      ensureFontFacesInjected(document);

      expect(document.getElementById).toHaveBeenCalledWith("epub-reader-fonts");
      expect(document.createElement).not.toHaveBeenCalled();
      expect(document.head.appendChild).not.toHaveBeenCalled();
    });

    it("should set correct id on style element", () => {
      const document = createMockDocument();
      document.getElementById = vi.fn().mockReturnValue(null);
      const styleElement = {
        id: "",
        appendChild: vi.fn(),
      } as unknown as HTMLStyleElement;
      document.createElement = vi.fn().mockReturnValue(styleElement);

      ensureFontFacesInjected(document);

      expect(styleElement.id).toBe("epub-reader-fonts");
    });
  });

  describe("applyDocumentTheme", () => {
    it("should apply theme to document body", () => {
      const document = createMockDocument();
      const colors = { textColor: "#000", backgroundColor: "#fff" };

      applyDocumentTheme(document, colors);

      expect(document.body.style.color).toBe("#000");
      expect(document.body.style.backgroundColor).toBe("#fff");
    });

    it("should apply theme to iframe contentDocument body when present", () => {
      const document = createMockDocument();
      const setProperty = vi.fn();
      const iframeBody = {
        style: {
          color: "",
          backgroundColor: "",
          fontFamily: "",
          setProperty,
        },
      };
      const iframe = {
        contentDocument: {
          body: iframeBody,
        },
      };
      document.querySelector = vi.fn().mockReturnValue(iframe);
      const colors = { textColor: "#000", backgroundColor: "#fff" };

      applyDocumentTheme(document, colors, "Bookerly");

      expect(iframeBody.style.color).toBe("#000");
      expect(iframeBody.style.backgroundColor).toBe("#fff");
      expect(setProperty).toHaveBeenCalledWith(
        "font-family",
        '"Bookerly"',
        "important",
      );
    });

    it("should apply theme including font family to document body with correct global override", () => {
      const document = createMockDocument();
      const setProperty = vi.fn();
      document.body.style.setProperty = setProperty;

      const styleElement = {
        id: "epub-font-override",
        textContent: "",
        appendChild: vi.fn(),
      };
      document.createElement = vi.fn().mockReturnValue(styleElement);

      const colors = { textColor: "#000", backgroundColor: "#fff" };

      applyDocumentTheme(document, colors, "Bookerly");

      expect(document.body.style.color).toBe("#000");
      expect(document.body.style.backgroundColor).toBe("#fff");
      expect(setProperty).toHaveBeenCalledWith(
        "font-family",
        '"Bookerly"',
        "important",
      );
      expect(document.createElement).toHaveBeenCalledWith("style");

      // Verify the global override style content
      expect(styleElement.textContent).toContain(
        'font-family: "Bookerly" !important',
      );
      expect(styleElement.textContent).toContain("p, span, div");
      expect(styleElement.textContent).not.toContain("pre");
      expect(styleElement.textContent).not.toContain("code");
    });

    it("should handle missing iframe gracefully", () => {
      const document = createMockDocument();
      document.querySelector = vi.fn().mockReturnValue(null);
      const colors = { textColor: "#000", backgroundColor: "#fff" };

      expect(() => applyDocumentTheme(document, colors)).not.toThrow();
    });

    it("should handle iframe without contentDocument gracefully", () => {
      const document = createMockDocument();
      const iframe = {
        contentDocument: null,
      };
      document.querySelector = vi.fn().mockReturnValue(iframe);
      const colors = { textColor: "#000", backgroundColor: "#fff" };

      expect(() => applyDocumentTheme(document, colors)).not.toThrow();
    });

    it("should handle iframe contentDocument without body gracefully", () => {
      const document = createMockDocument();
      const iframe = {
        contentDocument: {
          body: null,
        },
      };
      document.querySelector = vi.fn().mockReturnValue(iframe);
      const colors = { textColor: "#000", backgroundColor: "#fff" };

      expect(() => applyDocumentTheme(document, colors)).not.toThrow();
    });
  });

  describe("createContentHook", () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    it("should return a function", () => {
      const rendition = createMockRendition();
      const pageColorRef = { current: "light" as PageColor };
      const fontFamilyRef = { current: "Bookerly" as FontFamily };
      const fontSizeRef = { current: 16 };

      const hook = createContentHook(
        rendition,
        pageColorRef,
        fontFamilyRef,
        fontSizeRef,
      );

      expect(typeof hook).toBe("function");
    });

    it("should apply font faces and theme when called", () => {
      const rendition = createMockRendition();
      const pageColorRef = { current: "light" as PageColor };
      const fontFamilyRef = { current: "Bookerly" as FontFamily };
      const fontSizeRef = { current: 16 };
      const document = createMockDocument();
      document.getElementById = vi.fn().mockReturnValue(null);
      const contents = createMockContents(document);

      const hook = createContentHook(
        rendition,
        pageColorRef,
        fontFamilyRef,
        fontSizeRef,
      );
      hook(contents);

      expect(document.getElementById).toHaveBeenCalledWith("epub-reader-fonts");
      expect(rendition.themes.override).toHaveBeenCalled();
      expect(document.body.style.color).toBeDefined();
    });

    it("should return early when document is null", () => {
      const rendition = createMockRendition();
      const pageColorRef = { current: "light" as PageColor };
      const fontFamilyRef = { current: "Bookerly" as FontFamily };
      const fontSizeRef = { current: 16 };
      const contents = {
        window: {
          document: null,
        },
      } as unknown as Contents;

      const hook = createContentHook(
        rendition,
        pageColorRef,
        fontFamilyRef,
        fontSizeRef,
      );
      expect(() => hook(contents)).not.toThrow();
    });

    it("should use current ref values", () => {
      const rendition = createMockRendition();
      const pageColorRef = { current: "dark" as PageColor };
      const fontFamilyRef = { current: "Amazon Ember" as FontFamily };
      const fontSizeRef = { current: 18 };
      const document = createMockDocument();
      document.getElementById = vi.fn().mockReturnValue(null);
      const contents = createMockContents(document);

      const hook = createContentHook(
        rendition,
        pageColorRef,
        fontFamilyRef,
        fontSizeRef,
      );
      hook(contents);

      expect(rendition.themes.override).toHaveBeenCalledWith("color", "#fff");
      expect(rendition.themes.override).toHaveBeenCalledWith(
        "font-family",
        '"Amazon Ember"',
      );
    });
  });

  describe("refreshPageForTheme", () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    it("should refresh page when rendition and location are valid", () => {
      const rendition = createMockRendition();
      rendition.display = vi.fn();
      const isNavigatingRef = { current: false };
      const currentLocation = "epubcfi(/6/4[chap01ref]!/4/2/2)";

      refreshPageForTheme(rendition, currentLocation, isNavigatingRef);

      vi.advanceTimersByTime(50);

      expect(rendition.display).toHaveBeenCalledWith(currentLocation);
    });

    it("should not refresh when rendition is undefined", () => {
      const isNavigatingRef = { current: false };
      const currentLocation = "epubcfi(/6/4[chap01ref]!/4/2/2)";

      refreshPageForTheme(undefined, currentLocation, isNavigatingRef);

      vi.advanceTimersByTime(50);
      // Should not throw
    });

    it("should not refresh when location is null", () => {
      const rendition = createMockRendition();
      rendition.display = vi.fn();
      const isNavigatingRef = { current: false };

      refreshPageForTheme(
        rendition,
        null as unknown as string,
        isNavigatingRef,
      );

      vi.advanceTimersByTime(50);
      expect(rendition.display).not.toHaveBeenCalled();
    });

    it("should not refresh when location is number", () => {
      const rendition = createMockRendition();
      rendition.display = vi.fn();
      const isNavigatingRef = { current: false };

      refreshPageForTheme(rendition, 1 as unknown as string, isNavigatingRef);

      vi.advanceTimersByTime(50);
      expect(rendition.display).not.toHaveBeenCalled();
    });

    it("should not refresh when isNavigating is true", () => {
      const rendition = createMockRendition();
      rendition.display = vi.fn();
      const isNavigatingRef = { current: true };
      const currentLocation = "epubcfi(/6/4[chap01ref]!/4/2/2)";

      refreshPageForTheme(rendition, currentLocation, isNavigatingRef);

      vi.advanceTimersByTime(50);
      expect(rendition.display).not.toHaveBeenCalled();
    });

    it("should not refresh if isNavigating becomes true during delay", () => {
      const rendition = createMockRendition();
      rendition.display = vi.fn();
      const isNavigatingRef = { current: false };
      const currentLocation = "epubcfi(/6/4[chap01ref]!/4/2/2)";

      refreshPageForTheme(rendition, currentLocation, isNavigatingRef);
      isNavigatingRef.current = true;

      vi.advanceTimersByTime(50);
      expect(rendition.display).not.toHaveBeenCalled();
    });

    it("should not throw synchronously when display throws", () => {
      const rendition = createMockRendition();
      rendition.display = vi.fn(() => {
        throw new Error("Display error");
      });
      const isNavigatingRef = { current: false };
      const currentLocation = "epubcfi(/6/4[chap01ref]!/4/2/2)";

      // The try-catch in refreshPageForTheme wraps the setTimeout call, not the callback
      // Errors in the callback won't be caught, but the function should not throw synchronously
      expect(() => {
        refreshPageForTheme(rendition, currentLocation, isNavigatingRef);
      }).not.toThrow();

      // The error will be thrown asynchronously in the callback
      // We verify the function was called, but the error is unhandled
      expect(() => {
        vi.advanceTimersByTime(50);
      }).toThrow("Display error");
    });

    it("should handle setTimeout error in try-catch", () => {
      const rendition = createMockRendition();
      const isNavigatingRef = { current: false };
      const currentLocation = "epubcfi(/6/4[chap01ref]!/4/2/2)";
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});

      // Mock setTimeout to throw an error
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = vi.fn(() => {
        throw new Error("setTimeout error");
      }) as unknown as typeof setTimeout;

      refreshPageForTheme(rendition, currentLocation, isNavigatingRef);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "Could not refresh page for theme update:",
        expect.any(Error),
      );

      // Restore setTimeout
      global.setTimeout = originalSetTimeout;
      consoleWarnSpy.mockRestore();
    });

    it("should check rendition exists in timeout callback", () => {
      const rendition = createMockRendition();
      rendition.display = vi.fn();
      const isNavigatingRef = { current: false };
      const currentLocation = "epubcfi(/6/4[chap01ref]!/4/2/2)";

      refreshPageForTheme(rendition, currentLocation, isNavigatingRef);
      // The code checks `if (!isNavigatingRef.current && rendition)` in the timeout
      // This test verifies the check exists and works when rendition is truthy
      vi.advanceTimersByTime(50);
      expect(rendition.display).toHaveBeenCalledWith(currentLocation);
    });
  });
});
