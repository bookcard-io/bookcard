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

/**
 * POST /api/auth/logout
 *
 * Proxies logout request to the backend and clears authentication cookie.
 */
export async function POST(request: NextRequest) {
  try {
    // Get Authorization header from request to forward to backend
    const authHeader = request.headers.get("Authorization");
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (authHeader) {
      headers.Authorization = authHeader;
    }

    // Call backend logout endpoint
    await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      headers,
      credentials: "include",
    });

    // Clear authentication cookie
    const nextResponse = NextResponse.json({}, { status: 204 });
    nextResponse.cookies.delete(AUTH_COOKIE_NAME);

    return nextResponse;
  } catch {
    // Even if backend call fails, clear the cookie
    const nextResponse = NextResponse.json(
      { detail: "Logout completed" },
      { status: 200 },
    );
    nextResponse.cookies.delete(AUTH_COOKIE_NAME);
    return nextResponse;
  }
}
