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
import type { AnonymousBrowsingResponse } from "./types";

/**
 * Type guard for anonymous browsing response.
 *
 * Parameters
 * ----------
 * data : unknown
 *     Data to validate.
 *
 * Returns
 * -------
 * boolean
 *     True if data matches AnonymousBrowsingResponse schema.
 */
function isValidAnonymousBrowsingResponse(
  data: unknown,
): data is AnonymousBrowsingResponse {
  return (
    typeof data === "object" &&
    data !== null &&
    "allow_anonymous_browsing" in data &&
    typeof (data as AnonymousBrowsingResponse).allow_anonymous_browsing ===
      "boolean"
  );
}

/**
 * Fetches anonymous browsing configuration from the API.
 *
 * Follows IoC principles by being a pure function that can be
 * easily tested or replaced. Includes proper error handling
 * and type safety.
 *
 * Parameters
 * ----------
 * req : NextRequest
 *     The request to use for building the API URL.
 *
 * Returns
 * -------
 * Promise<boolean>
 *     True if anonymous browsing is allowed, false otherwise.
 *     Returns false on any error (fail-closed for security).
 */
export async function getAllowAnonymousBrowsing(
  req: NextRequest,
): Promise<boolean> {
  try {
    const resp = await fetch(
      `${req.nextUrl.origin}/api/config/anonymous-browsing`,
      {
        method: "GET",
        headers: {
          // Ensure this request is never cached between users.
          "Cache-Control": "no-store",
        },
      },
    );

    if (!resp.ok) {
      console.error(
        `[Middleware] Failed to fetch anonymous browsing config: ${resp.status} ${resp.statusText}`,
      );
      return false;
    }

    const data: unknown = await resp.json();

    if (!isValidAnonymousBrowsingResponse(data)) {
      console.error(
        "[Middleware] Invalid anonymous browsing config response format",
      );
      return false;
    }

    return Boolean(data.allow_anonymous_browsing);
  } catch (error) {
    console.error(
      "[Middleware] Error fetching anonymous browsing config:",
      error,
    );
    return false; // Fail closed - secure default
  }
}
