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

/**
 * Builds a login redirect URL with the current path as the "next" parameter.
 *
 * Follows DRY by centralizing redirect URL construction.
 *
 * Parameters
 * ----------
 * req : NextRequest
 *     The request to build redirect for.
 *
 * Returns
 * -------
 * URL
 *     URL object for login redirect.
 */
export function buildLoginRedirect(req: NextRequest): URL {
  const url = req.nextUrl.clone();
  url.pathname = "/login";
  url.searchParams.set("next", `${req.nextUrl.pathname}${req.nextUrl.search}`);
  return url;
}

/**
 * Creates a redirect response to the login page.
 *
 * Parameters
 * ----------
 * req : NextRequest
 *     The request to redirect.
 *
 * Returns
 * -------
 * NextResponse
 *     Redirect response to login page.
 */
export function redirectToLogin(req: NextRequest): NextResponse {
  return NextResponse.redirect(buildLoginRedirect(req));
}
