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
import { useRoles } from "@/contexts/RolesContext";
import type { Role, RoleCreate, RoleUpdate } from "@/services/roleService";

export interface UseRoleManagementReturn {
  /** Create a new role. */
  handleCreate: (data: RoleCreate) => Promise<Role>;
  /** Update an existing role. */
  handleUpdate: (id: number, data: RoleUpdate) => Promise<Role>;
  /** Delete a role. */
  handleDelete: (id: number) => Promise<void>;
  /** Update a role optimistically (for permission edits). */
  updateRoleOptimistic: (role: Role) => void;
}

/**
 * Hook for managing roles.
 *
 * Wraps the roles context to provide a consistent interface for role operations.
 * Follows SRP by focusing solely on role management concerns.
 * Follows IOC by delegating to roles context.
 * Follows DRY by centralizing role operations.
 *
 * Returns
 * -------
 * UseRoleManagementReturn
 *     Object with role CRUD operations.
 */
export function useRoleManagement(): UseRoleManagementReturn {
  const {
    createRole: createRoleContext,
    updateRoleById,
    deleteRoleById,
    updateRole: updateRoleOptimistic,
  } = useRoles();

  const handleCreate = useCallback(
    async (data: RoleCreate): Promise<Role> => {
      return await createRoleContext(data);
    },
    [createRoleContext],
  );

  const handleUpdate = useCallback(
    async (id: number, data: RoleUpdate): Promise<Role> => {
      return await updateRoleById(id, data);
    },
    [updateRoleById],
  );

  const handleDelete = useCallback(
    async (id: number): Promise<void> => {
      await deleteRoleById(id);
    },
    [deleteRoleById],
  );

  return {
    handleCreate,
    handleUpdate,
    handleDelete,
    updateRoleOptimistic,
  };
}
