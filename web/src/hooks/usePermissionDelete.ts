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

import { useCallback, useState } from "react";
import type { Permission } from "@/services/roleService";

export interface PermissionOperations {
  /** Delete a permission. */
  deletePermission: (id: number) => Promise<void>;
  /** Refresh roles data. */
  refreshRoles: () => Promise<void>;
}

export interface UsePermissionDeleteOptions {
  /** Permission to delete. */
  permission: Permission | null | undefined;
  /** Whether permission is orphaned. */
  isOrphaned: boolean;
  /** Permission operations (injected for IOC). */
  operations: PermissionOperations;
  /** Callback when deletion succeeds. */
  onSuccess: () => void;
  /** Callback when deletion fails. */
  onError: (error: string) => void;
}

export interface UsePermissionDeleteReturn {
  /** Whether deletion is in progress. */
  isDeleting: boolean;
  /** Error message from deletion attempt. */
  deleteError: string | null;
  /** Handler to trigger deletion. */
  handleDelete: () => Promise<void>;
}

/**
 * Hook for permission deletion logic.
 *
 * Manages deletion state and orchestrates the deletion process.
 * Follows SRP by separating deletion logic from UI components.
 * Follows IOC by accepting operations as dependencies.
 *
 * Parameters
 * ----------
 * options : UsePermissionDeleteOptions
 *     Configuration options for deletion.
 *
 * Returns
 * -------
 * UsePermissionDeleteReturn
 *     Object with deletion state and handler.
 */
export function usePermissionDelete({
  permission,
  isOrphaned,
  operations,
  onSuccess,
  onError,
}: UsePermissionDeleteOptions): UsePermissionDeleteReturn {
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = useCallback(async () => {
    if (!permission) {
      return;
    }

    if (!isOrphaned) {
      const errorMessage =
        "Cannot delete permission. This permission is associated with multiple roles. Please remove it from all roles first.";
      setDeleteError(errorMessage);
      onError(errorMessage);
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await operations.deletePermission(permission.id);
      // Refresh roles to ensure consistency
      await operations.refreshRoles();
      onSuccess();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete permission";
      setDeleteError(errorMessage);
      onError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  }, [permission, isOrphaned, operations, onSuccess, onError]);

  return {
    isDeleting,
    deleteError,
    handleDelete,
  };
}
