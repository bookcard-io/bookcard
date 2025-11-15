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
 * Service for interacting with admin role API endpoints.
 *
 * Provides methods for fetching roles.
 */

import { deduplicateFetch } from "@/utils/fetch";

export interface Role {
  id: number;
  name: string;
  description: string | null;
}

const API_BASE = "/api/admin/roles";

/**
 * Fetch all roles.
 *
 * Uses fetch deduplication to prevent multiple simultaneous requests.
 *
 * Returns
 * -------
 * Promise<Role[]>
 *     List of all roles.
 */
export async function fetchRoles(): Promise<Role[]> {
  return deduplicateFetch(API_BASE, async () => {
    const response = await fetch(API_BASE, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Failed to fetch roles" }));
      throw new Error(error.detail || "Failed to fetch roles");
    }

    return response.json();
  });
}
