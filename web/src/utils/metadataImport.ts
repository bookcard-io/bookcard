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

/**
 * Metadata import utility functions.
 *
 * Provides functions for parsing JSON metadata files into BookUpdate format.
 * OPF and YAML files are processed by the backend API.
 * Follows SRP by separating parsing logic from form logic.
 */

import type { BookUpdate } from "@/types/book";

/**
 * Parsed metadata structure from imported files.
 */
interface ParsedMetadata {
  title?: string;
  authors?: string[];
  series?: string;
  series_index?: number;
  description?: string;
  publisher?: string;
  pubdate?: string;
  languages?: string[];
  identifiers?: Array<{ type: string; val: string }> | Record<string, string>;
  tags?: string[];
  rating?: number;
  isbn?: string;
}

/**
 * Parse JSON metadata file.
 *
 * Parameters
 * ----------
 * content : string
 *     JSON file content as string.
 *
 * Returns
 * -------
 * ParsedMetadata
 *     Parsed metadata object.
 *
 * Raises
 * ------
 * Error
 *     If JSON parsing fails.
 */
function parseJsonMetadata(content: string): ParsedMetadata {
  try {
    return JSON.parse(content) as ParsedMetadata;
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to parse JSON";
    throw new Error(`Invalid JSON format: ${message}`);
  }
}

/**
 * Convert parsed metadata to BookUpdate format.
 *
 * Parameters
 * ----------
 * parsed : ParsedMetadata
 *     Parsed metadata from file.
 *
 * Returns
 * -------
 * BookUpdate
 *     Book update object ready for form application.
 */
function convertParsedMetadataToBookUpdate(parsed: ParsedMetadata): BookUpdate {
  const update: BookUpdate = {};

  if (parsed.title) {
    update.title = parsed.title;
  }

  if (parsed.authors && parsed.authors.length > 0) {
    update.author_names = parsed.authors;
  }

  if (parsed.series) {
    update.series_name = parsed.series;
  }

  if (parsed.series_index !== undefined && parsed.series_index !== null) {
    update.series_index = parsed.series_index;
  }

  if (parsed.description) {
    update.description = parsed.description;
  }

  if (parsed.publisher) {
    update.publisher_name = parsed.publisher;
  }

  if (parsed.pubdate) {
    // Normalize date format to YYYY-MM-DD
    const dateMatch = parsed.pubdate.match(/^(\d{4}-\d{2}-\d{2})/);
    if (dateMatch) {
      update.pubdate = dateMatch[1];
    } else {
      update.pubdate = parsed.pubdate;
    }
  }

  // Handle identifiers - convert from various formats
  if (parsed.identifiers) {
    if (Array.isArray(parsed.identifiers)) {
      update.identifiers = parsed.identifiers;
    } else if (typeof parsed.identifiers === "object") {
      // Convert object format to array format
      update.identifiers = Object.entries(parsed.identifiers).map(
        ([type, val]) => ({ type, val: String(val) || "" }),
      );
    }
  }

  // Also handle ISBN if present separately
  if (parsed.isbn && !update.identifiers?.some((id) => id.type === "isbn")) {
    if (!update.identifiers) {
      update.identifiers = [];
    }
    update.identifiers.push({ type: "isbn", val: parsed.isbn });
  }

  if (parsed.languages && parsed.languages.length > 0) {
    update.language_codes = parsed.languages;
  }

  if (parsed.tags && parsed.tags.length > 0) {
    update.tag_names = parsed.tags;
  }

  if (parsed.rating !== undefined && parsed.rating !== null) {
    // Ensure rating is in 0-5 range
    update.rating_value = Math.max(0, Math.min(5, Math.round(parsed.rating)));
  }

  return update;
}

/**
 * Parse JSON metadata file (client-side only).
 *
 * OPF and YAML files should be sent to the backend for processing.
 *
 * Parameters
 * ----------
 * file : File
 *     JSON file to parse.
 *
 * Returns
 * -------
 * Promise<BookUpdate>
 *     Book update object ready for form application.
 *
 * Raises
 * ------
 * Error
 *     If file format is not JSON or parsing fails.
 */
export async function parseJsonMetadataFile(file: File): Promise<BookUpdate> {
  const fileName = file.name.toLowerCase();
  const extension = fileName.split(".").pop()?.toLowerCase() || "";

  if (extension !== "json") {
    throw new Error(
      `Expected JSON file, got: ${extension}. Use backend API for OPF/YAML files.`,
    );
  }

  const content = await file.text();
  const parsed = parseJsonMetadata(content);
  return convertParsedMetadataToBookUpdate(parsed);
}
