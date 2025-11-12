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
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * PUT /api/auth/password
 *
 * Proxies password change request to the backend, then logs out the user
 * to invalidate the current token.
 */
export async function PUT(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const body = await request.json();

    // Call backend password change endpoint
    const response = await client.request("/auth/password", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const data = await response.json();
      return NextResponse.json(
        { detail: data.detail || "Failed to change password" },
        { status: response.status },
      );
    }

    // Password change successful - now logout to invalidate token
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
    const logoutHeaders: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (token) {
      logoutHeaders.Authorization = `Bearer ${token}`;
    }

    // Call backend logout endpoint to blacklist the token
    await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      headers: logoutHeaders,
      credentials: "include",
    });

    // Clear authentication cookie
    const nextResponse = NextResponse.json(
      { detail: "Password changed successfully" },
      { status: 200 },
    );
    nextResponse.cookies.delete(AUTH_COOKIE_NAME);

    return nextResponse;
  } catch (error) {
    console.error("Error in PUT /api/auth/password:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
