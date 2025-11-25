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
import * as epubLocation from "./epubLocation";
import {
  createJumpToProgressHandler,
  createLocationChangedHandler,
} from "./epubLocationHandlers";

/**
 * Create a mock book with locations.
 */
function createMockBook(
  locations: unknown,
  locationFromCfi?: (cfi: string) => number,
  cfiFromLocation?: (loc: number) => string | null,
) {
  const mockLocations = {
    length: 100,
    total: 100,
    locationFromCfi: locationFromCfi || vi.fn((_cfi: string) => 50),
    cfiFromLocation:
      cfiFromLocation ||
      vi.fn((loc: number) => `epubcfi(/6/4[chap${loc}]!/4/2/2)`),
    generate: vi.fn(() => Promise.resolve()),
  };

  return {
    locations: locations || mockLocations,
  } as Book;
}

/**
 * Create a mock rendition.
 */
function createMockRendition(): Rendition {
  return {
    display: vi.fn(),
  } as unknown as Rendition;
}

describe("epubLocationHandlers", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe("createLocationChangedHandler", () => {
    it("should return a function", () => {
      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation: vi.fn(),
        bookRef: { current: null },
        onLocationChange: undefined,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      expect(typeof handler).toBe("function");
    });

    it("should not process when isNavigating is true", () => {
      const setLocation = vi.fn();
      const onLocationChange = vi.fn();
      const options = {
        isNavigatingRef: { current: true },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation,
        bookRef: { current: null },
        onLocationChange,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      expect(setLocation).not.toHaveBeenCalled();
      expect(onLocationChange).not.toHaveBeenCalled();
    });

    it("should update location when different", () => {
      const setLocation = vi.fn();
      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation,
        bookRef: { current: null },
        onLocationChange: undefined,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      expect(setLocation).toHaveBeenCalledWith(
        "epubcfi(/6/4[chap02ref]!/4/2/2)",
      );
    });

    it("should not update location when same", () => {
      const setLocation = vi.fn();
      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation,
        bookRef: { current: null },
        onLocationChange: undefined,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap01ref]!/4/2/2)");

      expect(setLocation).not.toHaveBeenCalled();
    });

    it("should return early when book is null", () => {
      const onLocationChange = vi.fn();
      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation: vi.fn(),
        bookRef: { current: null },
        onLocationChange,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      vi.advanceTimersByTime(100);
      expect(onLocationChange).not.toHaveBeenCalled();
    });

    it("should return early when onLocationChange is undefined", () => {
      const setLocation = vi.fn();
      const book = createMockBook(null);
      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation,
        bookRef: { current: book },
        onLocationChange: undefined,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      vi.advanceTimersByTime(100);
      expect(setLocation).toHaveBeenCalled();
    });

    it("should skip backend update during initial load", () => {
      const onLocationChange = vi.fn();
      const book = createMockBook(null);
      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation: vi.fn(),
        bookRef: { current: book },
        onLocationChange,
        isInitialLoadRef: { current: true },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      vi.advanceTimersByTime(100);
      expect(onLocationChange).toHaveBeenCalledWith(
        "epubcfi(/6/4[chap02ref]!/4/2/2)",
        expect.any(Number),
        true,
      );
    });

    it("should call onLocationChange with progress when locations are ready", async () => {
      const onLocationChange = vi.fn();
      const book = createMockBook(
        {
          length: 100,
          total: 100,
          locationFromCfi: vi.fn(() => 50),
          cfiFromLocation: vi.fn(),
          generate: vi.fn(),
        },
        () => 50,
      );
      vi.spyOn(epubLocation, "areLocationsReady").mockReturnValue(true);

      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation: vi.fn(),
        bookRef: { current: book },
        onLocationChange,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      vi.advanceTimersByTime(100);
      expect(onLocationChange).toHaveBeenCalledWith(
        "epubcfi(/6/4[chap02ref]!/4/2/2)",
        0.5,
      );
    });

    it("should generate locations when not ready", async () => {
      const onLocationChange = vi.fn();
      const generateMock = vi.fn(() => Promise.resolve());
      const book = createMockBook(
        {
          length: 100,
          total: undefined,
          locationFromCfi: vi.fn(() => 50),
          cfiFromLocation: vi.fn(),
          generate: generateMock,
        },
        () => 50,
      );
      vi.spyOn(epubLocation, "areLocationsReady").mockReturnValue(false);

      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation: vi.fn(),
        bookRef: { current: book },
        onLocationChange,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: null },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      vi.advanceTimersByTime(100);
      await vi.runAllTimersAsync();

      expect(generateMock).toHaveBeenCalledWith(200);
    });

    it("should clear existing timeout before setting new one", () => {
      const clearTimeoutSpy = vi.spyOn(global, "clearTimeout");
      const timeoutId = setTimeout(() => {}, 1000);
      const onLocationChange = vi.fn();
      const book = createMockBook(null);
      const options = {
        isNavigatingRef: { current: false },
        location: "epubcfi(/6/4[chap01ref]!/4/2/2)",
        setLocation: vi.fn(),
        bookRef: { current: book },
        onLocationChange,
        isInitialLoadRef: { current: false },
        progressCalculationTimeoutRef: { current: timeoutId },
      };

      const handler = createLocationChangedHandler(options);
      handler("epubcfi(/6/4[chap02ref]!/4/2/2)");

      expect(clearTimeoutSpy).toHaveBeenCalledWith(timeoutId);
      clearTimeoutSpy.mockRestore();
    });
  });

  describe("createJumpToProgressHandler", () => {
    it("should return a function", () => {
      const options = {
        bookRef: { current: null },
        renditionRef: { current: undefined },
        isNavigatingRef: { current: false },
        setLocation: vi.fn(),
        onLocationChange: undefined,
      };

      const handler = createJumpToProgressHandler(options);
      expect(typeof handler).toBe("function");
    });

    it("should return early when book is null", () => {
      const setLocation = vi.fn();
      const options = {
        bookRef: { current: null },
        renditionRef: { current: createMockRendition() },
        isNavigatingRef: { current: false },
        setLocation,
        onLocationChange: undefined,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      expect(setLocation).not.toHaveBeenCalled();
    });

    it("should return early when rendition is undefined", () => {
      const book = createMockBook(null);
      const setLocation = vi.fn();
      const options = {
        bookRef: { current: book },
        renditionRef: { current: undefined },
        isNavigatingRef: { current: false },
        setLocation,
        onLocationChange: undefined,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      expect(setLocation).not.toHaveBeenCalled();
    });

    it("should warn and return when locations are not available", () => {
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      const book = {
        locations: null,
      } as unknown as Book;
      const rendition = createMockRendition();
      const isNavigatingRef = { current: false };
      const options = {
        bookRef: { current: book },
        renditionRef: { current: rendition },
        isNavigatingRef,
        setLocation: vi.fn(),
        onLocationChange: undefined,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "Cannot jump to progress: locations not available",
      );
      expect(isNavigatingRef.current).toBe(false);
      consoleWarnSpy.mockRestore();
    });

    it("should jump immediately when locations are ready", () => {
      const book = createMockBook(
        {
          length: 100,
          total: 100,
          locationFromCfi: vi.fn(() => 50),
          cfiFromLocation: vi.fn(
            (loc: number) => `epubcfi(/6/4[chap${loc}]!/4/2/2)`,
          ),
          generate: vi.fn(),
        },
        () => 50,
        (loc: number) => `epubcfi(/6/4[chap${loc}]!/4/2/2)`,
      );
      vi.spyOn(epubLocation, "areLocationsReady").mockReturnValue(true);
      const rendition = createMockRendition();
      const setLocation = vi.fn();
      const onLocationChange = vi.fn();
      const isNavigatingRef = { current: false };
      const options = {
        bookRef: { current: book },
        renditionRef: { current: rendition },
        isNavigatingRef,
        setLocation,
        onLocationChange,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      expect(isNavigatingRef.current).toBe(true);
      expect(rendition.display).toHaveBeenCalled();
      expect(setLocation).toHaveBeenCalled();
      expect(onLocationChange).toHaveBeenCalled();

      vi.advanceTimersByTime(200);
      expect(isNavigatingRef.current).toBe(false);
    });

    it("should generate locations when not ready", async () => {
      const generateMock = vi.fn(() => Promise.resolve());
      const book = createMockBook(
        {
          length: 100,
          total: undefined,
          locationFromCfi: vi.fn(() => 50),
          cfiFromLocation: vi.fn(
            (loc: number) => `epubcfi(/6/4[chap${loc}]!/4/2/2)`,
          ),
          generate: generateMock,
        },
        () => 50,
        (loc: number) => `epubcfi(/6/4[chap${loc}]!/4/2/2)`,
      );
      vi.spyOn(epubLocation, "areLocationsReady").mockReturnValue(false);
      const rendition = createMockRendition();
      const setLocation = vi.fn();
      const onLocationChange = vi.fn();
      const isNavigatingRef = { current: false };
      const options = {
        bookRef: { current: book },
        renditionRef: { current: rendition },
        isNavigatingRef,
        setLocation,
        onLocationChange,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      await vi.runAllTimersAsync();

      expect(generateMock).toHaveBeenCalledWith(200);
      expect(rendition.display).toHaveBeenCalled();
    });

    it("should warn when CFI cannot be obtained", () => {
      const consoleWarnSpy = vi
        .spyOn(console, "warn")
        .mockImplementation(() => {});
      const book = createMockBook(
        {
          length: 100,
          total: 100,
          locationFromCfi: vi.fn(),
          cfiFromLocation: vi.fn(() => null),
          generate: vi.fn(),
        },
        () => 50,
        () => null,
      );
      vi.spyOn(epubLocation, "areLocationsReady").mockReturnValue(true);
      const rendition = createMockRendition();
      const isNavigatingRef = { current: false };
      const options = {
        bookRef: { current: book },
        renditionRef: { current: rendition },
        isNavigatingRef,
        setLocation: vi.fn(),
        onLocationChange: undefined,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        "Cannot jump to progress: could not get CFI",
      );
      expect(isNavigatingRef.current).toBe(false);
      consoleWarnSpy.mockRestore();
    });

    it("should handle errors gracefully", () => {
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});
      const book = createMockBook(
        {
          length: 100,
          total: 100,
          locationFromCfi: vi.fn(),
          cfiFromLocation: vi.fn(() => {
            throw new Error("CFI error");
          }),
          generate: vi.fn(),
        },
        () => 50,
        () => {
          throw new Error("CFI error");
        },
      );
      vi.spyOn(epubLocation, "areLocationsReady").mockReturnValue(true);
      // Mock getCfiFromProgress to throw an error
      vi.spyOn(epubLocation, "getCfiFromProgress").mockImplementation(() => {
        throw new Error("CFI error");
      });
      const rendition = createMockRendition();
      const isNavigatingRef = { current: false };
      const options = {
        bookRef: { current: book },
        renditionRef: { current: rendition },
        isNavigatingRef,
        setLocation: vi.fn(),
        onLocationChange: undefined,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      // The error is caught in the try-catch block inside performJump
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Error jumping to progress:",
        expect.any(Error),
      );
      // The finally block resets isNavigatingRef after 200ms
      vi.advanceTimersByTime(200);
      expect(isNavigatingRef.current).toBe(false);
      consoleErrorSpy.mockRestore();
    });

    it("should not skip backend update for user action", () => {
      const book = createMockBook(
        {
          length: 100,
          total: 100,
          locationFromCfi: vi.fn(() => 50),
          cfiFromLocation: vi.fn(
            (loc: number) => `epubcfi(/6/4[chap${loc}]!/4/2/2)`,
          ),
          generate: vi.fn(),
        },
        () => 50,
        (loc: number) => `epubcfi(/6/4[chap${loc}]!/4/2/2)`,
      );
      vi.spyOn(epubLocation, "areLocationsReady").mockReturnValue(true);
      const rendition = createMockRendition();
      const setLocation = vi.fn();
      const onLocationChange = vi.fn();
      const isNavigatingRef = { current: false };
      const options = {
        bookRef: { current: book },
        renditionRef: { current: rendition },
        isNavigatingRef,
        setLocation,
        onLocationChange,
      };

      const handler = createJumpToProgressHandler(options);
      handler(0.5);

      expect(onLocationChange).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Number),
        false,
      );
    });
  });
});
