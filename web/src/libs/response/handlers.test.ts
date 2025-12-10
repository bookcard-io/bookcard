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
import { ApiError } from "../errors";
import { buildImportFormData, parseJsonResponse } from "./handlers";

/**
 * Create a mock Response for testing.
 *
 * Parameters
 * ----------
 * ok : boolean
 *     Whether the response is OK.
 * status : number
 *     HTTP status code.
 * body : string
 *     Response body text.
 *
 * Returns
 * -------
 * Response
 *     Mock Response instance.
 */
function createMockResponse(
  ok: boolean,
  status: number,
  body: string,
): Response {
  return {
    ok,
    status,
    text: async () => body,
  } as unknown as Response;
}

describe("parseJsonResponse", () => {
  it("should parse valid JSON response when OK", async () => {
    const data = { id: 1, name: "Test" };
    const response = createMockResponse(true, 200, JSON.stringify(data));

    const result = await parseJsonResponse<typeof data>(
      response,
      "Failed to parse",
    );

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toEqual(data);
    }
  });

  it("should return error when response is not OK with detail", async () => {
    const errorData = { detail: "Not found" };
    const response = createMockResponse(false, 404, JSON.stringify(errorData));

    const result = await parseJsonResponse(response, "Default error");

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ApiError);
      expect(result.error.message).toBe("Not found");
      expect(result.error.statusCode).toBe(404);
    }
  });

  it("should return error with fallback message when response is not OK without detail", async () => {
    const errorData = {};
    const response = createMockResponse(false, 500, JSON.stringify(errorData));

    const result = await parseJsonResponse(response, "Default error");

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ApiError);
      expect(result.error.message).toBe("Default error");
      expect(result.error.statusCode).toBe(500);
    }
  });

  it("should return error with fallback message when error response is invalid JSON", async () => {
    const response = createMockResponse(false, 500, "invalid json{");

    const result = await parseJsonResponse(response, "Default error");

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ApiError);
      expect(result.error.message).toBe("Default error");
      expect(result.error.statusCode).toBe(500);
    }
  });

  it("should return error when OK response has invalid JSON", async () => {
    const response = createMockResponse(true, 200, "invalid json{");

    const result = await parseJsonResponse(response, "Default error");

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ApiError);
      expect(result.error.message).toBe("Invalid response from server");
      expect(result.error.statusCode).toBe(500);
    }
  });

  it("should return error when OK response is empty", async () => {
    const response = createMockResponse(true, 200, "");

    const result = await parseJsonResponse(response, "Default error");

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ApiError);
      expect(result.error.message).toBe("Invalid response from server");
      expect(result.error.statusCode).toBe(500);
    }
  });

  it.each([
    { status: 400, detail: "Bad request" },
    { status: 401, detail: "Unauthorized" },
    { status: 403, detail: "Forbidden" },
    { status: 404, detail: "Not found" },
    { status: 500, detail: "Internal server error" },
  ])("should handle error response with status $status and detail '$detail'", async ({
    status,
    detail,
  }) => {
    const errorData = { detail };
    const response = createMockResponse(
      false,
      status,
      JSON.stringify(errorData),
    );

    const result = await parseJsonResponse(response, "Default error");

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error.statusCode).toBe(status);
      expect(result.error.message).toBe(detail);
    }
  });

  it("should parse complex nested JSON objects", async () => {
    const data = {
      id: 1,
      nested: {
        array: [1, 2, 3],
        object: { key: "value" },
      },
    };
    const response = createMockResponse(true, 200, JSON.stringify(data));

    const result = await parseJsonResponse<typeof data>(
      response,
      "Failed to parse",
    );

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toEqual(data);
    }
  });

  it("should parse arrays", async () => {
    const data = [1, 2, 3];
    const response = createMockResponse(true, 200, JSON.stringify(data));

    const result = await parseJsonResponse<typeof data>(
      response,
      "Failed to parse",
    );

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toEqual(data);
    }
  });
});

describe("buildImportFormData", () => {
  /**
   * Create a mock File for testing.
   *
   * Parameters
   * ----------
   * name : string
   *     File name.
   *
   * Returns
   * -------
   * File
   *     Mock File instance.
   */
  function createMockFile(name: string = "test.txt"): File {
    const blob = new Blob(["test content"], { type: "text/plain" });
    return new File([blob], name, { type: "text/plain" });
  }

  it("should build FormData with file and options", () => {
    const file = createMockFile("test.cbl");
    const options = {
      importer: "comicrack",
      autoMatch: true,
    };

    const formData = buildImportFormData(file, options);

    expect(formData.get("file")).toBe(file);
    expect(formData.get("importer")).toBe("comicrack");
    expect(formData.get("auto_match")).toBe("true");
  });

  it("should build FormData with autoMatch false", () => {
    const file = createMockFile("test.cbl");
    const options = {
      importer: "comicrack",
      autoMatch: false,
    };

    const formData = buildImportFormData(file, options);

    expect(formData.get("file")).toBe(file);
    expect(formData.get("importer")).toBe("comicrack");
    expect(formData.get("auto_match")).toBe("false");
  });

  it.each([
    { importer: "comicrack", autoMatch: true },
    { importer: "comicrack", autoMatch: false },
    { importer: "calibre", autoMatch: true },
    { importer: "calibre", autoMatch: false },
  ])("should build FormData with importer '$importer' and autoMatch $autoMatch", ({
    importer,
    autoMatch,
  }) => {
    const file = createMockFile();
    const options = { importer, autoMatch };

    const formData = buildImportFormData(file, options);

    expect(formData.get("file")).toBe(file);
    expect(formData.get("importer")).toBe(importer);
    expect(formData.get("auto_match")).toBe(String(autoMatch));
  });
});
