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

import { useCallback } from "react";
import type { Permission, Role } from "@/services/roleService";

export interface UsePermissionRulesOptions {
  /** All roles in the system. */
  roles: Role[];
  /** Permission to check rules for. */
  permission?: Permission | null;
  /** Whether we're in role context mode. */
  isRoleContext: boolean;
}

/**
 * Hook for permission business rules.
 *
 * Encapsulates business logic related to permissions, such as orphan checking.
 * Follows SRP by separating business rules from UI and API concerns.
 * Follows SOC by isolating business logic from presentation.
 *
 * Parameters
 * ----------
 * options : UsePermissionRulesOptions
 *     Configuration options for the rules.
 *
 * Returns
 * -------
 * object
 *     Object containing rule checking functions.
 */
export function usePermissionRules({
  roles,
  permission,
  isRoleContext,
}: UsePermissionRulesOptions) {
  /**
   * Check if permission is orphaned (only associated with one role).
   *
   * Returns
   * -------
   * boolean
   *     True if permission is orphaned, false otherwise.
   */
  const isOrphaned = useCallback((): boolean => {
    if (!isRoleContext || !permission) {
      return false;
    }
    // Count how many roles have this permission
    const roleCount = roles.filter((r) =>
      r.permissions.some((rp) => rp.permission.id === permission.id),
    ).length;
    // Orphaned if only associated with this one role
    return roleCount === 1;
  }, [isRoleContext, permission, roles]);

  return {
    isOrphaned,
  };
}
