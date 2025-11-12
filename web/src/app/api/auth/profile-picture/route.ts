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
 * GET /api/auth/profile-picture
 *
 * Proxies request to get the current user's profile picture.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const response = await client.request("/auth/profile-picture", {
      method: "GET",
    });

    if (!response.ok) {
      return NextResponse.json(
        { detail: "Profile picture not found" },
        { status: response.status },
      );
    }

    // Return the image file
    const imageBuffer = await response.arrayBuffer();
    return new NextResponse(imageBuffer, {
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "image/jpeg",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * POST /api/auth/profile-picture
 *
 * Proxies request to upload a profile picture file to the backend.
 */
export async function POST(request: NextRequest) {
  try {
    // Read formData first before any other request access
    // to avoid "body already consumed" errors in Next.js
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ detail: "No file provided" }, { status: 400 });
    }

    // Get authenticated client after reading formData
    // (getAuthenticatedClient only reads cookies, not body)
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    // Create FormData for backend request
    const backendFormData = new FormData();
    backendFormData.append("file", file);

    // Don't set Content-Type header for FormData - fetch will set it with boundary
    const response = await client.request("/auth/profile-picture", {
      method: "POST",
      headers: {}, // Empty headers - fetch will set Content-Type for FormData
      body: backendFormData,
    });

    // Read response body once
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to upload profile picture" },
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

/**
 * DELETE /api/auth/profile-picture
 *
 * Proxies request to delete the current user's profile picture.
 */
export async function DELETE(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const response = await client.request("/auth/profile-picture", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to delete profile picture" },
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
