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
 * GET /api/reading/status/[book_id]
 *
 * Proxies request to get read status for a book.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ book_id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { book_id } = await params;

    const response = await client.request(`/reading/status/${book_id}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch read status" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in GET /api/reading/status/[book_id]:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * PUT /api/reading/status/[book_id]
 *
 * Proxies request to update read status for a book.
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ book_id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { book_id } = await params;
    const body = await request.json();

    const response = await client.request(`/reading/status/${book_id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to update read status" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in PUT /api/reading/status/[book_id]:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
