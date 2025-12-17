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
import { getOptionalClient } from "@/services/http/routeHelpers";

/**
 * GET /api/books/[id]/formats/[format]/metadata
 *
 * Proxies request to get detailed metadata for a specific format.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; format: string }> },
) {
  try {
    const { client, error } = getOptionalClient(request);
    if (error) {
      return error;
    }

    const { id, format } = await params;

    const response = await client.request(
      `/books/${id}/formats/${format}/metadata`,
      {
        method: "GET",
      },
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to get format metadata" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 },
    );
  }
}
