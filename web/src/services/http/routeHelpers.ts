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
import { AUTH_COOKIE_NAME } from "@/constants/config";
import { createHttpClientFromRequest } from "./HttpClient";

/**
 * Helper functions for Next.js API route handlers.
 *
 * These utilities simplify common patterns when creating API routes
 * that proxy to the backend.
 */

/**
 * Get an authenticated HTTP client from a request, or return an error response.
 *
 * This is a convenience function that:
 * 1. Extracts the auth token from cookies
 * 2. Returns 401 if no token is found
 * 3. Creates and returns an HTTP client if token exists
 *
 * Parameters
 * ----------
 * req : NextRequest
 *     The Next.js request object.
 *
 * Returns
 * -------
 * { client: HttpClient; error: null } | { client: null; error: NextResponse }
 *     Either a client instance or an error response.
 */
export function getAuthenticatedClient(req: NextRequest) {
  const token = req.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return {
      client: null,
      error: NextResponse.json({ error: "unauthorized" }, { status: 401 }),
    };
  }

  const client = createHttpClientFromRequest(req, AUTH_COOKIE_NAME);
  return { client, error: null };
}
