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
import { Button } from "@/components/forms/Button";
import { useUser } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";

export interface User {
  id: number;
  username: string;
  email: string;
  profile_picture: string | null;
  is_admin: boolean;
  default_ereader_email: string | null;
  roles: Array<{
    id: number;
    name: string;
    description: string | null;
  }>;
}

export interface UsersTableProps {
  users: User[];
  isLoading?: boolean;
  onEdit?: (user: User) => void;
  onDelete?: (user: User) => void;
}

export function UsersTable({
  users,
  isLoading,
  onEdit,
  onDelete,
}: UsersTableProps) {
  const { user: currentUser } = useUser();

  // Memoize profile picture URLs to prevent re-downloading on re-renders
  // Use stable URLs without cache busting for table display
  const profilePictureUrls = useMemo(() => {
    const urlMap = new Map<number, string>();
    users.forEach((user) => {
      if (user.profile_picture) {
        // Use stable URL without cache buster for table display
        // Browser cache will handle caching, and we don't need to force refresh
        urlMap.set(user.id, `/api/admin/users/${user.id}/profile-picture`);
      }
    });
    return urlMap;
  }, [users]);

  if (isLoading) {
    return (
      <div className="w-full overflow-x-auto">
        <div className="p-6 text-center text-sm text-text-a30">
          Loading users...
        </div>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className="w-full overflow-x-auto">
        <div className="p-6 text-center text-sm text-text-a30">
          No users found
        </div>
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex flex-col overflow-hidden rounded-md border border-surface-a20 bg-surface-tonal-a0">
        {/* Header */}
        <div className="grid grid-cols-[60px_2fr_2fr_2fr_1fr_120px] gap-4 border-surface-a20 border-b bg-surface-a10 px-4 py-3 font-semibold text-sm text-text-a40">
          <div className="flex items-center justify-center">
            <i className="pi pi-face-smile" aria-hidden="true" />
          </div>
          <div className="flex items-center">User</div>
          <div className="flex items-center">Default Device</div>
          <div className="flex items-center">Roles</div>
          <div className="flex items-center">Admin</div>
          <div className="flex items-center">Actions</div>
        </div>

        {/* Rows */}
        <div className="flex flex-col">
          {users.map((user, index) => (
            <div
              key={user.id}
              className={cn(
                "grid grid-cols-[60px_2fr_2fr_2fr_1fr_120px] gap-4 border-surface-a20 border-b px-4 py-3 transition-colors duration-200 last:border-b-0",
                index % 2 === 0 ? "bg-surface-a20" : "bg-surface-a10",
                "hover:bg-surface-a40/50",
              )}
            >
              <div className="flex items-center justify-center">
                {user.profile_picture ? (
                  <img
                    src={
                      profilePictureUrls.get(user.id) ??
                      `/api/admin/users/${user.id}/profile-picture`
                    }
                    alt={`${user.username} profile`}
                    className="h-10 w-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full">
                    {/* Muted, blurred circular background */}
                    <div className="absolute inset-0 rounded-full bg-surface-tonal-a20 opacity-50 blur-xl" />
                    {/* Icon - dead centered */}
                    <i
                      className="pi pi-user relative text-text-a30 text-xl"
                      aria-hidden="true"
                    />
                  </div>
                )}
              </div>
              <div className="flex flex-col justify-center break-words text-sm text-text-a0">
                <span>{user.username}</span>
                <span className="text-text-a30 text-xs">{user.email}</span>
              </div>
              <div className="flex items-center break-words text-sm text-text-a0">
                {user.default_ereader_email || (
                  <span className="text-text-a40 italic">—</span>
                )}
              </div>
              <div className="flex items-center break-words text-sm text-text-a0">
                {user.roles.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {user.roles.map((role) => (
                      <span
                        key={role.id}
                        className="inline-block rounded bg-info-a20 px-2 py-1 font-medium text-info-a0 text-xs"
                      >
                        {role.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-text-a40 italic">—</span>
                )}
              </div>
              <div className="flex items-center break-words text-sm text-text-a0">
                {user.is_admin ? (
                  <span className="inline-block rounded bg-info-a20 px-2 py-1 font-medium text-info-a0 text-xs">
                    Admin
                  </span>
                ) : (
                  <span className="text-text-a40 italic">—</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {onEdit && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="xsmall"
                    onClick={() => onEdit(user)}
                    aria-label={`Edit user ${user.username}`}
                    title="Edit user"
                  >
                    <i className="pi pi-pencil text-sm" aria-hidden="true" />
                  </Button>
                )}
                {onDelete && (
                  <Button
                    type="button"
                    variant="danger"
                    size="xsmall"
                    onClick={() => onDelete(user)}
                    disabled={currentUser?.id === user.id}
                    aria-label={`Delete user ${user.username}`}
                    title={
                      currentUser?.id === user.id
                        ? "You cannot delete yourself"
                        : "Delete user"
                    }
                  >
                    <i className="pi pi-trash text-sm" aria-hidden="true" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
