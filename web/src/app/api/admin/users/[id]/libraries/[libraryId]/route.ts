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
 * DELETE /api/admin/users/[id]/libraries/[libraryId]
 *
 * Proxies request to unassign a library from a user.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; libraryId: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) return error;

    const { id, libraryId } = await params;
    const response = await client.request(
      `/admin/users/${id}/libraries/${libraryId}`,
      { method: "DELETE", headers: { "Content-Type": "application/json" } },
    );

    if (!response.ok) {
      const data = await response.json();
      return NextResponse.json(
        { detail: data.detail || "Failed to unassign library" },
        { status: response.status },
      );
    }
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    console.error(
      "Error in DELETE /api/admin/users/[id]/libraries/[libraryId]:",
      err,
    );
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
