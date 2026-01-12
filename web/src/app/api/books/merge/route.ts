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

export async function POST(request: NextRequest) {
  const { client, error } = getAuthenticatedClient(request);
  if (error) {
    return error;
  }

  try {
    const body = await request.json();
    const response = await client.request("/books/merge", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      return NextResponse.json(
        { detail: data.detail || "Failed to merge books" },
        { status: response.status },
      );
    }

    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    const data = await response.json().catch(() => null);
    return NextResponse.json(data || { success: true });
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
