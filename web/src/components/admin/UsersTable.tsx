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
}

export function UsersTable({ users, isLoading }: UsersTableProps) {
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
        <div className="grid grid-cols-[1.5fr_2fr_2fr_2fr_1fr] gap-4 border-surface-a20 border-b bg-surface-a10 px-4 py-3 font-semibold text-sm text-text-a10">
          <div className="flex items-center">Username</div>
          <div className="flex items-center">Email</div>
          <div className="flex items-center">Default Device</div>
          <div className="flex items-center">Roles</div>
          <div className="flex items-center">Admin</div>
        </div>

        {/* Rows */}
        <div className="flex flex-col">
          {users.map((user, index) => (
            <div
              key={user.id}
              className={cn(
                "grid grid-cols-[1.5fr_2fr_2fr_2fr_1fr] gap-4 border-surface-a20 border-b px-4 py-3 transition-colors duration-200 last:border-b-0",
                index % 2 === 0 ? "bg-surface-a20" : "bg-surface-a10",
                "hover:bg-surface-a40/50",
              )}
            >
              <div className="flex items-center break-words text-sm text-text-a0">
                {user.username}
              </div>
              <div className="flex items-center break-words text-sm text-text-a0">
                {user.email}
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
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
