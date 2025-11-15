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

/**
 * Service for interacting with admin user API endpoints.
 *
 * Provides methods for creating, updating, and deleting users.
 */

import type { User } from "@/components/admin/UsersTable";

export interface UserCreate {
  username: string;
  full_name?: string | null;
  email: string;
  password: string;
  is_admin?: boolean;
  is_active?: boolean;
  role_ids?: number[];
  default_device_email?: string | null;
  default_device_name?: string | null;
  default_device_type?: string;
  default_device_format?: string | null;
}

export interface UserUpdate {
  username?: string;
  email?: string;
  password?: string;
  is_admin?: boolean;
  is_active?: boolean;
  role_ids?: number[];
  default_device_email?: string | null;
  default_device_name?: string | null;
  default_device_type?: string;
  default_device_format?: string | null;
}

const API_BASE = "/api/admin/users";

/**
 * Create a new user.
 *
 * Parameters
 * ----------
 * data : UserCreate
 *     User creation data.
 *
 * Returns
 * -------
 * Promise<User>
 *     Created user data.
 */
export async function createUser(data: UserCreate): Promise<User> {
  const response = await fetch(API_BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to create user" }));
    throw new Error(error.detail || "Failed to create user");
  }

  return response.json();
}

/**
 * Update a user.
 *
 * Parameters
 * ----------
 * userId : number
 *     User ID to update.
 * data : UserUpdate
 *     User update data.
 *
 * Returns
 * -------
 * Promise<User>
 *     Updated user data.
 */
export async function updateUser(
  userId: number,
  data: UserUpdate,
): Promise<User> {
  const response = await fetch(`${API_BASE}/${userId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update user" }));
    throw new Error(error.detail || "Failed to update user");
  }

  return response.json();
}

/**
 * Delete a user.
 *
 * Parameters
 * ----------
 * userId : number
 *     User ID to delete.
 *
 * Returns
 * -------
 * Promise<void>
 */
export async function deleteUser(userId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${userId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to delete user" }));
    throw new Error(error.detail || "Failed to delete user");
  }
}
