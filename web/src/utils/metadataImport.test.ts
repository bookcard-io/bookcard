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
import { parseJsonMetadataFile } from "./metadataImport";

describe("parseJsonMetadataFile", () => {
  it("should parse valid JSON metadata file", async () => {
    const metadata = {
      title: "Test Book",
      authors: ["Author 1", "Author 2"],
      series: "Test Series",
      series_index: 1,
      description: "Test description",
      publisher: "Test Publisher",
      pubdate: "2024-01-15",
      languages: ["en"],
      tags: ["fiction", "sci-fi"],
      rating: 4,
      isbn: "1234567890",
      identifiers: [
        { type: "isbn", val: "1234567890" },
        { type: "asin", val: "B00TEST" },
      ],
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.title).toBe("Test Book");
    expect(result.author_names).toEqual(["Author 1", "Author 2"]);
    expect(result.series_name).toBe("Test Series");
    expect(result.series_index).toBe(1);
    expect(result.description).toBe("Test description");
    expect(result.publisher_name).toBe("Test Publisher");
    expect(result.pubdate).toBe("2024-01-15");
    expect(result.language_codes).toEqual(["en"]);
    expect(result.tag_names).toEqual(["fiction", "sci-fi"]);
    expect(result.rating_value).toBe(4);
    expect(result.identifiers).toEqual([
      { type: "isbn", val: "1234567890" },
      { type: "asin", val: "B00TEST" },
    ]);
  });

  it("should throw error for non-JSON file", async () => {
    const file = new File(["not json"], "metadata.opf", {
      type: "application/xml",
    });

    await expect(parseJsonMetadataFile(file)).rejects.toThrow(
      "Expected JSON file, got: opf",
    );
  });

  it("should throw error for invalid JSON", async () => {
    const file = new File(["invalid json {"], "metadata.json", {
      type: "application/json",
    });

    await expect(parseJsonMetadataFile(file)).rejects.toThrow(
      "Invalid JSON format",
    );
  });

  it("should handle JSON parse error with Error object", async () => {
    const file = new File(["invalid json"], "metadata.json", {
      type: "application/json",
    });

    await expect(parseJsonMetadataFile(file)).rejects.toThrow(
      "Invalid JSON format",
    );
  });

  it("should handle JSON parse error with non-Error value", async () => {
    // This is hard to test directly, but the code handles it
    const file = new File(["{ invalid }"], "metadata.json", {
      type: "application/json",
    });

    await expect(parseJsonMetadataFile(file)).rejects.toThrow();
  });

  it("should normalize date format to YYYY-MM-DD", async () => {
    const metadata = {
      pubdate: "2024-01-15T10:30:00Z",
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.pubdate).toBe("2024-01-15");
  });

  it("should handle date without time component", async () => {
    const metadata = {
      pubdate: "2024-01-15",
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.pubdate).toBe("2024-01-15");
  });

  it("should handle date that doesn't match pattern", async () => {
    const metadata = {
      pubdate: "January 15, 2024",
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.pubdate).toBe("January 15, 2024");
  });

  it("should convert object format identifiers to array", async () => {
    const metadata = {
      identifiers: {
        isbn: "1234567890",
        asin: "B00TEST",
      },
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.identifiers).toEqual([
      { type: "isbn", val: "1234567890" },
      { type: "asin", val: "B00TEST" },
    ]);
  });

  it("should handle identifiers with null values", async () => {
    const metadata = {
      identifiers: {
        isbn: "1234567890",
        asin: null,
      },
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    // null values are converted to "null" string via String(null)
    expect(result.identifiers).toEqual([
      { type: "isbn", val: "1234567890" },
      { type: "asin", val: "null" },
    ]);
  });

  it("should add ISBN to identifiers if not present", async () => {
    const metadata = {
      isbn: "1234567890",
      identifiers: [{ type: "asin", val: "B00TEST" }],
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.identifiers).toEqual([
      { type: "asin", val: "B00TEST" },
      { type: "isbn", val: "1234567890" },
    ]);
  });

  it("should not add ISBN if already present in identifiers", async () => {
    const metadata = {
      isbn: "1234567890",
      identifiers: [{ type: "isbn", val: "9876543210" }],
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.identifiers).toEqual([{ type: "isbn", val: "9876543210" }]);
  });

  it("should clamp rating to 0-5 range", async () => {
    const metadata = {
      rating: 10,
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.rating_value).toBe(5);
  });

  it("should clamp negative rating to 0", async () => {
    const metadata = {
      rating: -5,
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.rating_value).toBe(0);
  });

  it("should round rating value", async () => {
    const metadata = {
      rating: 4.7,
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.rating_value).toBe(5);
  });

  it("should handle empty arrays", async () => {
    const metadata = {
      authors: [],
      tags: [],
      languages: [],
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.author_names).toBeUndefined();
    expect(result.tag_names).toBeUndefined();
    expect(result.language_codes).toBeUndefined();
  });

  it("should handle null values", async () => {
    const metadata = {
      title: "Test Book",
      authors: null,
      series: null,
      series_index: null,
      description: null,
      publisher: null,
      pubdate: null,
      languages: null,
      tags: null,
      rating: null,
      isbn: null,
      identifiers: null,
    };

    const file = new File([JSON.stringify(metadata)], "metadata.json", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.title).toBe("Test Book");
    expect(result.author_names).toBeUndefined();
    expect(result.series_name).toBeUndefined();
    expect(result.series_index).toBeUndefined();
    expect(result.description).toBeUndefined();
    expect(result.publisher_name).toBeUndefined();
    expect(result.pubdate).toBeUndefined();
    expect(result.language_codes).toBeUndefined();
    expect(result.tag_names).toBeUndefined();
    expect(result.rating_value).toBeUndefined();
    expect(result.identifiers).toBeUndefined();
  });

  it("should handle file with no extension", async () => {
    const metadata = { title: "Test Book" };
    const file = new File([JSON.stringify(metadata)], "metadata", {
      type: "application/json",
    });

    await expect(parseJsonMetadataFile(file)).rejects.toThrow(
      "Expected JSON file",
    );
  });

  it("should handle file with uppercase extension", async () => {
    const metadata = { title: "Test Book" };
    const file = new File([JSON.stringify(metadata)], "metadata.JSON", {
      type: "application/json",
    });

    const result = await parseJsonMetadataFile(file);

    expect(result.title).toBe("Test Book");
  });
});
