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

import { describe, expect, it } from "vitest";
import type { PageColor } from "@/components/reading/ReadingThemeSettings";
import { createReaderStyles, createTocHoverStyles } from "./epubReaderStyles";

describe("epubReaderStyles", () => {
  describe("createReaderStyles", () => {
    it.each([
      { pageColor: "dark" as PageColor, isDark: true },
      { pageColor: "light" as PageColor, isDark: false },
      { pageColor: "sepia" as PageColor, isDark: false },
      { pageColor: "lightGreen" as PageColor, isDark: false },
    ])(
      "should create reader styles for $pageColor theme",
      ({ pageColor, isDark }) => {
        const styles = createReaderStyles(pageColor);

        expect(styles).toBeDefined();
        expect(styles.readerArea).toBeDefined();
        expect(styles.readerArea.backgroundColor).toBeDefined();
        expect(styles.readerArea.transition).toBeUndefined();
        expect(styles.titleArea).toBeDefined();
        expect(styles.tocArea).toBeDefined();
        expect(styles.tocAreaButton).toBeDefined();
        expect(styles.tocBackground).toBeDefined();
        expect(styles.tocButtonExpanded).toBeDefined();
        expect(styles.tocButton).toBeDefined();
        expect(styles.tocButton.display).toBe("none");

        if (isDark) {
          expect(styles.arrow).toBeDefined();
          expect(styles.arrow.color).toBe("#fff");
          expect(styles.arrowHover).toBeDefined();
          expect(styles.arrowHover.color).toBe("#ccc");
          expect(styles.titleArea.color).toBe("#ccc");
          expect(styles.tocButton.color).toBe("white");
        } else {
          expect(styles.titleArea.color).toBeDefined();
        }
      },
    );

    it("should include all ReactReaderStyle properties for dark theme", () => {
      const styles = createReaderStyles("dark");
      // Verify that styles extend ReactReaderStyle by checking for common properties
      expect(styles.readerArea).toBeDefined();
      expect(styles.titleArea).toBeDefined();
      expect(styles.tocArea).toBeDefined();
    });

    it("should include all ReactReaderStyle properties for light theme", () => {
      const styles = createReaderStyles("light");
      expect(styles.readerArea).toBeDefined();
      expect(styles.titleArea).toBeDefined();
      expect(styles.tocArea).toBeDefined();
    });

    it("should set correct colors for dark theme", () => {
      const styles = createReaderStyles("dark");
      expect(styles.readerArea.backgroundColor).toBe("#0b0e14");
      expect(styles.titleArea.color).toBe("#ccc");
      expect(styles.tocArea.background).toBe("#1a1d24");
      expect(styles.tocAreaButton.color).toBe("#ccc");
      expect(styles.tocAreaButton.borderBottom).toContain("#333");
      expect(styles.tocBackground.background).toBe("rgba(0, 0, 0, 0.5)");
      expect(styles.tocButtonExpanded.background).toBe("#1a1d24");
      expect(styles.tocButtonBar.background).toBe("#e0e0e0");
    });

    it("should set correct colors for light theme", () => {
      const styles = createReaderStyles("light");
      expect(styles.readerArea.backgroundColor).toBe("#f1f1f1");
      expect(styles.titleArea.color).toBe("#000");
      expect(styles.tocArea.background).toBe("#e8e8e8");
      expect(styles.tocAreaButton.color).toBe("#666");
      expect(styles.tocAreaButton.borderBottom).toContain("#d0d0d0");
      expect(styles.tocBackground.background).toBe("rgba(0, 0, 0, 0.3)");
      expect(styles.tocButtonExpanded.background).toBe("#e8e8e8");
    });

    it("should set correct colors for sepia theme", () => {
      const styles = createReaderStyles("sepia");
      expect(styles.readerArea.backgroundColor).toBe("#f4e4c1");
      expect(styles.titleArea.color).toBe("#000");
      expect(styles.tocArea.background).toBe("#e8d9b8");
      expect(styles.tocAreaButton.color).toBe("#555");
      expect(styles.tocAreaButton.borderBottom).toContain("#d4c5a4");
      expect(styles.tocBackground.background).toBe("rgba(0, 0, 0, 0.3)");
      expect(styles.tocButtonExpanded.background).toBe("#e8d9b8");
    });

    it("should set correct colors for lightGreen theme", () => {
      const styles = createReaderStyles("lightGreen");
      expect(styles.readerArea.backgroundColor).toBe("#e8f5e9");
      expect(styles.titleArea.color).toBe("#000");
      expect(styles.tocArea.background).toBe("#d4e8d5");
      expect(styles.tocAreaButton.color).toBe("#2d5a2d");
      expect(styles.tocAreaButton.borderBottom).toContain("#c0d8c1");
      expect(styles.tocBackground.background).toBe("rgba(0, 0, 0, 0.2)");
      expect(styles.tocButtonExpanded.background).toBe("#d4e8d5");
    });
  });

  describe("createTocHoverStyles", () => {
    it.each([
      { pageColor: "dark" as PageColor, isDark: true },
      { pageColor: "light" as PageColor, isDark: false },
      { pageColor: "sepia" as PageColor, isDark: false },
      { pageColor: "lightGreen" as PageColor, isDark: false },
    ])(
      "should create TOC hover styles for $pageColor theme",
      ({ pageColor, isDark }) => {
        const css = createTocHoverStyles(pageColor);

        expect(css).toBeDefined();
        expect(typeof css).toBe("string");
        expect(css).toContain('div[style*="overflowY"] button:hover');
        expect(css).toContain("background-color");
        expect(css).toContain("color");
        expect(css).toContain("transition");

        if (isDark) {
          expect(css).toContain("rgba(255, 255, 255, 0.1)");
        } else {
          expect(css).toContain("rgba(0, 0, 0, 0.05)");
        }
      },
    );

    it("should include correct hover background for dark theme", () => {
      const css = createTocHoverStyles("dark");
      expect(css).toContain("rgba(255, 255, 255, 0.1)");
      expect(css).toContain("!important");
    });

    it("should include correct hover background for light theme", () => {
      const css = createTocHoverStyles("light");
      expect(css).toContain("rgba(0, 0, 0, 0.05)");
      expect(css).toContain("!important");
    });

    it("should include transition properties", () => {
      const css = createTocHoverStyles("light");
      expect(css).toContain(
        "transition: background-color 0.2s ease, color 0.2s ease",
      );
    });

    it("should include buttonHoverColor from TOC colors", () => {
      const cssDark = createTocHoverStyles("dark");
      const cssLight = createTocHoverStyles("light");
      // The actual color value comes from getTocColors, but we verify it's included
      expect(cssDark).toContain("color:");
      expect(cssLight).toContain("color:");
    });
  });
});
