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

import { useCallback, useEffect, useState } from "react";
import type { User } from "@/components/admin/UsersTable";
import {
  createUser,
  deleteUser,
  type UserCreate,
  type UserUpdate,
  updateUser,
} from "@/services/userService";

export interface UseUserManagementReturn {
  /** List of users. */
  users: User[];
  /** Whether users are being loaded. */
  isLoading: boolean;
  /** Create a new user. */
  handleCreate: (data: UserCreate) => Promise<User>;
  /** Update an existing user. */
  handleUpdate: (id: number, data: UserUpdate) => Promise<User>;
  /** Delete a user. */
  handleDelete: (id: number) => Promise<void>;
  /** Refresh the users list. */
  refresh: () => Promise<void>;
}

/**
 * Hook for managing users.
 *
 * Handles fetching, creating, updating, and deleting users.
 * Follows SRP by focusing solely on user management concerns.
 * Follows DRY by centralizing user CRUD operations.
 * Follows IOC by accepting callbacks for operations.
 *
 * Returns
 * -------
 * UseUserManagementReturn
 *     Object with users list, loading state, and CRUD operations.
 */
export function useUserManagement(): UseUserManagementReturn {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUsers = useCallback(async () => {
    try {
      setIsLoading(true);

      const response = await fetch("/api/admin/users?limit=100&offset=0", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();
      setUsers(data);
    } catch (_err) {
      // Error handling can be enhanced here
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  const handleCreate = useCallback(async (data: UserCreate): Promise<User> => {
    const savedUser = await createUser(data);
    setUsers((prevUsers) => [...prevUsers, savedUser]);
    return savedUser;
  }, []);

  const handleUpdate = useCallback(
    async (id: number, data: UserUpdate): Promise<User> => {
      const savedUser = await updateUser(id, data);
      setUsers((prevUsers) =>
        prevUsers.map((u) => (u.id === savedUser.id ? savedUser : u)),
      );
      return savedUser;
    },
    [],
  );

  const handleDelete = useCallback(async (id: number): Promise<void> => {
    await deleteUser(id);
    setUsers((prevUsers) => prevUsers.filter((u) => u.id !== id));
  }, []);

  return {
    users,
    isLoading,
    handleCreate,
    handleUpdate,
    handleDelete,
    refresh: fetchUsers,
  };
}
