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
import type { User } from "@/contexts/UserContext";
import type { Book } from "@/types/book";
import type { Shelf } from "@/types/shelf";
import {
  buildBookPermissionContext,
  buildShelfPermissionContext,
  canAccessResource,
  evaluateCondition,
  hasPermission,
  type Permission,
  type Role,
  type RolePermission,
} from "./permissions";

describe("permissions", () => {
  const createMockPermission = (
    resource: string,
    action: string,
  ): Permission => ({
    id: 1,
    name: `${resource}:${action}`,
    description: null,
    resource,
    action,
  });

  const createMockRolePermission = (
    resource: string,
    action: string,
    condition: Record<string, unknown> | null = null,
  ): RolePermission => ({
    id: 1,
    permission: createMockPermission(resource, action),
    condition,
    assigned_at: "2024-01-01T00:00:00Z",
  });

  const createMockRole = (permissions: RolePermission[]): Role => ({
    id: 1,
    name: "Test Role",
    description: null,
    permissions,
  });

  describe("hasPermission", () => {
    it("should return false when user is null", () => {
      expect(hasPermission(null, "books", "read")).toBe(false);
    });

    it("should return false when user has no roles", () => {
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [],
      };
      expect(hasPermission(user, "books", "read")).toBe(false);
    });

    it("should return true when user is admin", () => {
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: true,
        profile_picture: null,
        roles: [],
      };
      expect(hasPermission(user, "books", "read")).toBe(true);
    });

    it("should return true when user has matching permission without condition", () => {
      const rolePermission = createMockRolePermission("books", "read", null);
      const role = createMockRole([rolePermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      expect(hasPermission(user, "books", "read")).toBe(true);
    });

    it("should return false when user has matching permission with condition", () => {
      const rolePermission = createMockRolePermission("books", "read", {
        author: "Author 1",
      });
      const role = createMockRole([rolePermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      // hasPermission doesn't evaluate conditions, so it returns false
      expect(hasPermission(user, "books", "read")).toBe(false);
    });

    it("should return false when permission doesn't match", () => {
      const rolePermission = createMockRolePermission("books", "write", null);
      const role = createMockRole([rolePermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      expect(hasPermission(user, "books", "read")).toBe(false);
    });

    it("should handle role with null permissions", () => {
      const role = {
        id: 1,
        name: "Test Role",
        description: null,
        // Simulate missing permissions array at runtime
        permissions: undefined,
      } as unknown as Role;
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      expect(hasPermission(user, "books", "read")).toBe(false);
    });
  });

  describe("evaluateCondition", () => {
    it("should return true for empty condition", () => {
      expect(evaluateCondition({}, {})).toBe(true);
    });

    it("should match author condition", () => {
      const condition = { author: "Author 1" };
      const resourceData = { authors: ["Author 1", "Author 2"] };
      expect(evaluateCondition(condition, resourceData)).toBe(true);
    });

    it("should fail author condition when author not in list", () => {
      const condition = { author: "Author 3" };
      const resourceData = { authors: ["Author 1", "Author 2"] };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail author condition when authors is not array", () => {
      const condition = { author: "Author 1" };
      const resourceData = { authors: "not an array" };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail author condition when authors is undefined", () => {
      const condition = { author: "Author 1" };
      const resourceData = {};
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should match author_id condition", () => {
      const condition = { author_id: 1 };
      const resourceData = { author_ids: [1, 2] };
      expect(evaluateCondition(condition, resourceData)).toBe(true);
    });

    it("should fail author_id condition when id not in list", () => {
      const condition = { author_id: 3 };
      const resourceData = { author_ids: [1, 2] };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail author_id condition when author_ids is not array", () => {
      const condition = { author_id: 1 };
      const resourceData = { author_ids: "not an array" };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should match author_ids condition", () => {
      const condition = { author_ids: [1, 3] };
      const resourceData = { author_ids: [1, 2, 3] };
      expect(evaluateCondition(condition, resourceData)).toBe(true);
    });

    it("should fail author_ids condition when no match", () => {
      const condition = { author_ids: [4, 5] };
      const resourceData = { author_ids: [1, 2, 3] };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail author_ids condition when expectedValue is not array", () => {
      const condition = { author_ids: "not an array" };
      const resourceData = { author_ids: [1, 2] };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail author_ids condition when resource author_ids is missing", () => {
      const condition = { author_ids: [1, 2] };
      const resourceData = {};
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should match tag condition", () => {
      const condition = { tag: "fiction" };
      const resourceData = { tags: ["fiction", "sci-fi"] };
      expect(evaluateCondition(condition, resourceData)).toBe(true);
    });

    it("should fail tag condition when tag not in list", () => {
      const condition = { tag: "horror" };
      const resourceData = { tags: ["fiction", "sci-fi"] };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail tag condition when tags is not array", () => {
      const condition = { tag: "fiction" };
      const resourceData = { tags: "not an array" };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should match tags condition", () => {
      const condition = { tags: ["fiction", "horror"] };
      const resourceData = { tags: ["fiction", "sci-fi", "horror"] };
      expect(evaluateCondition(condition, resourceData)).toBe(true);
    });

    it("should fail tags condition when no match", () => {
      const condition = { tags: ["horror", "thriller"] };
      const resourceData = { tags: ["fiction", "sci-fi"] };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail tags condition when expectedValue is not array", () => {
      const condition = { tags: "not an array" };
      const resourceData = { tags: ["fiction"] };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should fail tags condition when resource tags is missing", () => {
      const condition = { tags: ["fiction", "sci-fi"] };
      const resourceData = {};
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should match series_id condition", () => {
      const condition = { series_id: 1 };
      const resourceData = { series_id: 1 };
      expect(evaluateCondition(condition, resourceData)).toBe(true);
    });

    it("should fail series_id condition when mismatch", () => {
      const condition = { series_id: 1 };
      const resourceData = { series_id: 2 };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should match owner_id condition with numeric value", () => {
      const condition = { owner_id: 1 };
      const resourceData = { owner_id: 1 };
      expect(evaluateCondition(condition, resourceData, null)).toBe(true);
    });

    it("should fail owner_id condition when mismatch", () => {
      const condition = { owner_id: 1 };
      const resourceData = { owner_id: 2 };
      expect(evaluateCondition(condition, resourceData, null)).toBe(false);
    });

    it("should match owner_id condition with user.id", () => {
      const condition = { owner_id: "user.id" };
      const resourceData = { owner_id: 1 };
      expect(evaluateCondition(condition, resourceData, 1)).toBe(true);
    });

    it("should fail owner_id condition with user.id when userId is null", () => {
      const condition = { owner_id: "user.id" };
      const resourceData = { owner_id: 1 };
      expect(evaluateCondition(condition, resourceData, null)).toBe(false);
    });

    it("should fail owner_id condition with user.id when mismatch", () => {
      const condition = { owner_id: "user.id" };
      const resourceData = { owner_id: 1 };
      expect(evaluateCondition(condition, resourceData, 2)).toBe(false);
    });

    it("should return false for unknown condition key", () => {
      const condition = { unknown_key: "value" };
      const resourceData = {};
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });

    it("should handle multiple conditions with AND logic", () => {
      const condition = {
        author: "Author 1",
        tag: "fiction",
      };
      const resourceData = {
        authors: ["Author 1"],
        tags: ["fiction"],
      };
      expect(evaluateCondition(condition, resourceData)).toBe(true);
    });

    it("should fail when one condition doesn't match", () => {
      const condition = {
        author: "Author 1",
        tag: "horror",
      };
      const resourceData = {
        authors: ["Author 1"],
        tags: ["fiction"],
      };
      expect(evaluateCondition(condition, resourceData)).toBe(false);
    });
  });

  describe("canAccessResource", () => {
    it("should return false when user is null", () => {
      expect(canAccessResource(null, "books", "read")).toBe(false);
    });

    it("should return false when user has no roles", () => {
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [],
      };
      expect(canAccessResource(user, "books", "read")).toBe(false);
    });

    it("should return true when user is admin", () => {
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: true,
        profile_picture: null,
        roles: [],
      };
      expect(canAccessResource(user, "books", "read")).toBe(true);
    });

    it("should return true when user has matching permission without condition", () => {
      const rolePermission = createMockRolePermission("books", "read", null);
      const role = createMockRole([rolePermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      expect(canAccessResource(user, "books", "read")).toBe(true);
    });

    it("should return true when condition matches", () => {
      const rolePermission = createMockRolePermission("books", "read", {
        author: "Author 1",
      });
      const role = createMockRole([rolePermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      const resourceData = { authors: ["Author 1"] };
      expect(canAccessResource(user, "books", "read", resourceData)).toBe(true);
    });

    it("should return false when condition doesn't match", () => {
      const rolePermission = createMockRolePermission("books", "read", {
        author: "Author 1",
      });
      const role = createMockRole([rolePermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      const resourceData = { authors: ["Author 2"] };
      expect(canAccessResource(user, "books", "read", resourceData)).toBe(
        false,
      );
    });

    it("should return false when condition exists but no resourceData", () => {
      const rolePermission = createMockRolePermission("books", "read", {
        author: "Author 1",
      });
      const role = createMockRole([rolePermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      expect(canAccessResource(user, "books", "read")).toBe(false);
    });

    it("should handle role with null permissions", () => {
      const role = {
        id: 1,
        name: "Test Role",
        description: null,
        // Simulate missing permissions array at runtime
        permissions: undefined,
      } as unknown as Role;
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };
      expect(canAccessResource(user, "books", "read")).toBe(false);
    });

    it("should return false when permission resource/action does not match", () => {
      const mismatchedPermission = createMockRolePermission(
        "books",
        "write",
        null,
      );
      const role = createMockRole([mismatchedPermission]);
      const user: User = {
        id: 1,
        email: "test@example.com",
        username: "test",
        is_admin: false,
        profile_picture: null,
        roles: [role],
      };

      expect(canAccessResource(user, "books", "read")).toBe(false);
    });
  });

  describe("buildBookPermissionContext", () => {
    it("should build context with authors", () => {
      const book: Book = {
        id: 1,
        title: "Test Book",
        authors: ["Author 1", "Author 2"],
        author_sort: "Author 1",
        title_sort: null,
        pubdate: "2024-01-15T00:00:00Z",
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid-1",
        thumbnail_url: null,
        has_cover: false,
      };
      const context = buildBookPermissionContext(book);
      expect(context.authors).toEqual(["Author 1", "Author 2"]);
    });

    it("should default authors to empty array when missing", () => {
      const book = {
        id: 1,
        title: "Test Book",
        // Simulate missing authors array at runtime
        authors: undefined,
        author_sort: "Author 1",
        pubdate: "2024-01-15T00:00:00Z",
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid-1",
        thumbnail_url: null,
        has_cover: false,
      } as unknown as Book;
      const context = buildBookPermissionContext(book);
      expect(context.authors).toEqual([]);
    });

    it("should include series_id when available", () => {
      const book: Book = {
        id: 1,
        title: "Test Book",
        authors: ["Author 1"],
        author_sort: "Author 1",
        title_sort: null,
        pubdate: "2024-01-15T00:00:00Z",
        timestamp: null,
        series: "Test Series",
        series_id: 1,
        series_index: 1,
        isbn: null,
        uuid: "uuid-1",
        thumbnail_url: null,
        has_cover: false,
      };
      const context = buildBookPermissionContext(book);
      expect(context.series_id).toBe(1);
    });

    it("should not include series_id when null", () => {
      const book: Book = {
        id: 1,
        title: "Test Book",
        authors: ["Author 1"],
        author_sort: "Author 1",
        title_sort: null,
        pubdate: "2024-01-15T00:00:00Z",
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid-1",
        thumbnail_url: null,
        has_cover: false,
      };
      const context = buildBookPermissionContext(book);
      expect(context.series_id).toBeUndefined();
    });

    it("should include tags when available", () => {
      const book: Book = {
        id: 1,
        title: "Test Book",
        authors: ["Author 1"],
        author_sort: "Author 1",
        title_sort: null,
        pubdate: "2024-01-15T00:00:00Z",
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid-1",
        thumbnail_url: null,
        has_cover: false,
        tags: ["fiction", "sci-fi"],
      };
      const context = buildBookPermissionContext(book);
      expect(context.tags).toEqual(["fiction", "sci-fi"]);
    });

    it("should not include tags when empty", () => {
      const book: Book = {
        id: 1,
        title: "Test Book",
        authors: ["Author 1"],
        author_sort: "Author 1",
        title_sort: null,
        pubdate: "2024-01-15T00:00:00Z",
        timestamp: null,
        series: null,
        series_id: null,
        series_index: null,
        isbn: null,
        uuid: "uuid-1",
        thumbnail_url: null,
        has_cover: false,
        tags: [],
      };
      const context = buildBookPermissionContext(book);
      expect(context.tags).toBeUndefined();
    });
  });

  describe("buildShelfPermissionContext", () => {
    it("should build context with owner_id", () => {
      const shelf: Shelf = {
        id: 1,
        uuid: "test-uuid",
        name: "Test Shelf",
        description: null,
        user_id: 1,
        library_id: 1,
        cover_picture: null,
        is_public: false,
        is_active: true,
        book_count: 0,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        last_modified: "2024-01-01T00:00:00Z",
      };
      const context = buildShelfPermissionContext(shelf);
      expect(context.owner_id).toBe(1);
    });
  });
});
