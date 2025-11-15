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

"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  createRole,
  deleteRole,
  fetchRoles,
  type Role,
  type RoleCreate,
  type RoleUpdate,
  updateRole,
} from "@/services/roleService";

interface RolesContextType {
  roles: Role[];
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  refreshTimestamp: number;
  // Optimistically update role without full refresh (avoids remounts)
  updateRole: (roleData: Role) => void;
  // Create a new role
  createRole: (data: RoleCreate) => Promise<Role>;
  // Update an existing role
  updateRoleById: (roleId: number, data: RoleUpdate) => Promise<Role>;
  // Delete a role
  deleteRoleById: (roleId: number) => Promise<void>;
}

export const RolesContext = createContext<RolesContextType | undefined>(
  undefined,
);

/**
 * Roles context provider.
 *
 * Manages roles and permissions data globally.
 * Fetches roles from the backend and provides them to child components.
 * Follows SRP by handling only roles data management.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Child components that can access the roles context.
 */
export function RolesProvider({ children }: { children: ReactNode }) {
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [refreshTimestamp, setRefreshTimestamp] = useState(0);
  const hasInitialRefetchRunRef = useRef(false);

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await fetchRoles();
      // Mark admin role as locked
      const rolesWithLocked = data.map((role) => ({
        ...role,
        locked: role.name.toLowerCase() === "admin",
      }));
      setRoles(rolesWithLocked);

      // Update refresh timestamp to force cache invalidation in all components
      setRefreshTimestamp(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
      setRoles([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Avoid duplicate fetch in React 18 StrictMode development double-invoke
    if (!hasInitialRefetchRunRef.current) {
      hasInitialRefetchRunRef.current = true;
      void refresh();
    }
  }, [refresh]);

  /**
   * Optimistically update role state without triggering full refresh.
   * Prevents unnecessary remounts when only role data changes.
   * Does not update refreshTimestamp or refetch from server.
   */
  const updateRoleOptimistic = useCallback((roleData: Role) => {
    setRoles((prev) => {
      const index = prev.findIndex((r) => r.id === roleData.id);
      if (index === -1) {
        // Role not found, add it
        return [...prev, roleData];
      }
      // Update existing role
      const updated = [...prev];
      updated[index] = roleData;
      return updated;
    });
  }, []);

  const createRoleHandler = useCallback(
    async (data: RoleCreate): Promise<Role> => {
      const newRole = await createRole(data);
      // Mark admin role as locked
      const roleWithLocked = {
        ...newRole,
        locked: newRole.name.toLowerCase() === "admin",
      };
      updateRoleOptimistic(roleWithLocked);
      return roleWithLocked;
    },
    [updateRoleOptimistic],
  );

  const updateRoleByIdHandler = useCallback(
    async (roleId: number, data: RoleUpdate): Promise<Role> => {
      const updatedRole = await updateRole(roleId, data);
      // Mark admin role as locked
      const roleWithLocked = {
        ...updatedRole,
        locked: updatedRole.name.toLowerCase() === "admin",
      };
      updateRoleOptimistic(roleWithLocked);
      return roleWithLocked;
    },
    [updateRoleOptimistic],
  );

  const deleteRoleByIdHandler = useCallback(async (roleId: number) => {
    await deleteRole(roleId);
    setRoles((prev) => prev.filter((r) => r.id !== roleId));
  }, []);

  const contextValue = useMemo(
    () => ({
      roles,
      isLoading,
      error,
      refresh,
      refreshTimestamp,
      updateRole: updateRoleOptimistic,
      createRole: createRoleHandler,
      updateRoleById: updateRoleByIdHandler,
      deleteRoleById: deleteRoleByIdHandler,
    }),
    [
      roles,
      isLoading,
      error,
      refresh,
      refreshTimestamp,
      updateRoleOptimistic,
      createRoleHandler,
      updateRoleByIdHandler,
      deleteRoleByIdHandler,
    ],
  );

  return (
    <RolesContext.Provider value={contextValue}>
      {children}
    </RolesContext.Provider>
  );
}

/**
 * Hook to access roles context.
 *
 * Returns
 * -------
 * RolesContextType
 *     Roles context containing roles data, loading state, error state, and refresh function.
 *
 * Raises
 * ------
 * Error
 *     If used outside of RolesProvider.
 */
export function useRoles() {
  const context = useContext(RolesContext);
  if (context === undefined) {
    throw new Error("useRoles must be used within a RolesProvider");
  }
  return context;
}
