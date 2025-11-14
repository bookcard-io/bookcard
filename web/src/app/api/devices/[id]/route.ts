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
 * PUT /api/devices/[id]
 *
 * Proxies request to update a device for the current user.
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { id } = await params;
    const deviceId = parseInt(id, 10);

    if (Number.isNaN(deviceId)) {
      return NextResponse.json(
        { detail: "Invalid device ID" },
        { status: 400 },
      );
    }

    const body = await request.json();

    const response = await client.request(`/devices/${deviceId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to update device" },
        { status: response.status },
      );
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Error in PUT /api/devices/[id]:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * DELETE /api/devices/[id]
 *
 * Proxies request to delete a device for the current user.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { id } = await params;
    const deviceId = parseInt(id, 10);

    if (Number.isNaN(deviceId)) {
      return NextResponse.json(
        { detail: "Invalid device ID" },
        { status: 400 },
      );
    }

    const response = await client.request(`/devices/${deviceId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const data = await response.json();
      return NextResponse.json(
        { detail: data.detail || "Failed to delete device" },
        { status: response.status },
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Error in DELETE /api/devices/[id]:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
