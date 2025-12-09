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
import { ValidationError } from "../errors";
import {
  parseIdParam,
  parseImportFormData,
  parseShelfCreationFormData,
  parseShelfCreationJson,
} from "./parsers";

/**
 * Create a mock File for testing.
 *
 * Parameters
 * ----------
 * name : string
 *     File name.
 * content : string
 *     File content.
 *
 * Returns
 * -------
 * File
 *     Mock File instance.
 */
function createMockFile(
  name: string = "test.txt",
  content: string = "test",
): File {
  const blob = new Blob([content], { type: "text/plain" });
  return new File([blob], name, { type: "text/plain" });
}

/**
 * Create FormData with import fields.
 *
 * Parameters
 * ----------
 * file : File | null
 *     File to include.
 * importer : string
 *     Importer name.
 * autoMatch : boolean | string
 *     Auto match value (can be string for FormData).
 *
 * Returns
 * -------
 * FormData
 *     FormData instance with import fields.
 */
function createImportFormData(
  file: File | null = null,
  importer: string = "comicrack",
  autoMatch: boolean | string = true,
): FormData {
  const formData = new FormData();
  if (file) {
    formData.append("file", file);
  }
  formData.append("importer", importer);
  formData.append("auto_match", String(autoMatch));
  return formData;
}

/**
 * Create FormData with shelf creation fields.
 *
 * Parameters
 * ----------
 * shelf : object
 *     Shelf data to JSON stringify.
 * file : File | null
 *     Optional file to include.
 * importer : string
 *     Importer name.
 * autoMatch : boolean | string
 *     Auto match value.
 *
 * Returns
 * -------
 * FormData
 *     FormData instance with shelf creation fields.
 */
function createShelfFormData(
  shelf: object,
  file: File | null = null,
  importer: string = "comicrack",
  autoMatch: boolean | string = true,
): FormData {
  const formData = new FormData();
  formData.append("shelf", JSON.stringify(shelf));
  if (file) {
    formData.append("file", file);
  }
  formData.append("importer", importer);
  formData.append("auto_match", String(autoMatch));
  return formData;
}

describe("parseImportFormData", () => {
  it("should parse valid import form data", () => {
    const file = createMockFile();
    const formData = createImportFormData(file, "comicrack", true);

    const result = parseImportFormData(formData);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value.file).toBe(file);
      expect(result.value.options.importer).toBe("comicrack");
      expect(result.value.options.autoMatch).toBe(true);
    }
  });

  it("should return error when file is missing", () => {
    const formData = createImportFormData(null);

    const result = parseImportFormData(formData);

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("No file provided");
    }
  });

  it.each([
    { value: "true" as string | null, expected: true },
    { value: "1" as string | null, expected: true },
    { value: "on" as string | null, expected: true },
    { value: "false" as string | null, expected: false },
    { value: "0" as string | null, expected: false },
    { value: "" as string | null, expected: false },
    { value: null, expected: false },
  ])(
    "should parse auto_match value '$value' as $expected",
    ({ value, expected }) => {
      const file = createMockFile();
      const formData = createImportFormData(file, "comicrack", value ?? false);

      const result = parseImportFormData(formData);

      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value.options.autoMatch).toBe(expected);
      }
    },
  );

  it("should use default importer when not provided", () => {
    const file = createMockFile();
    const formData = new FormData();
    formData.append("file", file);

    const result = parseImportFormData(formData);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value.options.importer).toBe("comicrack");
    }
  });

  it("should handle File object as auto_match value (returns false)", () => {
    const file = createMockFile();
    const autoMatchFile = createMockFile("auto_match.txt");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("auto_match", autoMatchFile);

    const result = parseImportFormData(formData);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value.options.autoMatch).toBe(false);
    }
  });
});

describe("parseShelfCreationFormData", () => {
  const validShelf = {
    name: "Test Shelf",
    description: "Test Description",
    is_public: false,
  };

  it("should parse valid shelf creation form data", () => {
    const file = createMockFile();
    const formData = createShelfFormData(validShelf, file, "comicrack", true);

    const result = parseShelfCreationFormData(formData);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value.shelf).toEqual(validShelf);
      expect(result.value.file).toBe(file);
      expect(result.value.importOptions.importer).toBe("comicrack");
      expect(result.value.importOptions.autoMatch).toBe(true);
    }
  });

  it("should parse shelf creation form data without file", () => {
    const formData = createShelfFormData(validShelf, null);

    const result = parseShelfCreationFormData(formData);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value.shelf).toEqual(validShelf);
      expect(result.value.file).toBeNull();
    }
  });

  it("should return error when shelf data is missing", () => {
    const formData = new FormData();

    const result = parseShelfCreationFormData(formData);

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("Missing shelf data");
    }
  });

  it("should return error when shelf JSON is invalid", () => {
    const formData = new FormData();
    formData.append("shelf", "invalid json{");

    const result = parseShelfCreationFormData(formData);

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("Invalid shelf JSON");
    }
  });

  it.each([
    { value: "true" as string | null, expected: true },
    { value: "1" as string | null, expected: true },
    { value: "on" as string | null, expected: true },
    { value: "false" as string | null, expected: false },
    { value: "0" as string | null, expected: false },
    { value: "" as string | null, expected: false },
    { value: null, expected: false },
  ])(
    "should parse auto_match value '$value' as $expected",
    ({ value, expected }) => {
      const formData = createShelfFormData(
        validShelf,
        null,
        "comicrack",
        value ?? false,
      );

      const result = parseShelfCreationFormData(formData);

      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value.importOptions.autoMatch).toBe(expected);
      }
    },
  );

  it("should use default importer when not provided", () => {
    const formData = new FormData();
    formData.append("shelf", JSON.stringify(validShelf));

    const result = parseShelfCreationFormData(formData);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value.importOptions.importer).toBe("comicrack");
    }
  });

  it("should handle File object as auto_match value (returns false)", () => {
    const autoMatchFile = createMockFile("auto_match.txt");
    const formData = new FormData();
    formData.append("shelf", JSON.stringify(validShelf));
    formData.append("auto_match", autoMatchFile);

    const result = parseShelfCreationFormData(formData);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value.importOptions.autoMatch).toBe(false);
    }
  });
});

describe("parseShelfCreationJson", () => {
  const validShelf = {
    name: "Test Shelf",
    description: "Test Description",
    is_public: false,
  };

  it("should parse valid JSON request", async () => {
    const request = new Request("http://example.com", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(validShelf),
    });

    const result = await parseShelfCreationJson(request);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toEqual(validShelf);
    }
  });

  it("should return error when JSON is invalid", async () => {
    const request = new Request("http://example.com", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "invalid json{",
    });

    const result = await parseShelfCreationJson(request);

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("Invalid JSON in request body");
    }
  });

  it("should return error when body is empty", async () => {
    const request = new Request("http://example.com", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "",
    });

    const result = await parseShelfCreationJson(request);

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("Invalid JSON in request body");
    }
  });
});

describe("parseIdParam", () => {
  it("should parse valid ID parameter", async () => {
    const params = Promise.resolve({ id: "123" });

    const result = await parseIdParam(params);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toBe(123);
    }
  });

  it("should parse valid ID with custom param name", async () => {
    const params = Promise.resolve({ shelfId: "456" });

    const result = await parseIdParam(params, "shelfId");

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toBe(456);
    }
  });

  it("should return error when parameter is missing", async () => {
    const params = Promise.resolve({});

    const result = await parseIdParam(params);

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("Missing id parameter");
    }
  });

  it("should return error when parameter is missing with custom name", async () => {
    const params = Promise.resolve({});

    const result = await parseIdParam(params, "shelfId");

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("Missing shelfId parameter");
    }
  });

  it.each([
    { value: "abc", paramName: "id" },
    { value: "not-a-number", paramName: "id" },
    { value: "abc", paramName: "shelfId" },
  ])(
    "should return error when $paramName is invalid: '$value'",
    async ({ value, paramName }) => {
      const params = Promise.resolve({ [paramName]: value });

      const result = await parseIdParam(params, paramName);

      expect(result.isErr).toBe(true);
      if (result.isErr) {
        expect(result.error).toBeInstanceOf(ValidationError);
        expect(result.error.message).toBe(
          `Invalid ${paramName}: must be a number`,
        );
      }
    },
  );

  it("should return error when ID contains decimal point", async () => {
    const params = Promise.resolve({ id: "12.5" });

    const result = await parseIdParam(params);

    expect(result.isErr).toBe(true);
    if (result.isErr) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.message).toBe("Invalid id: must be a number");
    }
  });

  it("should parse zero as valid ID", async () => {
    const params = Promise.resolve({ id: "0" });

    const result = await parseIdParam(params);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toBe(0);
    }
  });

  it("should parse negative numbers", async () => {
    const params = Promise.resolve({ id: "-1" });

    const result = await parseIdParam(params);

    expect(result.isOk).toBe(true);
    if (result.isOk) {
      expect(result.value).toBe(-1);
    }
  });
});
