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

import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { redirectToLogin } from "./redirect";
import type { RouteClassification } from "./types";

/**
 * Handles request routing based on classification and authentication state.
 *
 * Follows SoC by separating routing logic from classification.
 *
 * Parameters
 * ----------
 * classification : RouteClassification
 *     The route classification result.
 * hasToken : boolean
 *     Whether the request has an authentication token.
 * req : NextRequest
 *     The request to handle.
 * allowAnonymousBrowsing : boolean
 *     Whether anonymous browsing is enabled.
 *
 * Returns
 * -------
 * NextResponse
 *     The response for the request.
 */
export async function handleRequest(
  classification: RouteClassification,
  hasToken: boolean,
  req: NextRequest,
  allowAnonymousBrowsing: boolean,
): Promise<NextResponse> {
  // Public assets are always allowed
  if (classification.isPublicAsset) {
    return NextResponse.next();
  }

  // API routes are never gated at the edge; let route handlers enforce
  if (classification.isApiRoute) {
    return NextResponse.next();
  }

  // Auth routes are always allowed
  if (classification.isAuthRoute) {
    return NextResponse.next();
  }

  // Authenticated users can access all pages
  if (hasToken) {
    return NextResponse.next();
  }

  // Unauthenticated users: handle special cases
  // Home page always allowed (shows either library or login prompt)
  if (classification.isHomePage) {
    return NextResponse.next();
  }

  // Protected routes always require authentication
  if (classification.isProtectedRoute) {
    return redirectToLogin(req);
  }

  // Check if anonymous browsing is allowed for this route
  if (allowAnonymousBrowsing && classification.isAnonymousAllowedPage) {
    return NextResponse.next();
  }

  // Default: redirect to login
  return redirectToLogin(req);
}
