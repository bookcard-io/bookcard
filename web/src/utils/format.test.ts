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

import { describe, expect, it, vi } from "vitest";
import { formatDate, formatFileSize, formatYear } from "./format";

describe("format utils", () => {
  describe("formatFileSize", () => {
    it("should format 0 bytes", () => {
      expect(formatFileSize(0)).toBe("0 B");
    });

    it("should format bytes", () => {
      expect(formatFileSize(500)).toBe("500.00 B");
    });

    it("should format kilobytes", () => {
      expect(formatFileSize(1024)).toBe("1.00 KB");
      expect(formatFileSize(1536)).toBe("1.50 KB");
      expect(formatFileSize(2048)).toBe("2.00 KB");
    });

    it("should format megabytes", () => {
      expect(formatFileSize(1024 * 1024)).toBe("1.00 MB");
      expect(formatFileSize(1024 * 1024 * 1.5)).toBe("1.50 MB");
      expect(formatFileSize(1024 * 1024 * 2)).toBe("2.00 MB");
    });

    it("should format gigabytes", () => {
      expect(formatFileSize(1024 * 1024 * 1024)).toBe("1.00 GB");
      expect(formatFileSize(1024 * 1024 * 1024 * 2.5)).toBe("2.50 GB");
    });

    it("should handle large values", () => {
      expect(formatFileSize(1024 * 1024 * 1024 * 10)).toBe("10.00 GB");
    });
  });

  describe("formatDate", () => {
    it("should return '—' for null", () => {
      expect(formatDate(null)).toBe("—");
    });

    it("should format valid ISO date string", () => {
      const date = "2024-01-15T10:30:00Z";
      const result = formatDate(date);
      expect(result).toMatch(/January 15, 2024/);
    });

    it("should format date-only string", () => {
      const date = "2024-12-25";
      const result = formatDate(date);
      // Handle timezone differences - date might be Dec 24 or Dec 25 depending on timezone
      expect(result).toMatch(/December (24|25), 2024/);
    });

    it("should handle invalid date string gracefully", () => {
      const invalidDate = "not-a-date";
      const result = formatDate(invalidDate);
      expect(result).toBe(invalidDate);
    });

    it("should handle date that creates NaN", () => {
      // Create a date string that will result in NaN when parsed
      const invalidDate = "Invalid Date";
      const result = formatDate(invalidDate);
      expect(result).toBe(invalidDate);
    });

    it("should handle exception in date parsing", () => {
      // Mock toLocaleDateString to throw an error to test catch block
      const originalToLocaleDateString = Date.prototype.toLocaleDateString;
      Date.prototype.toLocaleDateString = vi.fn(() => {
        throw new Error("toLocaleDateString failed");
      });

      const result = formatDate("2024-01-15");
      expect(result).toBe("2024-01-15"); // Should return original string on error

      Date.prototype.toLocaleDateString = originalToLocaleDateString;
    });

    it("should format different dates correctly", () => {
      // Handle timezone differences
      expect(formatDate("2023-06-01")).toMatch(/(May 31|June 1), 2023/);
      expect(formatDate("2022-03-15")).toMatch(/March (14|15), 2022/);
    });
  });

  describe("formatYear", () => {
    it("should return '—' for null", () => {
      expect(formatYear(null)).toBe("—");
    });

    it("should extract year from ISO date string", () => {
      const date = "2024-01-15T10:30:00Z";
      expect(formatYear(date)).toBe("2024");
    });

    it("should extract year from date-only string", () => {
      const date = "2024-12-25";
      expect(formatYear(date)).toBe("2024");
    });

    it("should return '—' for invalid date string", () => {
      const invalidDate = "not-a-date";
      expect(formatYear(invalidDate)).toBe("—");
    });

    it("should handle exception in date parsing", () => {
      // Mock getFullYear to throw an error to test catch block
      const originalGetFullYear = Date.prototype.getFullYear;
      Date.prototype.getFullYear = vi.fn(() => {
        throw new Error("getFullYear failed");
      });

      const result = formatYear("2024-01-15");
      expect(result).toBe("—"); // Should return "—" on error

      Date.prototype.getFullYear = originalGetFullYear;
    });

    it("should extract year from different dates", () => {
      expect(formatYear("2023-06-01")).toBe("2023");
      expect(formatYear("2022-03-15")).toBe("2022");
      expect(formatYear("1999-12-31")).toBe("1999");
    });
  });
});
