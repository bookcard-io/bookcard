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

import type { Book, Rendition } from "epubjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  FontFamily,
  PageColor,
} from "@/components/reading/ReadingThemeSettings";
import * as epubLocation from "./epubLocation";
import * as epubRendering from "./epubRendering";
import { setupRendition } from "./epubRenditionSetup";

/**
 * Create a mock book with locations.
 */
function createMockBook(locations: unknown) {
  const mockLocations = locations || {
    length: 100,
    total: 100,
    locationFromCfi: vi.fn(),
    cfiFromLocation: vi.fn(),
    generate: vi.fn(() => Promise.resolve()),
  };

  return {
    locations: mockLocations,
  } as Book;
}

/**
 * Create a mock rendition.
 */
function createMockRendition(book?: Book): Rendition {
  const mockRendition = {
    book: book || createMockBook(null),
    themes: {
      override: vi.fn(),
      fontSize: vi.fn(),
    },
    hooks: {
      content: {
        register: vi.fn(),
      },
    },
  };
  return mockRendition as unknown as Rendition;
}

describe("epubRenditionSetup", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(epubRendering, "applyThemeToRendition");
    vi.spyOn(epubRendering, "createContentHook");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe("setupRendition", () => {
    it("should store book reference", () => {
      const book = createMockBook(null);
      const rendition = createMockRendition(book);
      const bookRef = { current: null };
      const options = {
        rendition,
        bookRef,
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange: undefined,
        onLocationChange: undefined,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      expect(bookRef.current).toBe(book);
    });

    it("should apply initial CFI when provided", () => {
      const rendition = createMockRendition();
      const applyInitialCfi = vi.fn();
      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        applyInitialCfi,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange: undefined,
        onLocationChange: undefined,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      expect(applyInitialCfi).toHaveBeenCalled();
    });

    it("should not apply initial CFI when not provided", () => {
      const rendition = createMockRendition();
      const applyInitialCfi = vi.fn();
      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange: undefined,
        onLocationChange: undefined,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      expect(applyInitialCfi).not.toHaveBeenCalled();
    });

    it("should apply initial theme", () => {
      const rendition = createMockRendition();
      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "dark" as PageColor,
        fontFamily: "Amazon Ember" as FontFamily,
        fontSize: 18,
        pageColorRef: { current: "dark" as PageColor },
        fontFamilyRef: { current: "Amazon Ember" as FontFamily },
        fontSizeRef: { current: 18 },
        onLocationsReadyChange: undefined,
        onLocationChange: undefined,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      expect(epubRendering.applyThemeToRendition).toHaveBeenCalledWith(
        rendition,
        "dark",
        "Amazon Ember",
        18,
      );
    });

    it("should register content hook", () => {
      const rendition = createMockRendition();
      const pageColorRef = { current: "light" as PageColor };
      const fontFamilyRef = { current: "Bookerly" as FontFamily };
      const fontSizeRef = { current: 16 };
      const mockContentHook = vi.fn();
      vi.mocked(epubRendering.createContentHook).mockReturnValue(
        mockContentHook,
      );

      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef,
        fontFamilyRef,
        fontSizeRef,
        onLocationsReadyChange: undefined,
        onLocationChange: undefined,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      expect(epubRendering.createContentHook).toHaveBeenCalledWith(
        rendition,
        pageColorRef,
        fontFamilyRef,
        fontSizeRef,
      );
      expect(rendition.hooks.content.register).toHaveBeenCalledWith(
        mockContentHook,
      );
    });

    it("should generate locations and notify when ready", async () => {
      const generateMock = vi.fn(() => Promise.resolve());
      const book = createMockBook({
        length: 100,
        total: undefined,
        locationFromCfi: vi.fn(),
        cfiFromLocation: vi.fn(),
        generate: generateMock,
      });
      const rendition = createMockRendition(book);
      const onLocationsReadyChange = vi.fn();
      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange,
        onLocationChange: undefined,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      await vi.runAllTimersAsync();

      expect(generateMock).toHaveBeenCalledWith(200);
      expect(onLocationsReadyChange).toHaveBeenCalledWith(true);
    });

    it("should notify false when locations are not available", async () => {
      const book = {
        locations: null,
      } as unknown as Book;
      const rendition = createMockRendition(book);
      const onLocationsReadyChange = vi.fn();
      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange,
        onLocationChange: undefined,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      await vi.runAllTimersAsync();
      expect(onLocationsReadyChange).toHaveBeenCalledWith(false);
    });

    it("should calculate and update progress from initial CFI when locations are ready", async () => {
      let resolveGenerate: (() => void) | undefined;
      const generatePromise = new Promise<void>((resolve) => {
        resolveGenerate = resolve;
      });
      const generateMock = vi.fn(() => generatePromise);
      const book = createMockBook({
        length: 100,
        total: undefined,
        locationFromCfi: vi.fn(() => 50),
        cfiFromLocation: vi.fn(),
        generate: generateMock,
      });
      const rendition = createMockRendition(book);
      const bookRef = { current: null };
      const onLocationsReadyChange = vi.fn();
      const onLocationChange = vi.fn();
      const initialCfi = "epubcfi(/6/4[chap01ref]!/4/2/2)";
      vi.spyOn(epubLocation, "calculateProgressFromCfi").mockReturnValue(0.5);

      const options = {
        rendition,
        bookRef,
        initialCfi,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange,
        onLocationChange,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      // Resolve the generate promise
      resolveGenerate?.();
      // Wait for the promise chain
      await generatePromise;
      await Promise.resolve();

      // bookRef.current is set to rendition.book in setupRendition, which is the book we passed
      expect(epubLocation.calculateProgressFromCfi).toHaveBeenCalled();
      expect(epubLocation.calculateProgressFromCfi).toHaveBeenCalledWith(
        bookRef.current,
        initialCfi,
      );
      expect(onLocationChange).toHaveBeenCalledWith(initialCfi, 0.5, true);
    });

    it("should handle error when calculating initial progress", async () => {
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      let resolveGenerate: (() => void) | undefined;
      const generatePromise = new Promise<void>((resolve) => {
        resolveGenerate = resolve;
      });
      const generateMock = vi.fn(() => generatePromise);
      const book = createMockBook({
        length: 100,
        total: undefined,
        locationFromCfi: vi.fn(),
        cfiFromLocation: vi.fn(),
        generate: generateMock,
      });
      const rendition = createMockRendition(book);
      const bookRef = { current: null };
      const onLocationsReadyChange = vi.fn();
      const onLocationChange = vi.fn();
      const initialCfi = "epubcfi(/6/4[chap01ref]!/4/2/2)";
      vi.spyOn(epubLocation, "calculateProgressFromCfi").mockImplementation(
        () => {
          throw new Error("Calculation error");
        },
      );

      const options = {
        rendition,
        bookRef,
        initialCfi,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange,
        onLocationChange,
        isInitialLoadRef: { current: true },
      };

      setupRendition(options);

      // Resolve the generate promise
      resolveGenerate?.();
      // Wait for the promise chain
      await generatePromise;
      await Promise.resolve();

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "Error calculating initial progress from CFI:",
        expect.any(Error),
      );
      consoleWarnSpy.mockRestore();
    });

    it("should mark initial load complete after delay", async () => {
      const generateMock = vi.fn(() => Promise.resolve());
      const book = createMockBook({
        length: 100,
        total: undefined,
        locationFromCfi: vi.fn(),
        cfiFromLocation: vi.fn(),
        generate: generateMock,
      });
      const rendition = createMockRendition(book);
      const isInitialLoadRef = { current: true };
      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange: undefined,
        onLocationChange: undefined,
        isInitialLoadRef,
      };

      setupRendition(options);

      await vi.runAllTimersAsync();
      vi.advanceTimersByTime(500);

      expect(isInitialLoadRef.current).toBe(false);
    });

    it("should mark initial load complete even when no callbacks provided", async () => {
      const book = createMockBook(null);
      const rendition = createMockRendition(book);
      const isInitialLoadRef = { current: true };
      const options = {
        rendition,
        bookRef: { current: null },
        initialCfi: null,
        applyInitialCfi: undefined,
        pageColor: "light" as PageColor,
        fontFamily: "Bookerly" as FontFamily,
        fontSize: 16,
        pageColorRef: { current: "light" as PageColor },
        fontFamilyRef: { current: "Bookerly" as FontFamily },
        fontSizeRef: { current: 16 },
        onLocationsReadyChange: undefined,
        onLocationChange: undefined,
        isInitialLoadRef,
      };

      setupRendition(options);

      vi.advanceTimersByTime(500);

      expect(isInitialLoadRef.current).toBe(false);
    });
  });
});
