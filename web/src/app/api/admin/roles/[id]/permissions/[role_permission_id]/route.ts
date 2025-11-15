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

import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * PUT /api/admin/roles/[id]/permissions/[role_permission_id]
 *
 * Proxies request to update a role-permission association condition.
 */
export async function PUT(
  request: NextRequest,
  {
    params,
  }: {
    params: Promise<{ id: string; role_permission_id: string }>;
  },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { id, role_permission_id } = await params;
    const body = await request.json();

    const response = await client.request(
      `/admin/roles/${id}/permissions/${role_permission_id}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "Failed to update role permission",
      }));
      return NextResponse.json(
        { detail: errorData.detail || "Failed to update role permission" },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(
      "Error in PUT /api/admin/roles/[id]/permissions/[role_permission_id]:",
      error,
    );
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
