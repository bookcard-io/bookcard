// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
// See the GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

/**
 * Permission utility functions for frontend permission checking.
 *
 * Matches backend condition evaluation logic for consistent permission enforcement.
 */

import type { User } from "@/contexts/UserContext";
import type { Book } from "@/types/book";
import type { Shelf } from "@/types/shelf";

export interface Role {
  id: number;
  name: string;
  description: string | null;
  permissions: RolePermission[];
}

export interface RolePermission {
  id: number;
  permission: Permission;
  condition: Record<string, unknown> | null;
  assigned_at: string;
}

export interface Permission {
  id: number;
  name: string;
  description: string | null;
  resource: string;
  action: string;
}

/**
 * Check if user has a basic permission (without conditions).
 *
 * Parameters
 * ----------
 * user : User
 *     User to check permissions for.
 * resource : string
 *     Resource name (e.g., 'books', 'shelves').
 * action : string
 *     Action name (e.g., 'read', 'write', 'delete').
 *
 * Returns
 * -------
 * boolean
 *     True if user has the permission, False otherwise.
 */
export function hasPermission(
  user: User | null,
  resource: string,
  action: string,
): boolean {
  if (!user || !user.roles) {
    return false;
  }

  // Admin users have all permissions
  if (user.is_admin) {
    return true;
  }

  // Check all roles for matching permission
  for (const role of user.roles) {
    if (!role.permissions) {
      continue;
    }
    for (const rolePermission of role.permissions) {
      const perm = rolePermission.permission;
      if (perm.resource === resource && perm.action === action) {
        // If no condition, permission applies globally
        if (!rolePermission.condition) {
          return true;
        }
      }
    }
  }

  return false;
}

/**
 * Evaluate condition against resource metadata.
 *
 * Supports the same condition keys as the backend:
 * - author: Exact author name match
 * - author_id: Author ID match
 * - author_ids: List of author IDs (matches if any in list)
 * - tag: Single tag match
 * - tags: List of tags (matches if any tag in list)
 * - series_id: Series ID match
 * - owner_id: Owner ID match (supports "user.id" for current user)
 *
 * Multiple conditions are combined with AND logic (all must match).
 *
 * Parameters
 * ----------
 * condition : Record<string, unknown>
 *     Condition dictionary to evaluate.
 * resourceData : Record<string, unknown>
 *     Resource metadata to match against.
 * userId : number | null
 *     Optional user ID for evaluating "user.id" in owner_id conditions.
 *
 * Returns
 * -------
 * boolean
 *     True if condition matches, False otherwise.
 */
export function evaluateCondition(
  condition: Record<string, unknown>,
  resourceData: Record<string, unknown>,
  userId: number | null = null,
): boolean {
  // Evaluate each condition key
  for (const [key, expectedValue] of Object.entries(condition)) {
    if (key === "author") {
      // Match exact author name
      const authors = resourceData.authors as string[] | undefined;
      if (!authors || !Array.isArray(authors)) {
        return false;
      }
      if (!authors.includes(expectedValue as string)) {
        return false;
      }
    } else if (key === "author_id") {
      // Match author ID
      const authorIds = resourceData.author_ids as number[] | undefined;
      if (!authorIds || !Array.isArray(authorIds)) {
        return false;
      }
      if (!authorIds.includes(expectedValue as number)) {
        return false;
      }
    } else if (key === "author_ids") {
      // Match any author ID in list
      if (!Array.isArray(expectedValue)) {
        return false;
      }
      const authorIds = resourceData.author_ids as number[] | undefined;
      if (!authorIds || !Array.isArray(authorIds)) {
        return false;
      }
      // Check if any expected author ID is in resource author IDs
      if (!(expectedValue as number[]).some((aid) => authorIds.includes(aid))) {
        return false;
      }
    } else if (key === "tag") {
      // Match single tag
      const tags = resourceData.tags as string[] | undefined;
      if (!tags || !Array.isArray(tags)) {
        return false;
      }
      if (!tags.includes(expectedValue as string)) {
        return false;
      }
    } else if (key === "tags") {
      // Match any tag in list
      if (!Array.isArray(expectedValue)) {
        return false;
      }
      const tags = resourceData.tags as string[] | undefined;
      if (!tags || !Array.isArray(tags)) {
        return false;
      }
      // Check if any expected tag is in resource tags
      if (!(expectedValue as string[]).some((tag) => tags.includes(tag))) {
        return false;
      }
    } else if (key === "series_id") {
      // Match series ID
      const seriesId = resourceData.series_id as number | undefined;
      if (seriesId !== expectedValue) {
        return false;
      }
    } else if (key === "owner_id") {
      // Match owner ID (supports "user.id" for current user)
      const ownerId = resourceData.owner_id as number | undefined;
      if (expectedValue === "user.id") {
        if (userId === null) {
          return false;
        }
        if (ownerId !== userId) {
          return false;
        }
      } else {
        if (ownerId !== expectedValue) {
          return false;
        }
      }
    } else {
      // Unknown condition key - fail safe by denying
      return false;
    }
  }

  // All conditions matched
  return true;
}

/**
 * Check if user can access a resource with condition evaluation.
 *
 * Parameters
 * ----------
 * user : User | null
 *     User to check permissions for.
 * resource : string
 *     Resource name (e.g., 'books', 'shelves').
 * action : string
 *     Action name (e.g., 'read', 'write', 'delete').
 * resourceData : Record<string, unknown> | undefined
 *     Optional resource metadata for condition evaluation.
 *
 * Returns
 * -------
 * boolean
 *     True if user has permission (and conditions match if applicable), False otherwise.
 */
export function canAccessResource(
  user: User | null,
  resource: string,
  action: string,
  resourceData?: Record<string, unknown>,
): boolean {
  if (!user || !user.roles) {
    return false;
  }

  // Admin users have all permissions
  if (user.is_admin) {
    return true;
  }

  // Check all roles for matching permission
  for (const role of user.roles) {
    if (!role.permissions) {
      continue;
    }
    for (const rolePermission of role.permissions) {
      const perm = rolePermission.permission;
      if (perm.resource === resource && perm.action === action) {
        // If no condition, permission applies globally
        if (!rolePermission.condition) {
          return true;
        }

        // Evaluate condition against resource data
        if (resourceData) {
          if (
            evaluateCondition(rolePermission.condition, resourceData, user.id)
          ) {
            return true;
          }
        }
      }
    }
  }

  return false;
}

/**
 * Build permission context from book metadata.
 *
 * Parameters
 * ----------
 * book : Book
 *     Book to build context from.
 *
 * Returns
 * -------
 * Record<string, unknown>
 *     Permission context dictionary.
 */
export function buildBookPermissionContext(
  book: Book,
): Record<string, unknown> {
  const context: Record<string, unknown> = {
    authors: book.authors || [],
  };

  // Add series_id if available
  if (book.series_id !== null && book.series_id !== undefined) {
    context.series_id = book.series_id;
  }

  // Add tags if available
  if (book.tags && book.tags.length > 0) {
    context.tags = book.tags;
  }

  return context;
}

/**
 * Build permission context from shelf metadata.
 *
 * Parameters
 * ----------
 * shelf : Shelf
 *     Shelf to build context from.
 *
 * Returns
 * -------
 * Record<string, unknown>
 *     Permission context dictionary.
 */
export function buildShelfPermissionContext(
  shelf: Shelf,
): Record<string, unknown> {
  const context: Record<string, unknown> = {
    owner_id: shelf.user_id,
  };

  return context;
}
