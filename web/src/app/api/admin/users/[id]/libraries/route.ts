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
 * GET /api/admin/users/[id]/libraries
 *
 * Proxies request to list library assignments for a user.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) return error;

    const { id } = await params;
    const response = await client.request(`/admin/users/${id}/libraries`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch user libraries" },
        { status: response.status },
      );
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("Error in GET /api/admin/users/[id]/libraries:", err);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * POST /api/admin/users/[id]/libraries
 *
 * Proxies request to assign a library to a user.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) return error;

    const { id } = await params;
    const body = await request.json();
    const response = await client.request(`/admin/users/${id}/libraries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to assign library" },
        { status: response.status },
      );
    }
    return NextResponse.json(data, { status: 201 });
  } catch (err) {
    console.error("Error in POST /api/admin/users/[id]/libraries:", err);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
