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
 * Hook for checking user permissions in components.
 *
 * Provides a convenient way to check permissions with optional resource context
 * for condition evaluation.
 */

import { useMemo } from "react";
import { useUser } from "@/contexts/UserContext";

export interface UsePermissionOptions {
  /** Resource name (e.g., 'books', 'shelves'). */
  resource: string;
  /** Action name (e.g., 'read', 'write', 'delete'). */
  action: string;
  /** Optional resource data for condition evaluation. */
  resourceData?: Record<string, unknown>;
}

export interface UsePermissionResult {
  /** Whether the user has the required permission. */
  hasPermission: boolean;
  /** Whether permission data is still loading. */
  isLoading: boolean;
}

/**
 * Hook for checking user permissions.
 *
 * Uses UserContext for permission checking. Returns permission status
 * and loading state.
 *
 * Parameters
 * ----------
 * options : UsePermissionOptions
 *     Permission check options including resource, action, and optional context.
 *
 * Returns
 * -------
 * UsePermissionResult
 *     Permission status and loading state.
 *
 * Examples
 * --------
 * ```tsx
 * const { hasPermission } = usePermission({
 *   resource: "books",
 *   action: "write",
 *   resourceData: { authors: ["Stephen King"], tags: ["horror"] },
 * });
 *
 * if (!hasPermission) {
 *   return <div>You don't have permission to edit this book</div>;
 * }
 * ```
 */
export function usePermission(
  options: UsePermissionOptions,
): UsePermissionResult {
  const { canPerformAction, isLoading } = useUser();

  const hasPermission = useMemo(() => {
    if (isLoading) {
      return false;
    }
    return canPerformAction(
      options.resource,
      options.action,
      options.resourceData,
    );
  }, [
    isLoading,
    canPerformAction,
    options.resource,
    options.action,
    options.resourceData,
  ]);

  return {
    hasPermission,
    isLoading,
  };
}
