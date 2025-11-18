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
 * GET /api/tasks
 *
 * Proxy request to backend tasks endpoint.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const path = queryString ? `/tasks?${queryString}` : "/tasks";

    const response = await client.request(path, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const responseText = await response.text();

    if (!response.ok) {
      let errorData: { detail?: string };
      try {
        errorData = JSON.parse(responseText) as { detail?: string };
      } catch {
        errorData = { detail: "Failed to fetch tasks" };
      }
      return NextResponse.json(errorData, { status: response.status });
    }

    let data: unknown;
    try {
      data = JSON.parse(responseText);
    } catch {
      return NextResponse.json(
        { detail: "Invalid response from server" },
        { status: 500 },
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
