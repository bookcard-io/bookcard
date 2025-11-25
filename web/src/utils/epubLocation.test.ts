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

import type { Book } from "epubjs";
import { describe, expect, it, vi } from "vitest";
import {
  areLocationsReady,
  calculateProgressFromCfi,
  getCfiFromProgress,
  getTotalLocations,
} from "./epubLocation";

/**
 * Create a mock locations object with length property.
 */
function createMockLocationsWithLength(length: number) {
  const mockLocationFromCfi = vi.fn();
  const mockCfiFromLocation = vi.fn();
  const mockGenerate = vi.fn();
  return {
    length,
    total: length,
    locationFromCfi: mockLocationFromCfi,
    cfiFromLocation: mockCfiFromLocation,
    generate: mockGenerate,
  } as unknown as NonNullable<Book["locations"]> & {
    locationFromCfi: ReturnType<typeof vi.fn>;
    cfiFromLocation: ReturnType<typeof vi.fn>;
    generate: ReturnType<typeof vi.fn>;
  };
}

/**
 * Create a mock locations object with length method.
 */
function createMockLocationsWithLengthMethod(length: number) {
  const mockLength = vi.fn(() => length);
  const mockLocationFromCfi = vi.fn();
  const mockCfiFromLocation = vi.fn();
  const mockGenerate = vi.fn();
  return {
    length: mockLength,
    total: length,
    locationFromCfi: mockLocationFromCfi,
    cfiFromLocation: mockCfiFromLocation,
    generate: mockGenerate,
  } as unknown as NonNullable<Book["locations"]> & {
    length: ReturnType<typeof vi.fn>;
    locationFromCfi: ReturnType<typeof vi.fn>;
    cfiFromLocation: ReturnType<typeof vi.fn>;
    generate: ReturnType<typeof vi.fn>;
  };
}

/**
 * Create a mock book with locations.
 */
function createMockBook(locations: unknown) {
  return {
    locations,
  } as Book;
}

describe("epubLocation", () => {
  describe("getTotalLocations", () => {
    it("should return 0 when locations is null", () => {
      expect(getTotalLocations(null)).toBe(0);
    });

    it("should return 0 when locations is undefined", () => {
      expect(getTotalLocations(undefined)).toBe(0);
    });

    it("should return length when locations has length property", () => {
      const locations = createMockLocationsWithLength(100);
      expect(getTotalLocations(locations)).toBe(100);
    });

    it("should return length when locations has length method", () => {
      const locations = createMockLocationsWithLengthMethod(50);
      expect(getTotalLocations(locations)).toBe(50);
    });

    it("should return 0 when length is undefined", () => {
      const locations = {
        locationFromCfi: vi.fn(),
        cfiFromLocation: vi.fn(),
        generate: vi.fn(),
      } as unknown as NonNullable<Book["locations"]>;
      expect(getTotalLocations(locations)).toBe(0);
    });

    it("should return 0 when length is 0", () => {
      const locations = createMockLocationsWithLength(0);
      expect(getTotalLocations(locations)).toBe(0);
    });
  });

  describe("areLocationsReady", () => {
    it("should return false when locations is null", () => {
      expect(areLocationsReady(null)).toBe(false);
    });

    it("should return false when locations is undefined", () => {
      expect(areLocationsReady(undefined)).toBe(false);
    });

    it("should return true when locations has total property", () => {
      const locations = createMockLocationsWithLength(100);
      expect(areLocationsReady(locations)).toBe(true);
    });

    it("should return false when locations has no total property", () => {
      const locations = {
        length: 100,
        locationFromCfi: vi.fn(),
        cfiFromLocation: vi.fn(),
        generate: vi.fn(),
      } as unknown as NonNullable<Book["locations"]>;
      expect(areLocationsReady(locations)).toBe(false);
    });
  });

  describe("calculateProgressFromCfi", () => {
    it("should return 0 when book is null", () => {
      expect(
        calculateProgressFromCfi(null, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(0);
    });

    it("should return 0 when book has no locations", () => {
      const book = createMockBook(null);
      expect(
        calculateProgressFromCfi(book, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(0);
    });

    it("should return 0 when book has undefined locations", () => {
      const book = createMockBook(undefined);
      expect(
        calculateProgressFromCfi(book, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(0);
    });

    it("should calculate progress correctly", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.locationFromCfi as ReturnType<typeof vi.fn>).mockReturnValue(
        50,
      );
      const book = createMockBook(locations);
      expect(
        calculateProgressFromCfi(book, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(0.5);
    });

    it("should clamp progress to 1.0 when location exceeds total", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.locationFromCfi as ReturnType<typeof vi.fn>).mockReturnValue(
        150,
      );
      const book = createMockBook(locations);
      expect(
        calculateProgressFromCfi(book, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(1);
    });

    it("should clamp progress to 0.0 when location is negative", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.locationFromCfi as ReturnType<typeof vi.fn>).mockReturnValue(
        -10,
      );
      const book = createMockBook(locations);
      expect(
        calculateProgressFromCfi(book, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(0);
    });

    it("should return 0 when totalLocations is 0", () => {
      const locations = createMockLocationsWithLength(0);
      (locations.locationFromCfi as ReturnType<typeof vi.fn>).mockReturnValue(
        50,
      );
      const book = createMockBook(locations);
      expect(
        calculateProgressFromCfi(book, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(0);
    });

    it("should return 0 when locationFromCfi returns non-number", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.locationFromCfi as ReturnType<typeof vi.fn>).mockReturnValue(
        "invalid",
      );
      const book = createMockBook(locations);
      expect(
        calculateProgressFromCfi(book, "epubcfi(/6/4[chap01ref]!/4/2/2)"),
      ).toBe(0);
    });

    it("should return 0 when locationFromCfi throws error", () => {
      const locations = createMockLocationsWithLength(100);
      (
        locations.locationFromCfi as ReturnType<typeof vi.fn>
      ).mockImplementation(() => {
        throw new Error("Invalid CFI");
      });
      const book = createMockBook(locations);
      expect(calculateProgressFromCfi(book, "invalid-cfi")).toBe(0);
    });
  });

  describe("getCfiFromProgress", () => {
    it("should return null when book is null", () => {
      expect(getCfiFromProgress(null, 0.5)).toBeNull();
    });

    it("should return null when book has no locations", () => {
      const book = createMockBook(null);
      expect(getCfiFromProgress(book, 0.5)).toBeNull();
    });

    it("should return null when totalLocations is 0", () => {
      const locations = createMockLocationsWithLength(0);
      const book = createMockBook(locations);
      expect(getCfiFromProgress(book, 0.5)).toBeNull();
    });

    it("should get CFI from progress correctly", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.cfiFromLocation as ReturnType<typeof vi.fn>).mockReturnValue(
        "epubcfi(/6/4[chap01ref]!/4/2/2)",
      );
      const book = createMockBook(locations);
      const result = getCfiFromProgress(book, 0.5);
      expect(result).toBe("epubcfi(/6/4[chap01ref]!/4/2/2)");
      expect(locations.cfiFromLocation).toHaveBeenCalledWith(50);
    });

    it("should clamp progress to 1.0 and use last location", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.cfiFromLocation as ReturnType<typeof vi.fn>).mockReturnValue(
        "epubcfi(/6/4[chap01ref]!/4/2/2)",
      );
      const book = createMockBook(locations);
      const result = getCfiFromProgress(book, 1.5);
      expect(result).toBe("epubcfi(/6/4[chap01ref]!/4/2/2)");
      expect(locations.cfiFromLocation).toHaveBeenCalledWith(99);
    });

    it("should clamp progress to 0.0 and use first location", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.cfiFromLocation as ReturnType<typeof vi.fn>).mockReturnValue(
        "epubcfi(/6/4[chap01ref]!/4/2/2)",
      );
      const book = createMockBook(locations);
      const result = getCfiFromProgress(book, -0.5);
      expect(result).toBe("epubcfi(/6/4[chap01ref]!/4/2/2)");
      expect(locations.cfiFromLocation).toHaveBeenCalledWith(0);
    });

    it("should handle progress exactly at 1.0", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.cfiFromLocation as ReturnType<typeof vi.fn>).mockReturnValue(
        "epubcfi(/6/4[chap01ref]!/4/2/2)",
      );
      const book = createMockBook(locations);
      const result = getCfiFromProgress(book, 1.0);
      expect(result).toBe("epubcfi(/6/4[chap01ref]!/4/2/2)");
      expect(locations.cfiFromLocation).toHaveBeenCalledWith(99);
    });

    it("should return null when cfiFromLocation returns null", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.cfiFromLocation as ReturnType<typeof vi.fn>).mockReturnValue(
        null,
      );
      const book = createMockBook(locations);
      expect(getCfiFromProgress(book, 0.5)).toBeNull();
    });

    it("should return null when cfiFromLocation returns empty string", () => {
      const locations = createMockLocationsWithLength(100);
      (locations.cfiFromLocation as ReturnType<typeof vi.fn>).mockReturnValue(
        "",
      );
      const book = createMockBook(locations);
      expect(getCfiFromProgress(book, 0.5)).toBeNull();
    });

    it("should return null when cfiFromLocation throws error", () => {
      const locations = createMockLocationsWithLength(100);
      (
        locations.cfiFromLocation as ReturnType<typeof vi.fn>
      ).mockImplementation(() => {
        throw new Error("Invalid location");
      });
      const book = createMockBook(locations);
      expect(getCfiFromProgress(book, 0.5)).toBeNull();
    });

    it("should clamp targetLocation to valid range", () => {
      const locations = createMockLocationsWithLength(10);
      (locations.cfiFromLocation as ReturnType<typeof vi.fn>).mockReturnValue(
        "epubcfi(/6/4[chap01ref]!/4/2/2)",
      );
      const book = createMockBook(locations);
      // Progress 0.5 * 10 = 5, which is valid
      const result = getCfiFromProgress(book, 0.5);
      expect(result).toBe("epubcfi(/6/4[chap01ref]!/4/2/2)");
      expect(locations.cfiFromLocation).toHaveBeenCalledWith(5);
    });
  });
});
