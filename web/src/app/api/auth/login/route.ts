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
import {
  AUTH_COOKIE_NAME,
  BACKEND_URL,
  COOKIE_SECURE,
} from "@/constants/config";

/**
 * POST /api/auth/login
 *
 * Proxies login request to the backend and sets authentication cookie.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Login failed" },
        { status: response.status },
      );
    }

    const nextResponse = NextResponse.json(data);

    // Set authentication cookie
    if (data.access_token) {
      nextResponse.cookies.set(AUTH_COOKIE_NAME, data.access_token, {
        httpOnly: true,
        secure: COOKIE_SECURE,
        sameSite: "lax",
        path: "/",
      });
    }

    return nextResponse;
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
