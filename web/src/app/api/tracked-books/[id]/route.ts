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

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    const { client, error } = getAuthenticatedClient(request);
    if (error) return error;

    const response = await client.request(`/tracked-books/${id}`, {
      method: "GET",
    });

    // Handle 204 No Content or empty responses if necessary, though GET usually returns body
    const text = await response.text();
    const data = text ? JSON.parse(text) : null;

    if (!response.ok) {
      return NextResponse.json(data || { detail: response.statusText }, {
        status: response.status,
      });
    }
    return NextResponse.json(data);
  } catch (_error) {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    const { client, error } = getAuthenticatedClient(request);
    if (error) return error;

    const body = await request.json();
    const response = await client.request(`/tracked-books/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }
    return NextResponse.json(data);
  } catch (_error) {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    const { client, error } = getAuthenticatedClient(request);
    if (error) return error;

    const response = await client.request(`/tracked-books/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      // Try to parse error details if available
      try {
        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
      } catch {
        return NextResponse.json(
          { detail: response.statusText },
          { status: response.status },
        );
      }
    }

    // 204 No Content
    return new NextResponse(null, { status: 204 });
  } catch (_error) {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
