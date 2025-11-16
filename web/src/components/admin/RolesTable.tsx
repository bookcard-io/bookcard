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

import { useState } from "react";
import { PermissionsModal } from "@/components/admin/PermissionsModal";
import { Button } from "@/components/forms/Button";
import { Tooltip } from "@/components/layout/Tooltip";
import { cn } from "@/libs/utils";
import type { Role, RolePermission } from "@/services/roleService";

export interface RolesTableProps {
  roles: Role[];
  isLoading?: boolean;
  onEdit?: (role: Role) => void;
  onDelete?: (role: Role) => void;
  onPermissionClick?: (role: Role, rolePermission: RolePermission) => void;
  isRoleAssignedToUsers?: (roleId: number) => boolean;
}

const MAX_VISIBLE_PERMISSIONS = 10;

export function RolesTable({
  roles,
  isLoading,
  onEdit,
  onDelete,
  onPermissionClick,
  isRoleAssignedToUsers,
}: RolesTableProps) {
  const [expandedRoleId, setExpandedRoleId] = useState<number | null>(null);
  const [expandedInlineRoleId, setExpandedInlineRoleId] = useState<
    number | null
  >(null);
  if (isLoading) {
    return (
      <div className={cn("w-full overflow-x-auto")}>
        <div className={cn("p-6 text-center text-sm text-text-a30")}>
          Loading roles...
        </div>
      </div>
    );
  }

  if (roles.length === 0) {
    return (
      <div className={cn("w-full overflow-x-auto")}>
        <div className={cn("p-6 text-center text-sm text-text-a30")}>
          No roles found
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
            "grid grid-cols-[1fr_2fr_2fr_2fr_120px] gap-4 border-surface-a20 border-b bg-surface-a10 px-4 py-3 font-semibold text-sm text-text-a40",
          )}
        >
          <div className={cn("flex items-center")}>Name</div>
          <div className={cn("flex items-center")}>Description</div>
          <div className={cn("flex items-center")}>Permissions</div>
          <div className={cn("flex items-center gap-1.5")}>
            Conditions
            <Tooltip
              text={
                <>
                  Conditions add additional constraints to permissions,
                  restricting access based on specific criteria. Examples:{" "}
                  <code
                    className={cn("rounded bg-surface-a20 px-1 py-0.5 text-xs")}
                  >
                    {`{"owner_id": "user.id"}`}
                  </code>{" "}
                  limits access to resources owned by the current user.{" "}
                  <code
                    className={cn("rounded bg-surface-a20 px-1 py-0.5 text-xs")}
                  >
                    {`{"author": "Stephen King", "tags": ["Short Stories"]}`}
                  </code>{" "}
                  restricts access to books by Stephen King in the Short Stories
                  category.
                </>
              }
              className="max-w-[350px]"
            >
              <i
                className={cn(
                  "pi pi-question-circle cursor-help text-text-a30 text-xs",
                )}
              />
            </Tooltip>
          </div>
          <div className={cn("flex items-center")}>Actions</div>
        </div>

        {/* Rows */}
        <div className={cn("flex flex-col")}>
          {roles.map((role, index) => (
            <div
              key={role.id}
              className={cn(
                "grid grid-cols-[1fr_2fr_2fr_2fr_120px] gap-4 border-surface-a20 border-b px-4 py-3 transition-colors duration-200 last:border-b-0",
                index % 2 === 0 ? "bg-surface-a20" : "bg-surface-tonal-a20",
                "hover:bg-surface-a40/50",
              )}
            >
              <div
                className={cn(
                  "flex items-start gap-2 break-words pt-1 text-sm text-text-a0",
                )}
              >
                <span>{role.name}</span>
                <button
                  type="button"
                  onClick={() => setExpandedRoleId(role.id)}
                  className={cn(
                    "flex shrink-0 cursor-pointer items-center justify-center text-primary-a30 transition-colors",
                    "hover:text-primary-a0 active:text-primary-a20",
                  )}
                  aria-label={`View detailed permissions for ${role.name}`}
                  title="View detailed permissions"
                >
                  <i
                    className={cn("pi pi-info-circle text-sm")}
                    aria-hidden="true"
                  />
                </button>
              </div>
              <div
                className={cn(
                  "flex items-start break-words pt-1 text-sm text-text-a0",
                )}
              >
                {role.description || (
                  <span className={cn("text-text-a40 italic")}>—</span>
                )}
              </div>
              <div
                className={cn(
                  "flex items-start break-words pt-1 text-sm text-text-a0",
                )}
              >
                {role.permissions.length > 0 ? (
                  <div className={cn("flex flex-col gap-1.5")}>
                    <div className={cn("flex flex-wrap items-center gap-1.5")}>
                      {role.permissions
                        .slice(
                          0,
                          expandedInlineRoleId === role.id
                            ? role.permissions.length
                            : MAX_VISIBLE_PERMISSIONS,
                        )
                        .map((rp) => (
                          <button
                            key={rp.id}
                            type="button"
                            onClick={() => onPermissionClick?.(role, rp)}
                            className={cn(
                              "inline-block rounded bg-info-a20 px-2 py-1 font-medium text-info-a0 text-xs transition-colors",
                              onPermissionClick && !role.locked
                                ? "cursor-pointer hover:bg-info-a30"
                                : "cursor-default",
                            )}
                            title={`${rp.permission.resource}:${rp.permission.action}${onPermissionClick && !role.locked ? " (Click to edit)" : ""}`}
                            disabled={!onPermissionClick || role.locked}
                          >
                            {rp.permission.name}
                          </button>
                        ))}
                      {role.permissions.length > MAX_VISIBLE_PERMISSIONS && (
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedInlineRoleId(
                              expandedInlineRoleId === role.id ? null : role.id,
                            )
                          }
                          className={cn(
                            "flex items-center justify-center rounded bg-surface-a20 px-2 py-1 text-text-a30 transition-colors",
                            "hover:bg-surface-a40 hover:text-text-a0",
                          )}
                          aria-label={
                            expandedInlineRoleId === role.id
                              ? "Collapse permissions"
                              : `Show all ${role.permissions.length} permissions`
                          }
                          title={
                            expandedInlineRoleId === role.id
                              ? "Collapse permissions"
                              : `Show all ${role.permissions.length} permissions`
                          }
                        >
                          <i
                            className={cn(
                              expandedInlineRoleId === role.id
                                ? "pi pi-chevron-up text-sm"
                                : "pi pi-ellipsis-h text-sm",
                            )}
                            aria-hidden="true"
                          />
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <span className={cn("text-text-a40 italic")}>—</span>
                )}
              </div>
              <div
                className={cn(
                  "flex items-start break-words pt-1 text-sm text-text-a0",
                )}
              >
                {role.permissions.some((rp) => rp.condition) ? (
                  <div className={cn("flex w-full min-w-0 flex-col gap-1.5")}>
                    {role.permissions
                      .filter((rp) => rp.condition)
                      .map((rp) => {
                        const conditionJson = JSON.stringify(rp.condition);
                        return (
                          <span
                            key={rp.id}
                            className={cn(
                              "inline-block max-w-full truncate rounded bg-warning-a20 px-2 py-1 font-medium text-warning-a0 text-xs",
                            )}
                            title={conditionJson}
                          >
                            {conditionJson}
                          </span>
                        );
                      })}
                  </div>
                ) : (
                  <span className={cn("text-text-a40 italic")}>—</span>
                )}
              </div>
              <div className={cn("flex items-start gap-2 pt-1")}>
                {onEdit && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="xsmall"
                    onClick={() => onEdit(role)}
                    aria-label={`Edit role ${role.name}`}
                    title="Edit role"
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
                    onClick={() => onDelete(role)}
                    disabled={
                      role.locked || (isRoleAssignedToUsers?.(role.id) ?? false)
                    }
                    aria-label={`Delete role ${role.name}`}
                    title={
                      role.locked
                        ? "Cannot delete locked role"
                        : isRoleAssignedToUsers?.(role.id)
                          ? "Cannot delete role assigned to users"
                          : "Delete role"
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
          ))}
        </div>
      </div>

      {expandedRoleId !== null && (
        <PermissionsModal
          isOpen={expandedRoleId !== null}
          onClose={() => setExpandedRoleId(null)}
          permissions={
            roles.find((r) => r.id === expandedRoleId)?.permissions || []
          }
          roleName={roles.find((r) => r.id === expandedRoleId)?.name || ""}
        />
      )}
    </div>
  );
}
