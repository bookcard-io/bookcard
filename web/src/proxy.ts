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

import type { NextRequest, NextResponse } from "next/server";
import { getAuthToken } from "./middleware/auth";
import { getAllowAnonymousBrowsing } from "./middleware/configProvider";
import { handleRequest } from "./middleware/requestHandler";
import { classifyRoute } from "./middleware/routeClassifier";

/**
 * Main middleware function for request proxying and authentication.
 *
 * Orchestrates route classification, authentication checking, and request handling.
 * Follows SRP by delegating to focused helper functions.
 * Follows SoC by separating concerns into distinct functions.
 *
 * Parameters
 * ----------
 * req : NextRequest
 *     The incoming request.
 *
 * Returns
 * -------
 * Promise<NextResponse>
 *     The response for the request.
 */
export async function proxy(req: NextRequest): Promise<NextResponse> {
  const classification = classifyRoute(req.nextUrl.pathname);
  const token = getAuthToken(req);
  const hasToken = Boolean(token);

  // For unauthenticated users on non-exempt routes, check anonymous browsing config
  let allowAnonymousBrowsing = false;
  if (
    !hasToken &&
    !classification.isPublicAsset &&
    !classification.isApiRoute &&
    !classification.isAuthRoute &&
    !classification.isHomePage
  ) {
    allowAnonymousBrowsing = await getAllowAnonymousBrowsing(req);
  }

  return handleRequest(classification, hasToken, req, allowAnonymousBrowsing);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
