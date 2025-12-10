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

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  type SendBookOptions,
  sendBookToDevice,
  updateBookRating,
} from "./bookService";

/**
 * Creates a mock fetch response.
 *
 * Parameters
 * ----------
 * ok : boolean
 *     Response ok status.
 * jsonData : unknown
 *     JSON data to return.
 * jsonError : Error | null
 *     Optional error to throw from json().
 *
 * Returns
 * -------
 * Response
 *     Mock response object.
 */
function createMockResponse(
  ok: boolean,
  jsonData: unknown = {},
  jsonError: Error | null = null,
) {
  return {
    ok,
    json: jsonError
      ? vi.fn().mockRejectedValue(jsonError)
      : vi.fn().mockResolvedValue(jsonData),
  };
}

describe("bookService", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("sendBookToDevice", () => {
    const bookId = 1;
    const baseUrl = `/api/books/${bookId}/send`;
    const baseHeaders = {
      "Content-Type": "application/json",
    };
    const baseOptions = {
      method: "POST",
      headers: baseHeaders,
      credentials: "include" as const,
    };

    it("should send book successfully without options", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await sendBookToDevice(bookId);

      expect(globalThis.fetch).toHaveBeenCalledWith(baseUrl, {
        ...baseOptions,
        body: JSON.stringify({
          to_email: null,
          file_format: null,
        }),
      });
    });

    it.each<[string, SendBookOptions, Record<string, unknown>]>([
      [
        "with email only",
        { toEmail: "test@example.com" },
        { to_email: "test@example.com", file_format: null },
      ],
      [
        "with file format only",
        { fileFormat: "EPUB" },
        { to_email: null, file_format: "EPUB" },
      ],
      [
        "with both email and file format",
        { toEmail: "test@example.com", fileFormat: "MOBI" },
        { to_email: "test@example.com", file_format: "MOBI" },
      ],
    ])("should send book successfully %s", async (_desc, options, expectedBody) => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await sendBookToDevice(bookId, options);

      expect(globalThis.fetch).toHaveBeenCalledWith(baseUrl, {
        ...baseOptions,
        body: JSON.stringify(expectedBody),
      });
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Book not found" },
        "Book not found",
      ],
      ["without detail in error response", {}, "Failed to send book"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to send book",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(sendBookToDevice(bookId)).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(sendBookToDevice(bookId)).rejects.toThrow(
        "Failed to send book",
      );
    });
  });

  describe("updateBookRating", () => {
    const bookId = 1;

    it("should update rating successfully", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await updateBookRating(bookId, 5);

      expect(globalThis.fetch).toHaveBeenCalledWith(`/api/books/${bookId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          rating_value: 5,
        }),
      });
    });

    it("should update rating to null", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await updateBookRating(bookId, null);

      expect(globalThis.fetch).toHaveBeenCalledWith(`/api/books/${bookId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          rating_value: null,
        }),
      });
    });

    it("should throw error with detail from response", async () => {
      const mockResponse = createMockResponse(false, {
        detail: "Book not found",
      });
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateBookRating(bookId, 5)).rejects.toThrow(
        "Book not found",
      );
    });

    it("should throw error with default message when no detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateBookRating(bookId, 5)).rejects.toThrow(
        "Failed to update rating",
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateBookRating(bookId, 5)).rejects.toThrow(
        "Failed to update rating",
      );
    });
  });
});
