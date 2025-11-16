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

import { useMemo } from "react";
import { StatusPill } from "@/components/common/StatusPill";
import { Button } from "@/components/forms/Button";
import { useRoles } from "@/contexts/RolesContext";
import { cn } from "@/libs/utils";
import type { Permission } from "@/services/roleService";

export interface PermissionsTableProps {
  permissions: Permission[];
  isLoading?: boolean;
  onEdit?: (permission: Permission) => void;
  onDelete?: (permission: Permission) => void;
}

/**
 * Permissions table component.
 *
 * Displays permissions in a table format with edit and delete actions.
 * Shows which roles use each permission and whether it can be deleted.
 */
export function PermissionsTable({
  permissions,
  isLoading,
  onEdit,
  onDelete,
}: PermissionsTableProps) {
  const { roles } = useRoles();

  // Create a map of permission IDs to roles that use them
  const permissionToRoles = useMemo(() => {
    const map = new Map<number, string[]>();
    roles.forEach((role) => {
      role.permissions.forEach((rp) => {
        const permId = rp.permission.id;
        if (!map.has(permId)) {
          map.set(permId, []);
        }
        map.get(permId)?.push(role.name);
      });
    });
    return map;
  }, [roles]);

  // Check if a permission is orphaned (not associated with any roles)
  const isOrphaned = (permissionId: number): boolean => {
    return !permissionToRoles.has(permissionId);
  };

  if (isLoading) {
    return (
      <div className={cn("w-full overflow-x-auto")}>
        <div className={cn("p-6 text-center text-sm text-text-a30")}>
          Loading permissions...
        </div>
      </div>
    );
  }

  if (permissions.length === 0) {
    return (
      <div className={cn("w-full overflow-x-auto")}>
        <div className={cn("p-6 text-center text-sm text-text-a30")}>
          No permissions found
        </div>
      </div>
    );
  }

  return (
    <div className={cn("w-full overflow-x-auto")}>
      <div
        className={cn(
          "flex flex-col overflow-hidden rounded-md border border-surface-a20 bg-surface-tonal-a0",
        )}
      >
        {/* Header */}
        <div
          className={cn(
            "grid grid-cols-[1fr_2fr_1fr_2fr_120px] gap-4 border-surface-a20 border-b bg-surface-a10 px-4 py-3 font-semibold text-sm text-text-a40",
          )}
        >
          <div className={cn("flex items-center")}>Name</div>
          <div className={cn("flex items-center")}>Description</div>
          <div className={cn("flex items-center")}>Resource:Action</div>
          <div className={cn("flex items-center")}>Used by</div>
          <div className={cn("flex items-center")}>Actions</div>
        </div>

        {/* Rows */}
        <div className={cn("flex flex-col")}>
          {permissions.map((permission, index) => {
            const usingRoles = permissionToRoles.get(permission.id) || [];
            const orphaned = isOrphaned(permission.id);

            return (
              <div
                key={permission.id}
                className={cn(
                  "grid grid-cols-[1fr_2fr_1fr_2fr_120px] gap-4 border-surface-a20 border-b px-4 py-3 transition-colors duration-200 last:border-b-0",
                  index % 2 === 0 ? "bg-surface-a20" : "bg-surface-tonal-a20",
                  "hover:bg-surface-a40/50",
                )}
              >
                <div
                  className={cn(
                    "flex items-start break-words pt-1 text-sm text-text-a0",
                  )}
                >
                  {permission.name}
                </div>
                <div
                  className={cn(
                    "flex items-start break-words pt-1 text-sm text-text-a0",
                  )}
                >
                  {permission.description || (
                    <span className={cn("text-text-a40 italic")}>—</span>
                  )}
                </div>
                <div
                  className={cn(
                    "flex items-start break-words pt-1 text-sm text-text-a0",
                  )}
                >
                  <span
                    className={cn(
                      "inline-block rounded bg-info-a20 px-2 py-1 font-medium text-info-a0 text-xs",
                    )}
                  >
                    {permission.resource}:{permission.action}
                  </span>
                </div>
                <div
                  className={cn(
                    "flex items-start break-words pt-1 text-sm text-text-a0",
                  )}
                >
                  {usingRoles.length > 0 ? (
                    <div className={cn("flex flex-wrap items-center gap-1.5")}>
                      {usingRoles.map((roleName) => (
                        <StatusPill
                          key={roleName}
                          label={roleName}
                          icon="pi pi-users"
                          variant="warning"
                          size="small"
                        />
                      ))}
                    </div>
                  ) : (
                    <span className={cn("text-text-a40 italic")}>
                      {orphaned ? "Orphaned" : "—"}
                    </span>
                  )}
                </div>
                <div className={cn("flex items-start gap-2 pt-1")}>
                  {onEdit && (
                    <Button
                      type="button"
                      variant="secondary"
                      size="xsmall"
                      onClick={() => onEdit(permission)}
                      aria-label={`Edit permission ${permission.name}`}
                      title="Edit permission"
                    >
                      <i
                        className={cn("pi pi-pencil text-sm")}
                        aria-hidden="true"
                      />
                    </Button>
                  )}
                  {onDelete && (
                    <Button
                      type="button"
                      variant="danger"
                      size="xsmall"
                      onClick={() => onDelete(permission)}
                      disabled={!orphaned}
                      aria-label={`Delete permission ${permission.name}`}
                      title={
                        orphaned
                          ? "Delete permission"
                          : "Cannot delete permission associated with roles"
                      }
                    >
                      <i
                        className={cn("pi pi-trash text-sm")}
                        aria-hidden="true"
                      />
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
