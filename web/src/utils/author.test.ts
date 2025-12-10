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

import { beforeEach, describe, expect, it, vi } from "vitest";
import type { AuthorWithMetadata } from "@/types/author";
import { buildRematchAuthorId } from "./author";
import { normalizeAuthorKey } from "./openLibrary";

vi.mock("./openLibrary", () => ({
  normalizeAuthorKey: vi.fn(),
}));

/**
 * Create a mock author for testing.
 *
 * Parameters
 * ----------
 * overrides : Partial<AuthorWithMetadata>
 *     Optional overrides for author properties.
 *
 * Returns
 * -------
 * AuthorWithMetadata
 *     Mock author object.
 */
function createMockAuthor(
  overrides: Partial<AuthorWithMetadata> = {},
): AuthorWithMetadata {
  return {
    name: "Test Author",
    key: undefined,
    calibre_id: undefined,
    ...overrides,
  } as AuthorWithMetadata;
}

describe("buildRematchAuthorId", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return calibre-{id} when calibre_id is present", () => {
    const author = createMockAuthor({ calibre_id: 123 });

    const result = buildRematchAuthorId(author);

    expect(result).toBe("calibre-123");
    expect(normalizeAuthorKey).not.toHaveBeenCalled();
  });

  it("should return existing calibre- key when key starts with calibre-", () => {
    const author = createMockAuthor({
      calibre_id: undefined,
      key: "calibre-456",
    });

    const result = buildRematchAuthorId(author);

    expect(result).toBe("calibre-456");
    expect(normalizeAuthorKey).not.toHaveBeenCalled();
  });

  it("should return normalized key when no calibre_id and key doesn't start with calibre-", () => {
    const author = createMockAuthor({
      calibre_id: undefined,
      key: "/authors/OL12345A",
    });
    const normalizedKey = "OL12345A";

    vi.mocked(normalizeAuthorKey).mockReturnValue(normalizedKey);

    const result = buildRematchAuthorId(author);

    expect(normalizeAuthorKey).toHaveBeenCalledWith("/authors/OL12345A");
    expect(result).toBe(normalizedKey);
  });

  it("should return null when normalized key is empty", () => {
    const author = createMockAuthor({
      calibre_id: undefined,
      key: "invalid-key",
    });

    vi.mocked(normalizeAuthorKey).mockReturnValue("");

    const result = buildRematchAuthorId(author);

    expect(result).toBeNull();
  });

  it("should return null when key is undefined and no calibre_id", () => {
    const author = createMockAuthor({
      calibre_id: undefined,
      key: undefined,
    });

    vi.mocked(normalizeAuthorKey).mockReturnValue("");

    const result = buildRematchAuthorId(author);

    expect(normalizeAuthorKey).toHaveBeenCalledWith(undefined);
    expect(result).toBeNull();
  });

  it.each([
    { calibre_id: 0, expected: "calibre-0" },
    { calibre_id: 999, expected: "calibre-999" },
    { calibre_id: -1, expected: "calibre--1" },
  ])("should handle calibre_id $calibre_id and return '$expected'", ({
    calibre_id,
    expected,
  }) => {
    const author = createMockAuthor({ calibre_id });

    const result = buildRematchAuthorId(author);

    expect(result).toBe(expected);
  });

  it.each([
    { key: "calibre-123", expected: "calibre-123" },
    { key: "calibre-0", expected: "calibre-0" },
    { key: "calibre-abc", expected: "calibre-abc" },
  ])("should return existing key '$key' when it starts with calibre-", ({
    key,
    expected,
  }) => {
    const author = createMockAuthor({
      calibre_id: undefined,
      key,
    });

    const result = buildRematchAuthorId(author);

    expect(result).toBe(expected);
  });
});
